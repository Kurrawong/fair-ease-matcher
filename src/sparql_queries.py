import logging
import os
from SPARQLWrapper import SPARQLWrapper, JSON

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def find_vocabs_sparql(urns):
    return f"""
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX dcterms: <http://purl.org/dc/terms/>

    SELECT ?collection {{
      {{
        ?concept dcterms:identifier ?urn .
        ?collection skos:member ?concept .
      }}
      UNION
      {{
        ?concept dcterms:identifier ?urn .
        ?concept skos:inScheme ?collection .
      }}
      FILTER(?urn IN (
          {", ".join(f'"{urn}"' for urn in urns)} 
      ))
    }} 
    GROUP BY ?collection
    """


def get_vocabs_from_sparql_endpoint(query):
    sparql_endpoint = os.getenv("SPARQL_ENDPOINT")
    if not sparql_endpoint:
        raise Exception("SPARQL_ENDPOINT not set")
    sparql = SPARQLWrapper(
        endpoint=sparql_endpoint
    )
    sparql.setCredentials(
        user=os.getenv("SPARQL_USERNAME", ""),
        passwd=os.getenv("SPARQL_PASSWORD", ""),
    )
    sparql.setReturnFormat(JSON)
    sparql.setQuery(query)
    try:
        response = sparql.queryAndConvert()
        return response
    except Exception as e:
        raise
        logger.error(e)

