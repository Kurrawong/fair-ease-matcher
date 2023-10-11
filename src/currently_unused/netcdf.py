from pathlib import Path

from netCDF4 import Dataset

from src.sparql_queries import find_vocabs_sparql, get_vocabs_from_sparql_endpoint


def extract_urns_from_netcdf(rootgrp: Dataset, var_name: str):
    var_urns = []
    for var in rootgrp.variables.items():
        urn_or_none = var[1].__dict__.get(var_name)
        if urn_or_none:
            var_urns.append(urn_or_none)
    return var_urns

def extract_text_from_net_cdf(rootgrp: Dataset, var_name: str):
    var_text = []
    for var in rootgrp.variables.items():
        text_or_none = var[1].__dict__.get(var_name)
        if text_or_none:
            var_text.append(text_or_none)
    return var_text


def main():
    file_path = Path("data/ArgoFloats_389b_381a_5a9a.nc")
    # file_path = Path("data/000545_CFPOINT_77AR2009_00052_H09_V0.nc")
    rootgrp = Dataset(file_path, "r", format="NETCDF4")
    # try get URNs
    var_urns = extract_urns_from_netcdf(rootgrp, "sdn_parameter_urn")
    uom_urns = extract_urns_from_netcdf(rootgrp, "sdn_uom_urn")
    # try get text
    var_text = extract_text_from_net_cdf(rootgrp, "sdn_parameter_name")
    uom_text = extract_text_from_net_cdf(rootgrp, "sdn_uom_name")

    var_query = find_vocabs_sparql(var_urns)
    uom_query = find_vocabs_sparql(uom_urns)

    var_collections_uris = get_vocabs_from_sparql_endpoint(var_query)
    uom_collections_uris = get_vocabs_from_sparql_endpoint(uom_query)

    print(collections_uris)


if __name__ == '__main__':
    main()
