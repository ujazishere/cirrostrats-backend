import pickle
import os
from .weather_parse import WeatherParse

def getting_the_path_right():
    
    currentWorking = os.getcwd()
    print("currentWorking through dummy_files_call.py",currentWorking)
    luis_trailing_path = "Cirrostrats"
    uj_trailing_path = "Cirrostrats\dj"
    ismail_trailing_path = "Cirrostrats/dj/"

    if currentWorking[-11:] == luis_trailing_path:
        dummy_path_to_be_used = currentWorking + "/dj/"
        print('Maybe Luis path:', dummy_path_to_be_used)
    elif currentWorking[-14:] == uj_trailing_path:
        dummy_path_to_be_used = currentWorking + "\\"       # Caution! Escape char issue with `\` Windows path
        print('Maybe UJ path:', dummy_path_to_be_used)
    elif currentWorking[-14:] == ismail_trailing_path or currentWorking:  # This could be just `else` but elaborate for situational awareness.
        dummy_path_to_be_used = currentWorking + "/"        # linux path
        print('Maybe Ismail path or others:', dummy_path_to_be_used)

    # ismail = r"/Users/ismailsakhani/Desktop/Cirrostrats/dj/"
    # ujas = r"C:\Users\ujasv\OneDrive\Desktop\codes\Cirrostrats\dj\\"

    return dummy_path_to_be_used


def dummy_imports():
    dummy_path_to_be_used = getting_the_path_right()   
    
    # nas_data, summary box, weather_data, and dummy function takes this dummy bulk_flight_deets to the front end.
    
    def pickle_imports_and_processing():
        # TODO: Need to account for titles for dep and dest that has time gate and airport id.

        bulk_flight_deets_path = dummy_path_to_be_used + r"example_flight_deet_full_packet.pkl"
        bulk_flight_deets = pickle.load(open(bulk_flight_deets_path, 'rb'))
        return bulk_flight_deets

        # IFR and LIFR weather for departure and destination.
        # TODO: investigate: Just metars for dep and destination are KIND and KORD others are different. Why?
        ind = dummy_path_to_be_used + r"raw_weather_dummy_dataKIND.pkl"
        ord = dummy_path_to_be_used + r"raw_weather_dummy_dataKORD.pkl"
        with open(ind, 'rb') as f:
            dep_weather = pickle.load(f)
        with open(ord, 'rb') as f:
            dest_weather = pickle.load(f)

        # Injesting the html/css for highlighting here.
        weather = WeatherParse()
        bulk_flight_deets['dep_weather'] = weather.processed_weather(
            dummy=dep_weather)
        weather = WeatherParse()
        bulk_flight_deets['dest_weather'] = weather.processed_weather(
            dummy=dest_weather)


        # These seperate out all the weather for ease of work for design. for loops are harder to work with in html so..
        # sending the data as individuals rather than nested dictionaries.
        def weather_separation_process():
            dep_atis = bulk_flight_deets['dep_weather']['D-ATIS']
            dep_metar = bulk_flight_deets['dep_weather']['METAR']
            dep_taf = bulk_flight_deets['dep_weather']['TAF']
            bulk_flight_deets['dep_datis'] = dep_atis
            bulk_flight_deets['dep_metar'] = dep_metar
            bulk_flight_deets['dep_taf'] = dep_taf
            
            dest_datis = bulk_flight_deets['dest_weather']['D-ATIS']
            dest_metar = bulk_flight_deets['dest_weather']['METAR']
            dest_taf = bulk_flight_deets['dest_weather']['TAF']
            bulk_flight_deets['dest_datis'] = dest_datis
            bulk_flight_deets['dest_metar'] = dest_metar
            bulk_flight_deets['dest_taf'] = dest_taf
            return bulk_flight_deets
        return weather_separation_process(),dep_weather,dest_weather

    data_return = pickle_imports_and_processing()
    return data_return

