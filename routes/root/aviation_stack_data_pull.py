import requests
import pprint

flight = "UAL414"


params = {
  'access_key': '65dfac89c99477374011de39d27e290a',
  'flight_icao': flight

}

api_result = requests.get('http://api.aviationstack.com/v1/flights', params)

api_response = api_result.json()

# For access to flightschedules at a particular airport.
params = {
  'access_key': '65dfac89c99477374011de39d27e290a',
  'iataCode': 'EWR',
  'type': 'departure'   # or 'arrival'
}

api_result = requests.get('http://api.aviationstack.com/v1/flights', params)
api_response = api_result.json()
if api_response['error']:
    print('error occoured:',api_response['error'])

if 'error' in api_response:
    print(api_response['error'])
else:
    # print(api_response['data'])
    print(pprint.pprint(len(api_response['data'])))