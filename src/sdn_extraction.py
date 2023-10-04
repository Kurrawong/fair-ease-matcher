from collections import defaultdict
from functools import reduce

from src.functions import clean_list_of_keywords

ns = {
    'gmi': 'http://www.isotc211.org/2005/gmi',
    'gmd': 'http://www.isotc211.org/2005/gmd',
    'gco': 'http://www.isotc211.org/2005/gco'
}


def merge_dicts(dicts):
    def merge_two_dicts(dict1, dict2):
        merged = {}
        for key in dict1.keys() | dict2.keys():
            merged[key] = {
                'uris': list(set(dict1.get(key, {}).get('uris', []) + dict2.get(key, {}).get('uris', []))),
                'identifiers': list(set(dict1.get(key, {}).get('identifiers', []) + dict2.get(key, {}).get('identifiers', []))),
                'strings': list(set(dict1.get(key, {}).get('strings', []) + dict2.get(key, {}).get('strings', []))),
            }
        return merged
    return reduce(merge_two_dicts, dicts, {})


def extract_from_all(root):
    all_dicts = []
    all_dicts.append({"Keywords": {}, "Instrument": {}, "Variable": {}, "Platform": {}})  # default empty dicts
    all_dicts.append(extract_from_descriptiveKeywords(root))
    all_dicts.append(extract_from_topic_categories(root))
    all_dicts.append(extract_from_content_info(root))
    all_dicts.append(extract_instruments_platforms_from_acquisition_info(root))
    merged = merge_dicts(all_dicts)
    return merged


def extract_from_descriptiveKeywords(root):
    # Define namespaces for parsing

    # Mapping of keyword type to metadata element
    metadata_element_map = {
        'theme': 'Keywords',
        'instrument': 'Instrument',
        'Variable': 'Variable',
        'platform_class': 'Platform',
        'platform': 'Platform',
        'sensor_model': 'Instrument',
    }

    # Find all <gmd:descriptiveKeywords> blocks
    blocks = root.findall(".//gmd:descriptiveKeywords", ns)

    consolidated_results = defaultdict(lambda: {"uris": [], "identifiers": [], "strings": []})

    # Process each block
    for block in blocks:
        # Extract keyword string
        suspected_types = {"uris": [], "identifiers": [], "strings": []}
        keyword_str_list = block.findall(".//gmd:keyword/gco:CharacterString", ns)
        keyword_list = [text.text for text in keyword_str_list if text.text is not None]
        suspected_types["strings"] = keyword_list

        uri = block.find(".//gmd:identifier/gmd:MD_Identifier/gmd:code/gco:CharacterString", ns)
        if uri is not None and uri.text:
            uri_value = uri.text
            identifier = identifier_from_uri_end(uri_value)
            suspected_types["identifiers"] = [identifier]
            suspected_types["uris"] = [uri_value]

        cleaned_kw_elements = clean_list_of_keywords(suspected_types)

        # Determine type code
        keyword_typecode = block.find(".//gmd:type/gmd:MD_KeywordTypeCode", ns)
        if keyword_typecode is not None:
            keyword_type = keyword_typecode.get('codeListValue')
        else:
            keyword_type = "Keywords"
        # Consolidate the results by metadata type
        if keyword_type in metadata_element_map:
            meta_type = metadata_element_map[keyword_type]
            for key in cleaned_kw_elements:
                consolidated_results[meta_type][key].extend(cleaned_kw_elements[key])

    # Convert defaultdict back to a regular dictionary
    return dict(consolidated_results)


def extract_from_topic_categories(root):
    # look for keywords under topic category
    consolidated_results = defaultdict(lambda: {"uris": [], "identifiers": [], "strings": []})
    topic_category_elements = root.findall(".//gmd:topicCategory/gmd:MD_TopicCategoryCode", ns)
    topic_categories = [topic_category.text for topic_category in topic_category_elements if topic_category.text]
    cleaned_kw_elements = clean_list_of_keywords(
        {"strings": topic_categories,
         "uris": [],
         "identifiers": []})
    for key in cleaned_kw_elements:
        consolidated_results["Keywords"][key].extend(cleaned_kw_elements[key])
    return dict(consolidated_results)


def extract_from_content_info(root):
    # Check if codeListValue is "physicalMeasurement"
    content_type_elem = root.find(".//gmd:contentType/gmd:MD_CoverageContentTypeCode", ns)
    if content_type_elem is not None and content_type_elem.attrib.get("codeListValue") == "physicalMeasurement":

        # find all occurrences of the RecordType element
        record_type_elems = root.findall(".//gmd:attributeDescription/gco:RecordType", ns)
        record_type_strings = [elem.text for elem in record_type_elems if elem.text]
        record_type_uris = [elem.attrib.get("{http://www.w3.org/1999/xlink}href") for elem in record_type_elems if
                            elem.attrib.get("{http://www.w3.org/1999/xlink}href")]
        record_type_identifiers = [identifier_from_uri_end(uri) for uri in record_type_uris if uri]
        results = clean_list_of_keywords(
            {"strings": record_type_strings,
             "uris": record_type_uris,
             "identifiers": record_type_identifiers})
        return {"Variable": results}
    return {}


def extract_instruments_platforms_from_acquisition_info(root):
    consolidated_results = defaultdict(lambda: {"uris": [], "identifiers": [], "strings": []})
    keys = {"Instrument": "gmi:instrument", "Platform": "gmi:platform"}
    for elem_type, xml_path in keys.items():
        blocks = root.findall(f".//gmi:acquisitionInformation/gmi:MI_AcquisitionInformation/{xml_path}", ns)
        for block in blocks:
            string_elems = block.findall(".//gmi:MI_Instrument/gmi:citation/gmd:CI_Citation/gmd:title/gco:CharacterString", ns)
            strings = [elem.text for elem in string_elems if elem.text]
            uri_elems = block.findall(".//gmd:MD_Identifier/gmd:code/gco:CharacterString", ns)
            uris = [identifier.text for identifier in uri_elems if identifier.text]
            identifiers = [identifier_from_uri_end(uri) for uri in uris]
            suspected_types = {"strings": strings, "uris": uris, "identifiers": identifiers}
            cleaned_kw_elements = clean_list_of_keywords(suspected_types)
            for key in cleaned_kw_elements:
                consolidated_results[elem_type][key].extend(cleaned_kw_elements[key])
    return dict(consolidated_results)



def identifier_from_uri_end(uri):
    if uri.endswith("/"):
        return uri.split("/")[-2]
    return uri.split("/")[-1]