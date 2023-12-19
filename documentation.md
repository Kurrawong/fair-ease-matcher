# Semantic Analyser Documentation

[High Level Overview](#high-level-overview)  
[Analyser Input](#analyser-input)  
[Structured XML Analysis](#structured-xml-analysis)  
[Full XML Analysis](#full-xml-analysis)  
[netCDF Analysis](#netcdf-analysis)  
[SPARQL query generation](#sparql-query-generation)  
[Knowledge base construction](#knowledge-base-construction)  
[Federated Search across OntoPortal instances](#federated-search-across-ontoportal-instances)    
[User Interface](#user-interface)  
[Configuration](#configuration)  
[Future Work](#future-work)  
[Appendix A - Artifacts](#appendix-a---artifacts)  
[Appendix B - Live Instances](#appendix-b---live-instances)  

## High Level Overview
This documentation details the functional logic of the Semantic Analyser; predominantly implemented in a FastAPI based Python application. 
The Semantic Analyser requires an instance of Jena Fuseki with full text indexes appropriately constructed.
An optional frontend application can be used to select records for analysis, send these to the backend, and render the results.
The three components are therefore coupled in the following ways:
- requirement of there being a triplestore with full text indexes  
- the format of the input to the analyser  
- the format of the output from the analyser  
These interfaces have been implemented using simple models, and could be modified without much effort.
The Future Work section describes how a semantic model could be implemented create a self describing model of the interfaces and data exchanged between these.
A high level diagram showing the main components is shown below.

 
## Analyser Input
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
1. Structured XML Analysis - based on the structure of ISO19115 XML.
2. "Full" XML Analysis - which strips XML files of all textual fields.
3. netCDF Analysis - which considers only the netCDF metadata.

## Structured XML Analysis

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

## Full XML Analysis
The  full XML Analysis method works by extracting all text using Python's ElementTree library (`element.text`), tails (`element.tail`), xlinks (where the attribute is "{http://www.w3.org/1999/xlink}href"), and attribute values (`element.attrib.values`).
The types (URI, Identifier, or String) are then guessed for each extracted piece of text.
Where the guessed type is a URI, the variant of http/https that the URI is not is added as an additional serach term. Similarly, additional search terms are added with/without trailing slashes to complement the original extracted text.
The guessed types are then collected into a dictionary with keys as the types. As the target metadata element is unknown (there is no context other than the text extracted), the target metadata element is set as "All" such that the query code used for Structured Extraction can be reused.
The queries are then run against the triplestore, using the methodology and queries detailed below.
Where terms are not found, this is recorded, and a link is created to provide search against a number of different "OntoPortal" instances. This additional federated search is documented below.

## netCDF analysis
The netCDF analysis follows a similar methodology as the Structured XML Analysis. A set of terms is extracted from known places in the netCDF metadata, and these are inserted into parameterise SPARQL queries to search against the knowledge base.
The following list details the places within the metadata, and type of target metadata element expected to be extracted from that location.
- Variable Identifiers from the `sdn_parameter_urn` metadata element. These are Sea Data Net URNs.
- Variables Strings, from the metadata element "variables"; including "long" and "standard" versions of these (`long_name` and `standard_name`) attributes on the `variables` metadata element.
- Platform Strings from the `source` and `platform_name` metadata elements
- Platform Identifiers from the `platform_code` metadata elements
- Keyword Strings from the `conventions` metadata element

These extracted metadata elements are then used as arguments in the parameterised queries used for all search methods, and the results are returned and rendered in the same format as per the XML methods.

## SPARQL query generation

The extracted, cleaned, and categorised set of terms is then substituted into two SPARQL queries; one query where the search terms are URIs, and another query where the search terms are strings or identifiers.
This last query uses Apache Jena's Full Text Search functionality.

The extracted terms are then used to build SPARQL queries in the above types. In the case of identifiers, only the dcterms:identifier predicate is searched on.
For strings there is no restriction - all properties that are indexed are searched; and the predicate is not relevant for URIs; the URI either does or does not exist in the Knowledge Base. 

In the string based SPARQL queries, a quoted and unquoted variant of each search term is included in the query. This ensures exact matches are found, and can be ranked higher than other matches.

If a user has specified to restrict the search to certain themes, the graph to theme mapping is used to only retrieve results with those themes.

The two SPARQL template queries are shown below. They are written in a templating language called jinja2.

<details><summary>Query for URIs</summary>  

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

</details>

<details><summary>Query for identifiers and strings</summary>

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
        GRAPH &#003Chttps://themes> {?g dcat:theme ?theme_uri .
            ?theme_uri rdfs:label ?VocabCategory }
    {%- else %}
      OPTIONAL {
        GRAPH &#003Chttps://themes> {?g dcat:theme ?theme_uri .
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
</details>

Where a search term has not returned an exact or URI match with these methods, a follow-up query is performed on the these unmatched terms using the proximity method that is a part of Apache Lucene.

The results from the queries are in a tabular format, with the following headers:
SearchTerm, MatchURI, MatchProperty, MatchTerm, Container, ContainerLabel, MethodSubType, and Categories

These results are returned to the frontend application as JSON, with two additional columns to specify the target metadata element, and the search method (referring to how the query was parameterised, e.g. instruments using identifiers).

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

## Federated Search across OntoPortal instances

Where search terms are not found, a facility has been provided to search for them in a set of related portals (under the "OntoPortal" banner).
The considerations and motivations influencing this design are:
- although these portals provide SPARQL endpoints, hitting these with the queries used against the Semantic Analyser is not possible as they are running on a different triplestore, and the queries for the Semantic Analyser make use of Apache Jena's full text search integration with Apache Lucene. The query syntax would not be interpretable by any other triplestore "out of the box".
- some of these portals are frequently updated and contain a large amount of data; it is preferable to avoid duplicating this data if possible
- the portals offer a full text search facility, as such it is low effort to utilise this
- the results are returned in an RDF format, so future work can easily integrate these responses with the Semantic Analyser processing or results, as the Semantic Analyser is also an RDF based application.

## User interface
The user interface implements the following design goals:
- Users can select metadata records provided by the GeoDAB
- One or more metadata records can be selected for concurrent analysis
- Users can view the raw XML of records selected for analysis 
- The analysis can be resticted to different theme graphs in the triplestore
- The analysis method can be selected
- The results shall be displayed in a tabular format providing information on:
  - the method and submethod used; search and match terms; match URIs/links for the object with the property/object that matched; and the property that was matched on.
  - the portion of search terms for which a result was found in the knowledge graph
- unmatched terms can be searched in 'federated' type manner in other analyser/search systems

## Configuration
The Semantic Analyser backend requires the following environment variables to be specified.

SPARQL_ENDPOINT - the SPARQL endpoint for the Knowledge Base the Semantic Analyser depends on.
SPARQL_USERNAME - a username for the SPARQL endpoint, if Basic Authentication is enabled.
SPARQL_PASSWORD - a password for the SPARQL endpoint, if Basic Authentication is enabled.

The following config section in `src/app/config.json` is used to specify the methods the analyser makes available.
It also lists the theme graphs that the backend can restrict search to within the Knowledge Base.
The current frontend application reads these and renders them as available options in the UI.
To implement further methods or theme restrictions, Python code must be written for the implementation, and the methods will further need to be specified in this config, such that the frontend can read what is available.

<details><summary>Methods Configuration</summary>

```json
{
  "Methods": {
    "metadata": {
      "xml": "Structured XML Extraction",
      "full": "Full XML Extraction"
    },
    "netcdf": {
      "netcdf": "netCDF"
    }
  },
  "Restrict to Themes": {
    "param": "Parameter",
    "inst": "Instrument",
    "plat": "Platform"
  }
}
```
</details>

The User Interface must be supplied with the endpoint at which the analyser is deployed.
Tokens for the different federated search portals (EarthPortal and BioPortal) can also be supplied.
These can be obtained by signing up at the following websites:  
1. [BioPortal](https://bioportal.bioontology.org/)  
2. [EarthPortal](https://earthportal.eu/)

The analyser can be modified rather than configured at a lower level without much difficulty, though knowledge of Python and or SPARQL would be a requirement.
The string cleaning functions for example can altered or 'commented out'.
The SPARQL query can be modified to change the number of Full Text Search results _per search term_ within the `src/sparql/query_template.sparql` file
on line 22. This number is currently set to 10 in the production instance, and 5 in the development instance (see [Appendix B](#appendix-b---live-instances)).
Changing this mostly impacts the number of Wildcard results, which are of a poorer quality than Exact and URI matches. It is suggested that this number could be set as low as possible such that a 'complete' set of Exact matches is returned.

## Future work
The output of the Semantic Analyser (as passed from the backend to the frontend) have a model; at present it is a number of columns that are required for results to be displayed.
To improve upon this model, a formal ontological model could be created to represent these results.
Such a model would be expressed in OWL, and include additional shape validation using SHACL.
The model would extend beyond the results format, to enumerate common input types, and also to provide a framework for interpreting results.
Such a model is conceptually very close to one that would describe machine learning methodologies.
In machine learning terminology, there is a set of raw data (metadata), from which terms are extracted (feature engineering), and these are used with models (Apache Lucene's full text search, and exact matching), to produce predictions with probabilities (1 in the case of URI matches, close to 1 for exact matches, and less than one for other matches).
Creating, or aligining to existing models in this space, will allow for the comparison of the performance of the Semantic Analyser against other analysis methods, enhancing interoperability and highlighing areas of strength and weakness.

## Appendix A - Artifacts

The backend code repository is available on Github [here](https://github.com/Kurrawong/fair-ease-matcher).
Configuration for Apache Jena Fuseki, including the Full Text Search index configuration is within the `compose/` directory of the above repo.
The frontend UI application code is available on Github [here](https://github.com/Kurrawong/bodc-analyser-ui).
Note the 
## Appendix B - Live Instances

At the time of writing there are two instances online, these both utilise the same UI, but can be pointed at different backend analysers.
1. [Production](https://kurrawong.github.io/bodc-analyser-ui/?endpoint=https://99koor0nmj.execute-api.ap-southeast-2.amazonaws.com/production)  
2. [Development](https://kurrawong.github.io/bodc-analyser-ui/?endpoint=https://4p5qsqlhhi.execute-api.ap-southeast-2.amazonaws.com/dev)  
At some point these instances will be brought offline and the Semantic Analyser will be available within BODC.