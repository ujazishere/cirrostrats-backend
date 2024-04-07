# nosql db sends data via json, but is difficult for python to use json data
# so python needs to serialize the data
# this is why we use pydantic

# first we conect our todo object to connect  to dict
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
