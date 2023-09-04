import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import httpx
from jinja2 import Template

from src.sparql_queries import get_vocabs_from_sparql_endpoint

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

namespaces = {
    'gmd': 'http://www.isotc211.org/2005/gmd',
    'gco': 'http://www.isotc211.org/2005/gco',
    'gmi': 'http://www.isotc211.org/2005/gmi',
    'xlink': 'http://www.w3.org/1999/xlink'
}
template = Template(Path("src/query_template.sparql").read_text())


def analyse_from_xml(xml, threshold) -> dict:

    root = ET.fromstring(xml)
    logger.info("Obtained root from remote XML.")

    kws = get_keywords(root)
    inst_info = get_instrument_info(root)
    var_info = get_variable_info(root)

    logger.info(f"Keywords extracted: {kws['strings']}")
    logger.info(f"Instrument Info extracted: {inst_info['identifiers']}")
    logger.info(f"Variable Info extracted: {var_info['strings']}")

    query_args = {
        'kws_exact': {'predicate': None, 'exact': True, 'terms': kws['strings']},
        # 'kws_wildcard': {'predicate': None, 'exact': False, 'terms': kws['strings']},
        'inst_exact': {'predicate': 'dcterms:identifier', 'exact': True, 'terms': inst_info['identifiers']},
        # 'inst_wildcard': {'predicate': 'dcterms:identifier', 'exact': False, 'terms': inst_info['identifiers']},
        'var_exact_strings': {'predicate': None, 'exact': True, 'terms': var_info['strings']},
        # 'var_wildcard_strings': {'predicate': None, 'exact': False, 'terms': var_info['strings']},
    }

    results = {}
    for query_type, kwargs in query_args.items():
        query = create_query(**kwargs)
        results[query_type] = get_vocabs_from_sparql_endpoint(query)
        logger.info(f"Results for query type {query_type}: {results[query_type]}")

    return results


def create_query(predicate, exact: bool, terms):

    # escape the terms for Lucene
    escaped_terms = [escape_for_lucene_and_sparql(term) for term in terms]

    # Render the template with the necessary parameters
    query = template.render(predicate=predicate, exact=exact, terms=escaped_terms)  # template imported at module level.
    return query


def escape_for_lucene_and_sparql(query):
    # First, escape the Lucene special characters.
    chars_to_escape = re.compile(r'([\+\-!\(\)\{\}\[\]\^"~\*\?:\\/])')
    lucene_escaped = chars_to_escape.sub(r'\\\1', query)

    # Then, double escape the backslashes for SPARQL.
    sparql_escaped = lucene_escaped.replace('\\', '\\\\')

    return sparql_escaped


def clean_variables(variable_info: list):
    deduplicate_and_categorize(variable_info)


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
        response = httpx.get(xml_url, timeout=10)  # 10 seconds timeout
        logger.info(f"Response from {xml_url}: {response.text}")
        # Check if the request was successful
        if response.status_code != 200:
            logger.error(
                f"Failed to fetch XML from {xml_url}. Status code: {response.status_code}. Response: {response.text}")
            raise Exception(f"HTTP error {response.status_code} when fetching XML.")

        root = ET.fromstring(response.text)
        return root

    except httpx.HTTPError as e:
        logger.error(f"HTTP error occurred when fetching XML from {xml_url}. Error: {str(e)}")
        raise
    except ET.ParseError as e:
        logger.error(f"Failed to parse XML from {xml_url}. Error: {str(e)}")
        raise


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

    uris = []
    identifier = None
    if instrument_identifier.text is not None:
        # Handle SeaDataNet identifiers
        if instrument_identifier.text.startswith("http://www.seadatanet.org/urnurl/"):
            identifier = instrument_identifier.text.split('/')[-2]

    # Extract text from the XML elements, if they exist.
    return {
        'strings': deduped_strings,
        'identifiers': [identifier],
        'uris': [instrument_identifier.text] if instrument_identifier is not None else None
    }


def get_variable_info(root: ET.Element):
    # Extract content info for each variable
    attribute_description_elements = root.findall(
        ".//gmd:MD_CoverageDescription/gmd:attributeDescription/gco:RecordType", namespaces)
    content_type_elements = root.findall(".//gmd:MD_CoverageDescription/gmd:contentType/gmd:MD_CoverageContentTypeCode",
                                         namespaces)

    # Pairing variable descriptions with content types based on order
    cleaned = []
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
