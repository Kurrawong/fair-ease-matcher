from pathlib import Path

import openpyxl
from rdflib import URIRef, Namespace

OLIS = Namespace("https://olis.dev/")

filename = "SA Knowledge Base Library construction.xlsx"
sheetname = "categorisation of Vocabs"

file = Path(__file__).parent.parent.parent / "data/categories/" / filename
workbook = openpyxl.load_workbook(file)

sheet = workbook[sheetname]

# Dictionary to store the IRI as keys and SeaDataNet keyword types and URIs as values
iri_dict = {}

# Iterate through the rows in the specified columns
for row in sheet.iter_rows(min_row=2, max_row=sheet.max_row, min_col=2, max_col=3, values_only=True):
    iri_value, sea_data_net_value = row

    # Check if both columns have values
    if iri_value and sea_data_net_value:
        # If the IRI value already exists in the dictionary, append the new value
        if iri_value in iri_dict:
            iri_dict[iri_value].append(sea_data_net_value)
        else:
            # If not, create a new list with the SeaDataNet keyword type and URIs as the initial value
            iri_dict[iri_value] = [sea_data_net_value]

string_iri_map = {"parameter": URIRef("http://vocab.nerc.ac.uk/collection/L19/current/SDNKG03/"),
                  "instrument": URIRef("")}
# Printing the dictionary to see the output
print(iri_dict)
