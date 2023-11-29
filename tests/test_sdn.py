from pathlib import Path

from src.string_functions import extract_from_all
import xml.etree.ElementTree as ET

xml_string = Path(
    "../data/sdn-xml/sdn-open:urn:SDN:CDI:LOCAL:1022-1426-1022-ds04-4.xml"
).read_text()
root = ET.fromstring(xml_string)


def test_extract():
    results = extract_from_all(root)
