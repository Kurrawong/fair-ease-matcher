import os

from SPARQLWrapper import SPARQLWrapper, JSON


def find_vocabs_sparql(urns):
    return f"""
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX dcterms: <http://purl.org/dc/terms/>

SELECT ?collection {{
  ?concept dcterms:identifier ?urn .
    ?collection skos:member ?concept .
FILTER(?urn IN (
    {", ".join(f'"{urn}"' for urn in urns)} 
  ))
}} 
GROUP BY ?collection
    """

def get_vocabs_from_sparql_endpoint(query):
    sparql = SPARQLWrapper(os.getenv("SPARQL_ENDPOINT"))
    sparql.setReturnFormat(JSON)
    sparql.setQuery(query)
    try:
        ret = sparql.queryAndConvert()
        vocab_or_collection_uris = []
        for r in ret["results"]["bindings"]:
            vocab_or_collection_uris.append(r["collection"]["value"])
        return vocab_or_collection_uris
    except Exception as e:
        print(e)
