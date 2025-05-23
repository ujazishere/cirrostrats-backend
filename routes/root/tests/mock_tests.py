from bson import ObjectId
from config.database import db_UJ        # UJ mongoDB
from datetime import datetime, timedelta
import pickle
from pymongo import UpdateOne
import random
from routes.route import aws_jms

def test_aws_jms():
    # ajms data -- latest(redis) and mongo
    with open('mock_ajms_data.pkl','rb') as f:
        data = pickle.load(f)
        for each_flight_data in data:
            # await aws_jms(flight_number=None, mock=True)
            pass

def mt_flight_data():
    mt_flight_data = {
                      **{
          "towerAircraftID": "UAL2480",
          "timestamp": "2025-05-10T15:10:03.243000",
          "destinationAirport": "KSFO",
          "clearance": "003 UAL2480\t7737\tKLAX A320/L\tP1540 239\t280 KLAX SUMMR2 STOKD SERFR SERFR4 KSFO             CLEARED SUMMR2 DEPARTURE STOKD TRSN   CLB VIA SID EXC MAINT 5000FT EXP 280 5 MIN AFT DP,DPFRQ 125.2     ",
          "towerBeaconCode": "7737",
          "version_created_at": "2025-05-10T15:11:32.611000"
        },
        **{
          "flightID": "UAL2075",
          "timestamp": "2025-05-10T15:51:23.088000",
          "organization": "UAL",
          "aircraftType": "A320",
          "registration": "N445UA",
          "departure": "KLAX",
          "arrival": "KSFO",
          "route": "KLAX.SUMMR2.STOKD..SERFR.SERFR4.KSFO/1646",
          "assignedAltitude": "28000.0",
          "currentBeacon": "7737",
          "version_created_at": "2025-05-10T15:52:10.527000"
        },
        **           
        {
            "flightStatsDestination": "KIAH",
            "flightStatsFlightID": "UA492",
            "flightStatsOrigin": "KEWR",
            "flightStatsScheduledArrivalTime": "08:31 CDT",
            "flightStatsScheduledDepartureTime": "05:30 EDT",
            "flightViewArrivalGate": "\nD - D1A\n",
            "flightViewDeparture": "EWR",
            "flightViewDepartureGate": "\nC - C103\n",
            "flightViewDestination": "IAH"
        }
    }
    return mt_flight_data


class MockTestSubmits:
    def __init__(self):
        self.cts = db_UJ['test_st']

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
        cts = db_UJ['test_st']   # create/get a collection
        doc_ids = list(cts.find({},{"_id":1}).limit(15))       # Get limited test document IDs
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
        self.cts.bulk_write(self.update_operations(mdb_set=mdb_set))

    def check_transformed_submits(self):
        original = list(self.cts.find({'submits': {'$exists': True}},{"_id":0,"ph":0,"r_id":0}))
        transformed = [{v1: v2} for d in original for v1, v2 in zip(d.values(), list(d.values())[1:])]
        return transformed
# mts = MockTestSubmits()
# mts.update_operations(mdb_set=True)
# mts.update_submits(mdb_set=True)
# mts.check_transformed_submits()
