The semantic analyser backend takes as its input a JSON payload in the following structure for analysis of ISO19115 XML metadata records:

```json
{"xml":
  {"document-1":"<xml content ...>",
    "document-2":"<xml content ...>"},"threshold":1}
```

This input is sent from the frontend web application.

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
Once terms are extracted, they are cleaned. The cleaning process is:

...

For each category of variable, the terms are split out into three further subcategories relating to their datatype. The datatypes are guessed based on the value, rather than being determined based on the location in the XML. 
This more general approach ensures there are not mismatches, but does rely on the accuracy of the functions which guess the type.

The following Python regular expressions are used to guess the types:

...

There are then two kinds of SPARQL query performed, depending on the datatype:
1. URI queries - these use a "direct" querying method against the knowledge base.
2. Identifier and String queries - these use Apache Jena's Full Text Search functionality.

The extracted terms are then used to build SPARQL queries in the above types. In the case of identifiers, only the dcterms:identifier predicate is searched on.
For strings there is no restriction - all properties that are indexed are searched; and the predicate is not relevant for URIs; the URI either does or does not exist in the Knowledge Base. 

In the string based SPARQL queries, a quoted and unquoted variant of each search term is included in the query. This ensures exact matches are found, and can be ranked higher than other matches.

If a user has specified to restrict the search to certain themes, the graph to theme mapping is used to only retrieve results with those themes.

The two SPARQL template queries are shown below. They are written in a templating language called jinja2.

```jinja2
```

The results from the queries are in a tabular format, with the following headers:
...
Where a search term has not returned a result with these methods, a follow up query is performed on the these unmatched terms using the proximity method that is a part of Apache Lucene.


## Knowledge base construction
The knowledge base is composed of a number of Oceanographic related ontologies and vocabularies. These form a set of reference data against which Metadata or data elements can be compared.
