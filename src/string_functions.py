from src.quack import quack_analyser


def clean_list_of_keywords(suspected_types: dict):

    """returns a cleaned list of URIs and Strings for keywords"""
    strings = suspected_types["strings"]
    cleaned_strings = split_list_of_strings(strings)
    cleaned_strings = clean_list_of_strings(cleaned_strings)
    cleaned_strings = remove_empty_strings(cleaned_strings)
    return deduplicate_and_categorize(
        {"strings": cleaned_strings, "uris": suspected_types["uris"], "identifiers": suspected_types["identifiers"]}
        )

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


def remove_empty_strings(list_of_strings: list):
    return [string for string in list_of_strings if string != '' or string != ""]


def deduplicate_and_categorize(data):
    # Lists to store URNs/URIs and strings
    uris = set()
    identifiers = set()
    strings = set()

    # Get values based on type of data
    if isinstance(data, dict):
        values = data.values()
    elif isinstance(data, list):
        values = data
    else:
        raise ValueError("Input data must be a dictionary or a list")

    # Iterate over values
    for values_list in values:
        for elem in values_list:
            metadata_type = quack_analyser(elem)
            if metadata_type == 'URI':
                other_version = None
                if elem.startswith("http://"):
                    other_version = elem.replace("http://", "https://")
                elif elem.startswith("https://"):
                    other_version = elem.replace("https://", "http://")
                if other_version:
                    uris.add(other_version)
                uris.add(elem)
            elif metadata_type == 'identifier':
                identifiers.add(elem)
            else:
                strings.add(elem)
    # Convert sets back to lists for the final result
    return {"strings": list(strings), "uris": list(uris), "identifiers": list(identifiers)}


def identifier_from_uri_end(uri):
    if uri.endswith("/"):
        return uri.split("/")[-2]
    return uri.split("/")[-1]
