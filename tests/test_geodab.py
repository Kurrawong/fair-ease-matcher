from xml.etree.ElementTree import Element

import pytest

from src.analyse import get_root_from_remote, analyse_from_xml_structure


@pytest.mark.parametrize(
    "xml_url",
    [
        "https://gs-service-production.geodab.eu/gs-service/services/essi/csw?service=CSW&version=2.0.2&request=GetRecordById&id=dacd69e5-4417-4396-8aa9-166a47e00481&outputschema=http://www.isotc211.org/2005/gmi&elementSetName=full"
    ],
)
def test_get_remote_xml(xml_url):
    etree = get_root_from_remote(xml_url)
    assert isinstance(etree, Element)


@pytest.mark.parametrize(
    "xml_url",
    [
        "https://gs-service-production.geodab.eu/gs-service/services/essi/csw?service=CSW&version=2.0.2&request=GetRecordById&id=dacd69e5-4417-4396-8aa9-166a47e00481&outputschema=http://www.isotc211.org/2005/gmi&elementSetName=full"
    ],
)
def test_analyse_from_xml_url(xml_url):
    results = analyse_from_xml_structure(xml_url, 0.9)
