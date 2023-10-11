from src.currently_unused.odv import find_vocabs_sparql

def test_odv_sparql_generation():
    query = find_vocabs_sparql(["urn:ioos:station:wmo:44004", "urn:ioos:station:wmo:44006"])
    assert query == """
    SELECT (COUNT(?vocab) as ?count)
    WHERE {
    ?concept ?identifier ?urn 
    VALUES ?urn { "urn:ioos:station:wmo:44004" "urn:ioos:station:wmo:44006" }
    }
    """
