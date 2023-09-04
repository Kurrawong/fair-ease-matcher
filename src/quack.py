import re


def quack_analyser(value: str) -> str:
    # URI check
    if re.match(r'^[a-zA-Z][a-zA-Z0-9+-.]*://.*$', value):
        return 'URI'

    # Identifier check (alphanumeric characters or "::")
    if re.match(r'^[A-Za-z0-9:]+$', value) and not re.search(r'\s', value):
        return 'identifier'

    # If none of the above, consider it as a string
    return 'string'