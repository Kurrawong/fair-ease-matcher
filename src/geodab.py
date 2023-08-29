import json
import xml.etree.ElementTree as ET
from pathlib import Path
import httpx
from jinja2 import Template


# Define the XML namespace map
namespaces = {
    'gmd': 'http://www.isotc211.org/2005/gmd',
    'gco': 'http://www.isotc211.org/2005/gco',
    'gmi': 'http://www.isotc211.org/2005/gmi',
    'xlink': 'http://www.w3.org/1999/xlink'  # adding the xlink namespace
}
template = Template(Path("../src/query_template.sparql").read_text())


def analyse_from_xml_url(xml_url, threshold):
    # get the root element from the remote XML file
    root = get_root_from_remote(xml_url)

    # get the keywords, instrement info and variable info from the XML file
    kws = get_keywords(root)
    inst_info = get_instrument_info(root)
    var_info = get_variable_info(root)

    # create qureies for the keywords, instrument info and variable info
    kws_exact_query = create_query(predicate=None, exact=True, terms=kws['strings'])
    kws_wildcard_query = create_query(predicate=None, exact=False, terms=kws['strings'])
    inst_exact_query = create_query(predicate='dcterms:identifier', exact=True, terms=inst_info['identifiers'])
    inst_wildcard_query = create_query(predicate='dcterms:identifier', exact=False, terms=inst_info['identifiers'])
    var_exact_query_strings = create_query(predicate=None, exact=True, terms=var_info['strings'])
    var_wildcard_query_strings = create_query(predicate=None, exact=False, terms=var_info['strings'])
    print("i")






def create_query(predicate, exact: bool, terms):

    # Render the template with the necessary parameters
    query = template.render(predicate=predicate, exact=exact, terms=terms)  # template imported at module level.
    return query

def clean_variables(variable_info: list):
    deduplicate_and_categorize(variable_info)
    ...


def deduplicate_and_categorize(data):
    # Lists to store URNs/URIs and strings
    urns_uris = set()
    strings = set()

    # Get values based on type of data
    if isinstance(data, dict):
        values = data.values()
    elif isinstance(data, list):
        values = data
    else:
        raise ValueError("Input data must be a dictionary or a list")

    # Iterate over values
    for value in values:
        if isinstance(value, str):  # Ensure the value is a string
            if value.startswith(('http', 'https')):  # Check for http/https
                urns_uris.add(value)
            else:
                strings.add(value)

    # Convert sets back to lists for the final result
    return list(urns_uris), list(strings)


def get_root_from_file(file_path: Path):
    data = file_path.read_text()
    root = ET.fromstring(data)
    return root


def get_root_from_remote(xml_url):
    try:
        response = httpx.get(xml_url)
    except httpx.HTTPError as e:
        print(f"HTTP error: {e}")
        return None
    root = ET.fromstring(response.text)
    return root


def get_keywords(root: ET.Element):
    keywords = root.findall(".//gmd:MD_Keywords/gmd:keyword/gco:CharacterString", namespaces)
    keywords = [keyword.text for keyword in keywords]
    keywords = split_list_of_strings(keywords)
    keywords = clean_list_of_strings(keywords)
    uris, strings = deduplicate_and_categorize(keywords)
    return {"uris": uris, "strings": strings}


def split_list_of_strings(list_of_strings: list):
    intermediate_list = []
    newlist = []
    for string in list_of_strings:
        intermediate_list.append(string.split(' > ')[-1])
    for string in intermediate_list:
        newlist += string.split('/')
    return newlist


def clean_list_of_strings(list_of_strings: list):
    return [string.strip().replace('"', '').replace(',', '').replace('-', ' ').replace('_', ' ').lower() for string in
            list_of_strings]


def get_instrument_info(root: ET.Element):
    instrument_title = root.find(".//gmi:MI_Instrument/gmi:citation/gmd:CI_Citation/gmd:title/gco:CharacterString",
                                 namespaces)
    instrument_identifier = root.find(
        ".//gmi:MI_Instrument/gmi:identifier/gmd:MD_Identifier/gmd:code/gco:CharacterString", namespaces)
    instrument_description = root.find(".//gmi:MI_Instrument/gmi:description/gco:CharacterString", namespaces)

    string_fields = []
    if instrument_title is not None:
        instrument_title = instrument_title.text
        string_fields.append(instrument_title)
    if instrument_description is not None:
        instrument_description = instrument_description.text
        string_fields.append(instrument_description)
    cleaned_strings = clean_list_of_strings(string_fields)
    _, deduped_strings = deduplicate_and_categorize(cleaned_strings)

    # Extract text from the XML elements, if they exist.
    return {
        'strings': deduped_strings,
        'identifiers': instrument_identifier.text if instrument_identifier is not None else None,
        'uris': None  # TODO
    }


def get_variable_info(root: ET.Element):
    # Extract content info for each variable
    attribute_description_elements = root.findall(
        ".//gmd:MD_CoverageDescription/gmd:attributeDescription/gco:RecordType", namespaces)
    content_type_elements = root.findall(".//gmd:MD_CoverageDescription/gmd:contentType/gmd:MD_CoverageContentTypeCode",
                                         namespaces)

    # Pairing variable descriptions with content types based on order
    deduped_variables = []
    for desc_element, type_element in zip(attribute_description_elements, content_type_elements):
        variable = {
            "text": desc_element.text,
            "xlink_href": desc_element.get("{http://www.w3.org/1999/xlink}href"),
            "xlink_title": desc_element.get("{http://www.w3.org/1999/xlink}title"),
            "type": type_element.get('codeListValue') if type_element is not None else None
        }
        deduped = deduplicate_and_categorize(variable)
        split = split_list_of_strings(deduped[1])
        cleaned = clean_list_of_strings(split)
    return {"uris": None, "strings": cleaned}


def create_queries(extracted_data):
    for record in extracted_data:
        keywords = extracted_data[record]['keywords']


def main():
    files = Path("../data/geodab-metadata").glob("*.xml")
    extracted_data = {}

    for file in files:
        root = get_root_from_file(file)

        kws = get_keywords(root)
        cleaned_kws = clean_keywords(kws)

        inst_info = get_instrument_info(root)
        if not any(inst_info.values()):  # Check if all values in the dict are None
            inst_info = None

        var_info = get_variable_info(root)

        data = {
            "keywords": kws,
            "cleaned_keywords": cleaned_kws,
            "instrument_info": inst_info,
            "variable_info": var_info
        }

        # Remove None values at the top level
        data = {k: v for k, v in data.items() if v is not None}

        extracted_data[str(file.name)] = data

    with open('extracted_data.json', 'w') as outfile:
        json.dump(extracted_data, outfile)

    queries = create_queries(extracted_data)


# Assuming you want to run the main function immediately
if __name__ == "__main__":
    main()
