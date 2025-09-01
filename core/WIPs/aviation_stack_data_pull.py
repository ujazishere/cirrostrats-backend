import requests

params = {
  'access_key': '65dfac89c99477374011de39d27e290a',
  'flight_icao': "UAL414"
}

api_result = requests.get('http://api.aviationstack.com/v1/flights', params)

api_response = api_result.json()


# get the following data and put it into separate variables.
    # Gates, arrival/departure times and Routes if available.
