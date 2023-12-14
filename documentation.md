The semantic analyser backend takes as its input a JSON payload in the following structure for analysis of ISO19115 XML metadata records:

```json
{"xml":
  {"document-1":"<xml content ...>",
    "document-2":"<xml content ...>"},"threshold":1}
```
For netCDF files, the structure is similar, with the xml content replaced with the bytes of the netCDF file.
Note the analyser only reads the metadata portion of netCDF files, so where users have large netCDF files, these can be stripped (programatically) of their 'data' content, and sent to the analyser with just the metadata. This metadata still needs to be in the form of a netCDF file - it will effectively be a 'shell' of the original file, containing only metadata.

This input is sent from the frontend web application.

Three analysis methods are currently supported by the analyser, these are:
1. Structured XML analysis - based on the structure of ISO19115 XML.
2. "Full" XML analysis - which strips XML files of all textual fields.
3. netCDF analysis - which considers only the netCDF metadata.

## Structured

A number of metadata elements are then parsed from each document. These are listed in the table below:

- Descriptive Keywords - ".//gmd:descriptiveKeywords". 
- Topic Categories - ".//gmd:topicCategory/gmd:MD_TopicCategoryCode" - #TODO used for what?
- Content info - ".//gmd:contentType/gmd:MD_CoverageContentTypeCode", ".//gmd:attributeDescription/gco:RecordType" - #TODO used for what?
- Acquisition info - ".//gmi:acquisitionInformation/gmi:MI_AcquisitionInformation/{xml_path}"

There are further sub expressions for some of the above elements, which target strings, URIs, or other nested elements within the XML.

The analyser extracts candidate search terms to match against the knowledge base. Depending on where in the XML these terms are found, they are expected to be of a particular metadata category. 
Terms extracted from Descriptive Keywords are mapped to all metadata element categories (not just Keywords). The mapping to different categories is done by extracting the following element:
`".//gmd:type/gmd:MD_KeywordTypeCode"`.

The tag map is as follows:

```python
metadata_element_map = {
    "theme": "Keywords",
    "instrument": "Instrument",
    "Variable": "Variable",
    "platform_class": "Platform",
    "platform": "Platform",
    "sensor_model": "Instrument",
    "parameter": "Variable",
}
```
For each category of variable, the terms are split out into three further subcategories relating to their datatype. The datatypes are either inferred from the place in the XML they were found, or for indeterminate places in the XML initially processed as a string, then categorised into a string, URI, or identifier once cleaned.

Where the determined or guessed type is string, The terms are then cleaned using the following processes:
1. Split strings which appear to be lists (where the separator is ">" and "/")
2. Clean strings by removing the following characters: """, ",", "-", "_"
3. Removing empty strings (where the string is only whitespace)
4. Creating a second search string where there is a "|" in the original string, for the last part of the original string after the "|"

The list of strings is then deduplicated and again categorised into strings, URIs, and identifiers. The function to guess the type of strings is:

```python
def quack_analyser(value: str) -> str:
    # URI check
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+-.]*://.*$", value):
        return "URI"

    # Identifier check (alphanumeric characters or "::")
    if re.match(r"^(?=.*[0-9])([A-Za-z0-9:]+|[0-9]+)$", value) and not re.search(
        r"\s", value
    ):
        return "identifier"

    # If none of the above, consider it as a string
    return "string"
```

A parameterised unit test is available in `/tests` which gives an idea of the kinds of categorisation these regular expressions perform.
If the type is determined to be a URI, then a second search term is added; the same URI with the prefix changed to either http or https to give the "other" variant compared to what was extracted.

## SPARQL query generation

The extracted, cleaned, and categorised set of terms is then substituted into two SPARQL queries; one query where the search terms are URIs, and another query where the search terms are strings or identifiers.
This last query uses Apache Jena's Full Text Search functionality.

The extracted terms are then used to build SPARQL queries in the above types. In the case of identifiers, only the dcterms:identifier predicate is searched on.
For strings there is no restriction - all properties that are indexed are searched; and the predicate is not relevant for URIs; the URI either does or does not exist in the Knowledge Base. 

In the string based SPARQL queries, a quoted and unquoted variant of each search term is included in the query. This ensures exact matches are found, and can be ranked higher than other matches.

If a user has specified to restrict the search to certain themes, the graph to theme mapping is used to only retrieve results with those themes.

The two SPARQL template queries are shown below. They are written in a templating language called jinja2.

```jinja2
SELECT ?SearchTerm ?MatchURI ?MatchProperty ?MatchTerm ?Container ?ContainerLabel ?MethodSubType (GROUP_CONCAT(DISTINCT(?VocabCategory);separator=", ") AS ?Categories)
{
    {
      SELECT REDUCED ?MatchURI {
        VALUES ?MatchURI { {%- for term in terms -%}
        <{{term}}>
        {%- endfor %} }
        ?MatchURI ?p ?o
      }
    }
    GRAPH ?g {?MatchURI ?p ?o}
    {%- if theme_uris %}
      VALUES ?theme_uri {
    {%- for theme_uri in theme_uris -%}<{{theme_uri}}>{%- endfor %}
      }
        GRAPH <https://themes> {?g dcat:theme ?theme_uri .
            ?theme_uri rdfs:label ?VocabCategory }
    {%- else %}
      OPTIONAL {
        GRAPH <https://themes> {?g dcat:theme ?theme_uri .
            ?theme_uri rdfs:label ?VocabCategory }
      }
    {%- endif %}
    OPTIONAL {
      ?MatchURI skos:prefLabel|rdfs:label|dcterms:title|sdo:name ?MatchLabel .
    }
    OPTIONAL {
    ?OptContainer skos:member ?MatchURI ;
                 skos:prefLabel ?OptContainerLabel .
    }
    BIND(?MatchURI AS ?SearchTerm)
    BIND("N/A" AS ?MatchProperty)
    BIND(COALESCE(?MatchLabel,"") AS ?MatchTerm)
    BIND("URI Match" AS ?MethodSubType)
    BIND(COALESCE(?OptContainer,"") AS ?Container)
    BIND(COALESCE(?OptContainerLabel,"") AS ?ContainerLabel)
} GROUP BY ?g ?MatchURI ?MatchProperty ?MatchTerm ?SearchTerm ?Container ?ContainerLabel ?MethodSubType
```
_Query for URIs_

```jinja2
SELECT DISTINCT ?SearchTerm ?MatchURI (SAMPLE(?MatchPropertyAll) AS ?MatchProperty) ?MatchTerm ?Container ?ContainerLabel ?MethodSubType (GROUP_CONCAT(DISTINCT(?VocabCategory);separator=", ") AS ?Categories)
{
  VALUES ?EscapedSearchTerm {
    {%- for term in terms -%}
      {% if proximity %}"\"{{ term }}\"~10"{% else %}"{{ term }}" "\"{{ term }}\""{% endif %}
    {%- endfor %}
  }

  {%- if not predicate %}
    {% set predicate = "skos:definition skos:prefLabel dcterms:description skos:altLabel dcterms:identifier rdfs:label" %}
  {%- else %}
    {% set predicate = predicate %}
  {%- endif %}
  (?MatchURI ?Weight ?MatchTerm ?graph ?MatchProp) text:query ({{ predicate }} ?EscapedSearchTerm 10 ) .
    GRAPH ?g {?MatchURI ?p ?o}
    {%- if theme_uris %}
      VALUES ?theme_uri {
    {%- for theme_uri in theme_uris -%}<{{theme_uri}}>{%- endfor %}
      }
        GRAPH <https://themes> {?g dcat:theme ?theme_uri .
            ?theme_uri rdfs:label ?VocabCategory }
    {%- else %}
      OPTIONAL {
        GRAPH <https://themes> {?g dcat:theme ?theme_uri .
            ?theme_uri rdfs:label ?VocabCategory }
      }
    {%- endif %}
  OPTIONAL {
    ?MatchURI skos:prefLabel|rdfs:label|dcterms:title|sdo:name ?match_label .
  }
  OPTIONAL {
    ?MatchProp skos:prefLabel|rdfs:label|dcterms:title|sdo:name ?prop_label .
    FILTER(LANGMATCHES(LANG(?prop_label), "en") || LANG(?prop_label) = "")
  }
  OPTIONAL {
    ?OptContainer skos:member ?MatchURI ;
                  skos:prefLabel ?OptContainerPrefLabel .
  }
  OPTIONAL {
    ?OptContainer skos:member ?MatchURI ;
                  dcterms:title ?OptContainerTitle .
  }
  OPTIONAL {
    ?MatchURI skos:inScheme ?OptContainer .
    ?OptContainer skos:prefLabel ?OptContainerLabel .
  }
  BIND(COALESCE(?OptContainer,"") AS ?Container)
  BIND(COALESCE(?OptContainerPrefLabel,?OptContainerTitle,"") AS ?ContainerLabel)
  BIND(REPLACE(?EscapedSearchTerm, "\\\\", "") AS ?SearchTermRaw)
  BIND(REPLACE(?SearchTermRaw, "\"", "") AS ?CompletelyUnescaped)
    BIND(
      {% if proximity %}
        "Proximity Match"
      {% else %}
      IF(
        LCASE(?SearchTermRaw) = LCASE(?MatchTerm),
        "Exact Match",
        IF(
          LCASE(?CompletelyUnescaped) = LCASE(?MatchTerm) && LCASE(?SearchTermRaw) != LCASE(?MatchTerm),
          "Exact Match",
          "Wildcard Match"
          )
        )
      {% endif %}
      AS ?MethodSubType
      )
  BIND(COALESCE(?prop_label, ?MatchProp) AS ?MatchPropertyAll)
  BIND(COALESCE(?CompletelyUnescaped, ?SearchTermRaw) AS ?SearchTerm)
} GROUP BY ?g ?MatchURI ?MatchTerm ?SearchTerm ?Container ?ContainerLabel ?MethodSubType
ORDER BY DESC(?MethodSubType) DESC(?Weight)
```
_Query for identifiers and strings_
The results from the queries are in a tabular format, with the following headers:
...
Where a search term has not returned a result with these methods, a follow up query is performed on the these unmatched terms using the proximity method that is a part of Apache Lucene.


## Knowledge base construction
The knowledge base is composed of a number of Oceanographic related ontologies and vocabularies.
These form a set of reference data against which Metadata or data elements can be searched.
The ontologies and vocabularies have been organised into named graphs, with the named graph URIs typically being the namespace of the vocabulary or ontology.
The ontologies and vocabularies have been categorised into the metadata elements (Keywords, Instruments, Parameters, and Platforms) that the terms within the vocabulary describe.
The categorisation is done in practice by mapping the Graph name to a theme URI.
A python script has been provided to automatically create this information as RDF, based on a Google sheet maintained by the BODC.
The Google sheet can be downloaded as an Excel file, and used with the Python script, located at `/src/graph-partitioning/create_system_graph.py`.
The output of the script is an nquads file, which can be uploaded to the triplestore.
An example snippet of the file is as follows:
```nquads
<http://www.w3.org/ns/sosa/> <http://www.w3.org/ns/dcat#theme> <http://vocab.nerc.ac.uk/collection/L19/current/SDNKG04/> <https://themes> .
<http://vocab.nerc.ac.uk/collection/P08/current/> <http://www.w3.org/ns/dcat#theme> <http://vocab.nerc.ac.uk/collection/L19/current/SDNKG03/> <https://themes> .
```
As it was not anticipated that this process would need to be run often, it has not been automated, but this would not be hard to do.

