import pickle
import os

from pathlib import Path

from .weather_parse import Weather_parse

def getting_the_path_right(f_name):
    
    currentWorking = Path.cwd()
    file_path = currentWorking / f_name
    
    return file_path


def MockTestDataImports():
    # nas_data, summary box, weather_data, and dummy function takes this dummy bulk_flight_deets to the front end.
    
    def pickle_imports_and_processing():
        # TODO: Need to account for titles for dep and dest that has time gate and airport id.

        bulk_flight_deets_path = getting_the_path_right(r"mockTestDataFull.pkl")
        # bulk_flight_deets_path = getting_the_path_right(r"example_flight_deet_full_packet.pkl")       # Old legacy Django

        bulk_flight_deets = pickle.load(open(bulk_flight_deets_path, 'rb'))

        # Changing weather key names from upper case to lower for weathers.
        bulk_flight_deets['dep_weather'] = {
        "datis": bulk_flight_deets['dep_weather']['D-ATIS'],
        "metar": bulk_flight_deets['dep_weather']['METAR'],
        "taf": bulk_flight_deets['dep_weather']['TAF'],}

        # Introducing/interjecting html code within weather.
        weather = Weather_parse()
        bulk_flight_deets['dep_weather'] = weather.processed_weather(
            mock_test_data=bulk_flight_deets['dep_weather'])
    
        # Just mocking/copying departure weather into destination as well 
        bulk_flight_deets['dest_weather'] = bulk_flight_deets['dep_weather']

        return bulk_flight_deets

        # IFR and LIFR weather for departure and destination.
        ind = path_to_be_used + r"raw_weather_dummy_dataKIND.pkl"
        ord = path_to_be_used + r"raw_weather_dummy_dataKORD.pkl"
        with open(ind, 'rb') as f:
            dep_weather = pickle.load(f)
        with open(ord, 'rb') as f:
            dest_weather = pickle.load(f)

        # Injesting the html/css for highlighting here.
        weather = Weather_parse()
        bulk_flight_deets['dep_weather'] = weather.processed_weather(
            dummy=dep_weather)
        weather = Weather_parse()
        bulk_flight_deets['dest_weather'] = weather.processed_weather(
            dummy=dest_weather)


    data_return = pickle_imports_and_processing()
    return data_return

