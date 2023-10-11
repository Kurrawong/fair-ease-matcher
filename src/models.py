from typing import List, Optional

from pydantic import BaseModel, field_validator, validator
from rdflib import URIRef

from src.string_functions import quack_analyser


class TargetMetadataModel(BaseModel):
    strings: Optional[List[str]]
    uris: Optional[List[str]]
    identifiers: Optional[List[str]]

    @validator('uris', pre=True, each_item=True)
    def validate_uri(cls, uri: str) -> str:
        if uri:
            try:
                _ = URIRef(uri)
            except Exception as e:
                raise ValueError(f"{uri} is not a valid URI") from e
        return uri

    @validator('identifiers', pre=True, each_item=True)
    def validate_identifiers(cls, identifier: str) -> str:
        if identifier:
            if quack_analyser(identifier) != 'identifier':  # Assuming `quack_analyser` is an external function.
                raise ValueError(f"{identifier} is not a valid identifier")
        return identifier
