import logging
import os

from SPARQLWrapper import SPARQLWrapper, JSON
from httpx import AsyncClient
from rdflib import URIRef

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
sparql_endpoint = os.getenv("SPARQL_ENDPOINT")
user = os.getenv("SPARQL_USERNAME", "")
passwd = os.getenv("SPARQL_PASSWORD", "")


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
    if not sparql_endpoint:
        raise Exception("SPARQL_ENDPOINT not set")
    sparql = SPARQLWrapper(
        endpoint=sparql_endpoint
    )
    sparql.setCredentials(
        user=user,
        passwd=passwd,
    )
    sparql.setReturnFormat(JSON)
    sparql.setQuery(query)
    try:
        response = sparql.queryAndConvert()
        return response  # return as tuple to make it hashable and usable with asyncio.gather
    except Exception:
        raise


async_client = AsyncClient(
    auth=(user, passwd)
    if user
    else None,
    timeout=30,
)


async def send_query(query: str, mediatype="text/turtle"):
    """Sends a SPARQL query asynchronously.
    Args: query: str: A SPARQL query to be sent asynchronously.
    Returns: httpx.Response: A httpx.Response object
    """
    query_rq = async_client.build_request(
        "POST",
        url=sparql_endpoint,
        headers={"Accept": mediatype},
        data={"query": query},
    )
    response = await async_client.send(query_rq, stream=True)
    return response


async def tabular_query_to_dict(query: str, context: URIRef = None):
    """
    Sends a SPARQL query asynchronously and parses the response into a table format.
    The optional context parameter allows an identifier to be supplied with the query, such that multiple results can be
    distinguished from each other.
    """
    response = await send_query(query, "application/sparql-results+json")
    await response.aread()
    return context, response.json()