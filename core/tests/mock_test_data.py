from bson import ObjectId
from config.database import db_UJ        # UJ mongoDB
from datetime import datetime, timedelta
import pickle
from pymongo import UpdateOne
import random
# from routes.route import aws_jms
from ..weather_parse import Weather_parse

async def test_aws_jms():
    """ This wont work because of circular imports. take it out into a jupyter interactive and it shall work
        This ajms data structure is --> latest(redis) and mongo. Then gets processed according to the route function which parses the data.
    """
    with open('mock_ajms_data.pkl','rb') as f:
        data = pickle.load(f)
       # Process each flight
    results = []
    for each_flight_data in data:
        # result = await aws_jms(flightID=None, mock=each_flight_data)
        # results.append(result)
        pass
    print(results)
            # pass


class Mock_data:
    """ The way to use this is to init flight and weather data then use collective to combine them"""
    def __init__(self):
        pass


    def flight_data_init(self):

        self.jms_STDDS_clearance = {
            "towerAircraftID": "UAL4458",
            "timestamp": "2025-05-10T15:10:03.243000",
            "destinationAirport": "KDEN",
            "clearance": "003 UAL2480\t7737\tKDEN A320/L\tP1540 239\t280 KDEN SUMMR2 STOKD SERFR SERFR4 KSFO             CLEARED SUMMR2 DEPARTURE STOKD TRSN   CLB VIA SID EXC MAINT 5000FT EXP 280 5 MIN AFT DP,DPFRQ 125.2     ",
            "towerBeaconCode": "7737",
            "version_created_at": "2025-05-10T15:11:32.611000"
        }
        
        self.jms_FDPS_base = {
            "flightID": "UAL4458",
            "timestamp": "2025-05-10T15:51:23.088000",
            "organization": "UAL",
            "aircraftType": "A320",
            "registration": "N445UA",

            # NOTE: Temporary discrepancy between FDPS and flightstats and flightaware to fix discrepancy issue in frontend
            "departure": "KMCO",            
            "arrival": "KDEN",

            "departureAlternate": "KDEN",
            'arrivalAlternate': 'KDEN',
            'estimatedDepartureTime': '2025-06-05T18:00:00Z',
            "route": "KDEN.SUMMR2.STOKD..SERFR.SERFR4.KDEN/1646",
            "faa_skyvector": "https://skyvector.com/?fpl=%20KGSO%20QUAK8%20SBV%20CREWE%20QUART%20PHLBO4%20KEWR",
            "assignedAltitude": "28000.0",
            "requestedAltitude": "37000.0",
            "currentBeacon": "7737",
            "reassignedBeacon": "1016",
            "version_created_at": "2025-05-10T15:52:10.527000"
        }

        # This will be the new version of returns for flightstats.
        self.flightStatsv2 = {
            'fsDeparture': {'Code': 'HAM',
                'City': 'Hamburg, DE',
                'AirportName': 'Hamburg Airport',
                'ScheduledDate': '20-Jul-2025',
                'ScheduledTime': '13:35 CEST',
                'ActualTime': '13:38 CEST',
                'TerminalGate': '2'},
            'fsArrival': {'Code': 'DUB',
                'City': 'Dublin, IE',
                'AirportName': 'Dublin Airport',
                'ScheduledDate': '20-Jul-2025',
                'ScheduledTime': '14:35 IST',
                'ActualTime': '14:39 IST',
                'TerminalGate': 'T2'},
            'fsDelayStatus': 'On time'
                }
        
        self.flightStats = {
                'flightStatsFlightID': 'UA4508',
                'flightStatsOrigin': 'EWR',
                "flightStatsDestination": "IAH",
                'flightStatsOriginGate': 'C-101',
                'flightStatsDestinationGate': 'D-1',
                'flightStatsScheduledDepartureTime': '15:55 EDT',
                'flightStatsActualDepartureTime': '15:59 EDT',
                'flightStatsScheduledArrivalTime': '18:09 EDT',
                'flightStatsActualArrivalTime': "18:09 EDT",
                'flightStatsDelayStatus':"On time",
            }

        # # Depricated
        # self.flightView = {
        #         "flightViewArrivalGate": "\nD - D1A\n",
        #         "flightViewDeparture": "EWR",
        #         "flightViewDepartureGate": "\nC - C103\n",
        #         "flightViewDestination": "IAH"
        #     }

        self.flightAware = {
                'fa_ident_icao': 'GJS4558',
                'fa_origin': 'KEWR',
                'fa_destination': 'KIAH',
                'fa_registration': 'N551GJ',
                'fa_date_out': '20250606',
                'fa_scheduled_out': '1530Z',
                'fa_estimated_out': '1530Z',
                'fa_scheduled_in': '1721Z',
                'fa_estimated_in': '1655Z',
                'fa_terminal_origin': None,
                'fa_terminal_destination': 'C',
                'fa_gate_origin': None,
                'fa_gate_destination': None,
                'fa_filed_altitude': 'FL350',
                'fa_filed_ete': 4200,
                'fa_route': 'QUAK8 SBV CREWE QUART PHLBO4',
                'fa_sv': 'https://skyvector.com/?fpl=%20KGSO%20QUAK8%20SBV%20CREWE%20QUART%20PHLBO4%20KEWR',
            }

        import datetime as dt
        utc_now = dt.datetime.now(dt.UTC)
        current_time = utc_now.strftime("%m/%d/%Y %H:%M")
        edct = utc_now + timedelta(minutes=150)
        edct = edct.strftime("%m/%d/%Y %H:%M")
        
        self.EDCT_data = [
            {
                'filedDepartureTime': current_time,
                'edct': edct,
                'controlElement': 'EWR',
                'flightCancelled': 'No'
                },
            {
                'filedDepartureTime': current_time,
                'edct': edct,
                'controlElement': 'EWR',
                'flightCancelled': 'No'
                }
        ]

        self.nas_singular_mock = {
                'Ground Stop': {
                    'Airport': 'DEN',
                    'Reason': 'other',
                    'End Time': '8:15 pm EDT'
                    },
                'Airport Closure': {
                    'Airport': 'DEN',
                    'Reason': '!DEN 05/042 BOS AD AP CLSD TO NON SKED TRANSIENT GA ACFT EXC PPR 617-561-2500 2505030256-2510300359',
                    'Start': 'May 03 at 02:56 UTC.',
                    'Reopen': 'Oct 30 at 03:59 UTC.'
                    },
                'Ground Delay': {
                    'Airport': 'DEN',
                    'Reason': 'other',
                    'Average Delay': '1 hour and 40 minutes',
                    'Maximum Delay': '3 hours and 39 minutes',
                    },
                'Arrival/Departure Delay': {
                    'Airport': 'DEN',
                    'Reason': 'TM Initiatives:SWAP:WX',
                    'Type': 'Departure',
                    'Minimum': '1 hour and 46 minutes',
                    'Maximum': '2 hours',
                    'Trend': 'Increasing'
                    }
            }
        self.ajms_mock = {'latest': None, 'mongo': [{'flightID': 'GJS4404', 'matching_versions': [{'timestamp': '2025-08-26T18:17:33.889000', 'organization': 'GJS', 'aircraftType': 'CRJ7', 'registration': 'N562GJ', 'departure': 'KEWR', 'arrival': 'KCVG', 'estimatedDepartureTime': '2025-08-26T18:45:00Z', 'route': 'KEWR..PARKE.J6.COLNS.GAVNN7.KCVG/0132', 'requestedAltitude': '30000.0', 'towerAircraftID': {'timestamp': '2025-08-26T18:17:39.247778+00:00', 'value': 'GJS4404'}, 'destinationAirport': {'timestamp': '2025-08-26T18:17:39.247778+00:00', 'value': 'KCVG'}, 'clearance': {'timestamp': '2025-08-26T18:17:39.247778+00:00', 'value': '001 GJS4404\t1676\tKEWR CRJ7/L\tP1845 958\t300 KEWR PARKE J6 COLNS GAVNN7 KCVG @TCAS           CLEARED EWR5 DEPARTURE    MAINTAIN 2500FT EXP 300 10 MIN AFT DP,DPFRQ 119.2 CTC GROUND 121.8 FOR TAXI   '}, 'towerBeaconCode': {'timestamp': '2025-08-26T18:17:39.247778+00:00', 'value': '1676'}, 'version_created_at': '2025-08-26T18:19:31.516000'}, {'timestamp': '2025-08-26T19:03:54.927000', 'organization': 'GJS', 'aircraftType': 'CRJ7', 'registration': 'N562GJ', 'departure': 'KEWR', 'arrival': 'KCVG', 'route': 'KEWR..PARKE.J6.COLNS.GAVNN7.KCVG/2035', 'assignedAltitude': '30000.0', 'currentBeacon': '1676', 'version_created_at': '2025-08-26T19:05:06.015000'}, {'timestamp': '2025-08-26T19:30:10.576000', 'organization': 'GJS', 'aircraftType': 'CRJ7', 'registration': 'N562GJ', 'departure': 'KEWR', 'arrival': 'KCVG', 'route': 'KEWR./.PARKE251038..STEVY.GAVNN7.KCVG/2035', 'assignedAltitude': '30000.0', 'currentBeacon': '1676', 'version_created_at': '2025-08-26T19:31:37.248000'}]}]}

    def weather_data_init(self,html_injected_weather):
        self.raw_datis_combined = [{'airport': 'KEWR',
                        'type': 'combined',
                        'code': 'F',
                        'datis': 'EWR ATIS INFO F 1751Z. 29011G17KT 1SM BKN004 BKN190 BKN250 29/15 A2981 (TWO NINER EIGHT ONE). ILS RWY 22L APCH IN USE. DEPARTING RY 22R FROM INT W 10,150 FEET TODA. RWY 22L TDZL OTS, RWY 22L CL LIGHTS OTS. GBAS OTS. VIP TFR. NO CLASS "B" SERVICES. USE CAUTION FOR BIRDS AND CRANES IN THE VICINITY OF EWR. READBACK ALL RUNWAY HOLD SHORT INSTRUCTIONS AND ASSIGNED ALT. ...ADVS YOU HAVE INFO F.',
                        'time': '1751',
                        'updatedAt': '2025-09-26T18:03:40.3038413Z'}]
        self.raw_datis_arr_dep = [{'airport': 'KPHL',
                        'type': 'arr',
                        'code': 'L',
                        'datis': 'PHL ARR INFO L 1754Z. 29009KT 1/2SM OVC004 28/15 A2984 (TWO NINER EIGHT FOUR) RMK AO2 SLP102 T02830150 10283 20211 58009. SIMUL APCHS TO INTERSECTING RWYS. ARRIVALS EXPECT ILS APCH RWY 27R, OR VISUAL APPROACH RWY 35. NOTAMS... ILS RWY 26 OTS, RY 27L PAPI OTS. TWY P CLSD BTN, TWY, W AND TWY N . .. TWY U CLSD BTN, TWY, P AND TWY S . .. TWY G CLSD BTN, TWY, J AND TWY E . .. TWY T CLSD, BTN RWY, 27R AND TWY P . TWY E CLSD, BTN RWY, 35 AND TWY B . TWY E1 CLSD, TWY E2 CLSD TWY S4 CLSD . RWY 9 RIGHT HOLD PAD CLSD. TOWER FREQ 118.5 FOR ALL RUNWAYS. ADZ GATE ASSIGNMENT TO APPROACH CTL ON INITIAL CTC. PAJA IN PROGRESS 2NM NE OF ZMRMN INTERSECTION AT ONE7N AOB 13500 ALL ACFT USE CAUTION. ...ADVS YOU HAVE INFO L.',
                        'time': '1754',
                        'updatedAt': '2025-09-26T18:03:13.6447762Z'},
                        {'airport': 'KPHL',
                        'type': 'dep',
                        'code': 'Y',
                        'datis': 'PHL DEP INFO Y 1754Z. 29009KT 1SM BKN015 SCT110 SCT260 28/15 A2984 (TWO NINER EIGHT FOUR) RMK AO2 SLP102 T02830150 10283 20211 58009. DEPG 27L, RWY 35. NOTAMS... RY 27L PAPI OTS. TWY P CLSD BTN, TWY, W AND TWY N . .. TWY U CLSD BTN, TWY, P AND TWY S . .. TWY G CLSD BTN, TWY, J AND TWY E . .. TWY T CLSD, BTN RWY, 27R AND TWY P . TWY E CLSD, BTN RWY, 35 AND TWY B . TWY E1 CLSD, TWY E2 CLSD TWY S4 CLSD . RWY 9 RIGHT HOLD PAD CLSD. TOWER FREQ 118.5 FOR ALL RUNWAYS. PAJA IN PROGRESS 2NM NE OF ZMRMN INTERSECTION AT ONE7N AOB 13500 ALL ACFT USE CAUTION. ...ADVS YOU HAVE INFO Y.',
                        'time': '1754',
                        'updatedAt': '2025-09-26T18:03:14.6154463Z'}]
        self.raw_datis_error = {'error': 'No results found'}

        self.processed_datis_combined = Weather_parse().datis_processing(self.raw_datis_combined)
        self.processed_datis_arr_dep = Weather_parse().datis_processing(self.raw_datis_arr_dep)
        self.processed_datis_error = Weather_parse().datis_processing(self.raw_datis_error)

        # TODO: if processed internally use the function instead of the raw data that was processed by the function. Then use this class to spit out structured data structure.

        self.weather_raw = {
            'datis': Weather_parse().datis_processing(self.raw_datis_arr_dep),
            # 'datis': 'DEN ARR INFO L 1953Z. 27025G33KT 10SM FEW080 SCT130 SCT200 01/M19 A2955 (TWO NINER FIVE FIVE) RMK AO2 PK WND 29040/1933 SLP040. LLWS ADZYS IN EFCT. HAZUS WX INFO FOR CO, KS, NE, WY AVBL FM FLT SVC. PIREP 30 SW DEN, 2005Z B58T RPRTD MDT-SVR, TB, BTN 14THSD AND 10 THSD DURD. PIREP DEN AREA,, 1929Z PC24 RPRTD MDT, TB, BTN AND FL 190 DURD. EXPC ILS, RNAV, OR VISUAL APCH, SIMUL APCHS IN USE, RWY 25, RWY 26. NOTICE TO AIR MISSION. S C DEICE PAD CLOSED. DEN DME OTS. BIRD ACTIVITY VICINITY ARPT. ...ADVS YOU HAVE INFO L.',
            'datis_ts': "0756Z",
            'metar': 'KDEN 012054Z 16004KT 1/2SM R05L/P6000FT BR OVC004 08/08 A2978 RMK AO2 SFC VIS 3 SLP085 T00830078 56006',
            'metar_ts': "300830Z",
            'taf': 'KDEN 022355Z 0300/0324 00000KT 2SM BR VCSH FEW015 OVC060 TEMPO 0300/0303 1 1/2SM FG BKN015\n    FM030300 00000KT 1SM -SHRA FG OVC002\n    FM031300 19005KT 3/4SM BR OVC004\n    FM031500 23008KT 1/26SM OVC005\n    FM031800 25010KT 1/4SM OVC015\n    FM032100 25010KT M1/4SM BKN040',
            'taf_ts': "300330Z",
        }

        if html_injected_weather:
            wp = Weather_parse()
            self.weather = wp.html_injected_weather(
                weather_raw=self.weather_raw)
        else:
            self.weather = self.weather_raw

    def collective(self,):
        """ initialize flight_data first to use this function since variables in here are from flight_data"""
        self.primary_flight_data_collective = {
            **self.jms_STDDS_clearance,
            **self.jms_FDPS_base,
            **self.flightStats,
            # **self.flightView,
            **self.flightAware,
        }

        self.weather_collective = {
            'departureWeatherLive': self.weather,
            'arrivalWeatherLive': self.weather,
            'departureAlternateWeatherLive': self.weather,
            'arrivalAlternateWeatherLive': self.weather,
        }

        self.NAS_collective = {
            'arrivalAlternateNAS': self.nas_singular_mock,
            'arrivalNAS': self.nas_singular_mock,
            'departureAlternateNAS': self.nas_singular_mock,
            'departureNAS': self.nas_singular_mock,
        }

        self.collective = {
            'flightData':self.primary_flight_data_collective,
            'weather': self.weather_collective,
            'NAS': self.NAS_collective,
            'EDCT': self.EDCT_data,
        }
        return self.collective


    def mongo_collection_mock(self,):
        """ set of mock data from all collections across all mongoDB"""

        """ Search Index Collection: a collection that servers dropdown suggestions to the frontend, keeps track of popularity hits and submits.
            Fields:
                r_id: is the reference ID of the associated collection for associated data retrival.
                type: type of search term(st) -- associated with a particular type of collection - airport, fid(flightID), terminal/gate
                ph: Popularity hit - a form of ranking score that is prorcessed through QueryClassifier's normalization function. 
                submits: the submits on the frontend.
        """
        self.search_index_collection = [
            {
                # airport search index collection doc
                '_id': ObjectId('6821b9805795b7ff557e3153'),
                'r_id': ObjectId('66176711170d1d57a24df7ce'),       # this is original _id from collection_airport
                'airport_st': 'DCA - Ronald Reagan Washington Ntl Airport',
                'ph': 2.4973989440488236,           # Popularity hit - ranking score
                'submits': [
                    datetime.datetime(2025, 5, 23, 15, 57, 51, 796000),
                    datetime.datetime(2025, 6, 1, 7, 20, 45, 448000)]},

                # flight search index collection doc
                {'_id': ObjectId('6821b9805795b7ff557e3161'),
                'r_id': ObjectId('67e4ca4228d60c5468f315c2'),
                'fid_st': 'GJS4416',
                'ph': 1.3010847436299786,
                'submits': [
                    datetime.datetime(2025, 5, 29, 20, 29, 55, 402000),
                    datetime.datetime(2025, 6, 10, 16, 15, 59, 15000)]},

                # terminal search index collection doc
                {'_id': ObjectId('6821b9805795b7ff557e3154'),
                'r_id': ObjectId('66eb8aa5122bd9fc2f88896a'),
                'Terminal/Gate': 'Terminal C - C71X',
                'ph': 2.3975190568219413,
                'submits': [
                    datetime.datetime(2025, 6, 10, 12, 16, 14, 469000)]

            },
        ]

        self.collection_airport = [
            {'_id': ObjectId('66176711170d1d57a24df6a5'),
            'name': 'Troy Municipal At N Kenneth Campbell Field Airport',
            'code': 'TOI'}
        ] 

        self.collection_weather = [
            {'_id': ObjectId('66b8fb323bb8c0e553b1ce79'),
            'airport_id': ObjectId('66176711170d1d57a24dfc58'),
            'code': 'PHL',
            'weather': {'datis': {
                                    'combined': 'N/A',
                                    'arr': 'PHL ARR INFO K 2054Z. VRB05KT 10SM FEW042 FEW270 29/15 A3006 (THREE ZERO ZERO SIX). SIMUL APCHS TO INTERSECTING RWYS. ARRIVALS EXPECT ILS APCH RWY 27R, VISUAL APPROACH RWY 35. NOTAMS... ILS RWY 26 OTS, RY 27L PAPI OTS. TWY P CLSD BTN, TWY, W AND TWY N . .. TWY U CLSD BTN, TWY, P AND TWY S . .. TWY T CLSD, BTN RWY, 27R AND TWY P . TWY E CLSD, BTN RWY, 35 AND TWY B . TWY E1 CLSD, TWY E2 CLSD TWY S4 CLSD . RWY 9 RIGHT HOLD PAD CLSD. TOWER FREQ 118.5 FOR ALL RUNWAYS. ADZ GATE ASSIGNMENT TO APPROACH CTL ON INITIAL CTC. PAJA IN PROGRESS 7 NM SE OF SPUDS INT AT CKZ AOB 14500 ALL ACFT USE CAUTION. ...ADVS YOU HAVE INFO K.',
                                    'dep': 'PHL DEP INFO X 2054Z. VRB05KT 10SM FEW042 FEW270 29/15 A3006 (THREE ZERO ZERO SIX). DEPG 27L, RWY 35. NOTAMS... RY 27L PAPI OTS. TWY P CLSD BTN, TWY, W AND TWY N . .. TWY U CLSD BTN, TWY, P AND TWY S . .. TWY T CLSD, BTN RWY, 27R AND TWY P . TWY E CLSD, BTN RWY, 35 AND TWY B . TWY E1 CLSD, TWY E2 CLSD TWY S4 CLSD . RWY 9 RIGHT HOLD PAD CLSD. TOWER FREQ 118.5 FOR ALL RUNWAYS. PAJA IN PROGRESS 7 NM SE OF SPUDS INT AT CKZ AOB 14500 ALL ACFT USE CAUTION. ...ADVS YOU HAVE INFO X.'
                                    },
                        'metar': 'METAR KPHL 282054Z VRB05KT 10SM FEW042 FEW270 29/15 A3006 RMK AO2 SLP177 T02940150 55004 $',
                        'taf': 'TAF KPHL 282116Z 2821/2924 32004KT P6SM FEW250 \n  FM282300 VRB02KT P6SM SKC \n  FM291000 05005KT P6SM SCT250 \n  FM291800 08004KT P6SM BKN250\n'},
                        'ICAO': 'KPHL'}
        ]

        self.gate_collection = [
            {
                'Scheduled': 'July 21, 2025 18:00',
                'Departed': '18:09',        # mind Departed vs Estimated
                'Gate': 'C83',
                'FlightID': 'UA1707'},
            {
                'Scheduled': 'July 21, 2025 18:10',
                'Estimated': '18:03',
                'Gate': 'C115',
                'FlightID': 'UA1733'},
        ]


class MockTestSubmits:
    def __init__(self):
        self.search_index_collection = db_UJ['test_st']

    def random_date_gen(self, simplify=False, total_dates=5):
        def df(dt):
            return dt.strftime("%m-%d")

        now = datetime.now()  # Get current date and time
        dates = []

        # Generate dates for the last 3 days (today and the two previous days)
        for i in range(3):
            date = now - timedelta(days=i)
            dates.append(date)

        # Randomly select 5 items from these dates (with replacement)
        random_items = random.choices(dates, k=random.randint(1, total_dates))
        # If simplify is True, format the dates
        if simplify:
            # Format the dates using your df function
            formatted_items = [df(item) for item in random_items]
            return formatted_items    
        else:
            return random_items
        # Format the dates using your df function
        # formatted_items = [df(item) for item in random_items]
        # return formatted_items

    def update_operations(self,mdb_set=False):
        search_index_collection = db_UJ['test_st']   # create/get a collection
        doc_ids = list(search_index_collection.find({},{"_id":1}).limit(15))       # Get limited test document IDs
        update_operation = []
        for i in doc_ids:
            juice = {'submits':self.random_date_gen(simplify=False, total_dates=15)}
            # Use this to remove all the submits fields
            # Use this to simulate setting the new submits field with mock timestamps
            set_ops = {'$set': juice} if mdb_set else {'$unset': {'submits': ''}}
            update_operation.append(
                UpdateOne(
                {"_id": ObjectId(i['_id'])},
                set_ops
            ))
        return update_operation

    def update_submits(self, mdb_set):
        self.search_index_collection.bulk_write(self.update_operations(mdb_set=mdb_set))

    def check_transformed_submits(self):
        original = list(self.search_index_collection.find({'submits': {'$exists': True}},{"_id":0,"ph":0,"r_id":0}))
        transformed = [{v1: v2} for d in original for v1, v2 in zip(d.values(), list(d.values())[1:])]
        return transformed
# mts = MockTestSubmits()
# mts.update_operations(mdb_set=True)
# mts.update_submits(mdb_set=True)
# mts.check_transformed_submits()
