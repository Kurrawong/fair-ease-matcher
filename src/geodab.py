import json
import xml.etree.ElementTree as ET
from pathlib import Path

# Define the XML namespace map
namespaces = {
    'gmd': 'http://www.isotc211.org/2005/gmd',
    'gco': 'http://www.isotc211.org/2005/gco',
    'gmi': 'http://www.isotc211.org/2005/gmi',
    'xlink': 'http://www.w3.org/1999/xlink'  # adding the xlink namespace
}


def get_root(file_path: Path):
    data = file_path.read_text()
    root = ET.fromstring(data)
    return root


def get_keywords(root: ET.Element):
    keywords = root.findall(".//gmd:MD_Keywords/gmd:keyword/gco:CharacterString", namespaces)
    keywords = [keyword.text for keyword in keywords]
    return keywords


def clean_keywords(keywords: list):
    return [kw.strip().replace('"', '').replace(',', '').replace('-', ' ').replace('_', ' ').lower() for kw in
            keywords]


def get_instrument_info(root: ET.Element):
    instrument_title = root.find(".//gmi:MI_Instrument/gmi:citation/gmd:CI_Citation/gmd:title/gco:CharacterString",
                                 namespaces)
    instrument_identifier = root.find(
        ".//gmi:MI_Instrument/gmi:identifier/gmd:MD_Identifier/gmd:code/gco:CharacterString", namespaces)
    instrument_description = root.find(".//gmi:MI_Instrument/gmi:description/gco:CharacterString", namespaces)

    # Extract text from the XML elements, if they exist.
    return {
        'title': instrument_title.text if instrument_title is not None else None,
        'identifier': instrument_identifier.text if instrument_identifier is not None else None,
        'description': instrument_description.text if instrument_description is not None else None
    }


def get_variable_info(root: ET.Element):
    # Extract content info for each variable
    attribute_description_elements = root.findall(
        ".//gmd:MD_CoverageDescription/gmd:attributeDescription/gco:RecordType", namespaces)
    content_type_elements = root.findall(".//gmd:MD_CoverageDescription/gmd:contentType/gmd:MD_CoverageContentTypeCode",
                                         namespaces)

    # Pairing variable descriptions with content types based on order
    variables = []
    for desc_element, type_element in zip(attribute_description_elements, content_type_elements):
        variable = {
            "text": desc_element.text,
            "xlink_href": desc_element.get("{http://www.w3.org/1999/xlink}href"),
            "xlink_title": desc_element.get("{http://www.w3.org/1999/xlink}title"),
            "type": type_element.get('codeListValue') if type_element is not None else None
        }
        variables.append(variable)

    return variables


def create_queries(extracted_data):
    for record in extracted_data:
        keywords = extracted_data[record]['keywords']


def main():
    files = Path("../data/geodab-metadata").glob("*.xml")
    extracted_data = {}

    for file in files:
        root = get_root(file)

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
