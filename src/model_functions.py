from functools import reduce


def merge_dicts(dicts):
    def merge_two_dicts(dict1, dict2):
        merged = {}
        for key in dict1.keys() | dict2.keys():
            merged[key] = {
                'uris': list(set(dict1.get(key, {}).get('uris', []) + dict2.get(key, {}).get('uris', []))),
                'identifiers': list(
                    set(dict1.get(key, {}).get('identifiers', []) + dict2.get(key, {}).get('identifiers', []))),
                'strings': list(set(dict1.get(key, {}).get('strings', []) + dict2.get(key, {}).get('strings', []))),
            }
        return merged

    return reduce(merge_two_dicts, dicts, {})
