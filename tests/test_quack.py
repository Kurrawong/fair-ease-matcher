import pytest

from src.string_functions import quack_analyser


@pytest.mark.parametrize("input_str,expected", [
    ("hello world!", "string"),
    ("http://example.com", "URI"),
    ("applePie123", "identifier"),
    ("3 birds", "string"),
    ("123ABC", "identifier"),
    ("https://www.example.com/page?param=value", "URI"),
    ("ftp://fileserver.com/file.txt", "URI"),
    ("file:///home/user/file.txt", "URI"),
    ("    ", "string"),  # only spaces
    ("", "string"),  # empty string
    ("1234", "identifier"),  # just numbers
    ("abcd", "string"),  # just alphabets
    ("apple_pie", "string"),  # underscores (not in identifier definition)
    ("www.example.com", "string"),  # not a valid URI format
    ("3.14", "string"),  # decimal point
    ("apple-pie", "string"),  # hyphen
    ("SDN::L10", "identifier"),  # real example
    ("SDN:L10", "identifier"),  # variation
    ("lithology", "string")
])
def test_quack_analyser(input_str, expected):
    result = quack_analyser(input_str)
    assert result == expected, f"Expected {expected} but got {result} for input {input_str}"