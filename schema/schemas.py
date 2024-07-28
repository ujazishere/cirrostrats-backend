# nosql db sends data via json, but is difficult for python to use json data
# so python needs to serialize the data
# this is why we use pydantic

# collection returns a dict type database in a pymongo format but is then serialized to use it as dict in python.
def individual_serial(airport) -> dict:
    return {
        "id": str(airport['_id']),
        "name": airport['name'],
        "code": airport['code'],
        # "gate": flight['gate'],
        # 'flight_number': flight['flight_number'],
        # 'destination': flight['destination'],
    }


# retrive all the data from the database
# returns a list/array of all the data
def list_serial(airports) -> list:
    # This individual serial is probably not necessary you can just use [airport for airport in airports]
    # The reason for this use case is probably to read into the database as to what the keys are and they are reflected in the individual_serial.
    return [individual_serial(airport) for airport in airports]


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
