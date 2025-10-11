"""
MongoDB Document Serialization Schema

PROJECT CONTEXT (Post-Restructuring October 2025):
This schema module is part of the organized schema/ directory that handles data serialization
for MongoDB documents. During the project restructuring, this file's location and purpose
were preserved as it provides essential functionality for converting MongoDB BSON data
to JSON-compatible Python dictionaries.

The schema/ directory contains all data transformation and validation logic, following
FastAPI best practices for clean separation of concerns.
"""

from typing import Dict, Any, Iterable
from datetime import datetime, date
from bson import ObjectId

# NoSQL DB sends data via JSON, but is difficult for Python to use JSON data directly
# So Python needs to serialize the data - this is why we use Pydantic and custom serializers
# This handles MongoDB's BSON types (ObjectId, datetime) -> Python native types


def serialize_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serialize a single MongoDB document, preserving common data types.
    """
    def serialize_value(v: Any) -> Any:
        if isinstance(v, (int, float, bool, str)):
            return v
        elif isinstance(v, (datetime, date)):
            return v.isoformat()
        elif isinstance(v, ObjectId):
            return str(v)
        elif isinstance(v, dict):
            return serialize_document(v)
        elif isinstance(v, list):
            return [serialize_value(item) for item in v]
        return str(v)
    
    return {k: serialize_value(v) for k, v in doc.items()}

def serialize_document_list(docs: Iterable[Dict[str, Any]]) -> Iterable[Dict[str, Any]]:
    # Serialize a list of MongoDB documents.
    return (serialize_document(doc) for doc in docs)


"""
# Old use case
# collection returns a dict type database in a pymongo format but is then serialized to use it as dict in python.
def serialize_document(mdbDocument: dict) -> dict:
    return {k: str(v) if isinstance(v, ObjectId) else v for k,v in mdbDocument.items()}

# retrive all the data from the database
# returns a list/array of all the data
def serialize_document_list(allDocuments) -> list:
    # This individual serial is probably not necessary you can just use [airport for airport in airports]
    # The reason for this use case is probably to read into the database as to what the keys are and they are reflected in the individual_serial.
    return [serialize_document(eachDocument) for eachDocument in allDocuments]

"""
def individual_airport_input_data(airport) -> dict:
    return {
        "id": str(airport['_id']),
        "name": airport['name'],
        "code": airport['code'],
        "value": f"{airport['name']} ({airport['code']})",
        "label": f"{airport['name']} ({airport['code']})",
    }


def serialize_airport_input_data(airports) -> dict:
    return [individual_airport_input_data(airport) for airport in airports]
