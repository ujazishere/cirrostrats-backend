import pickle
from routes.route import aws_jms

with open('mock_ajms_data.pkl','rb') as f:
    data = pickle.load(f)

mock_test_data = {
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

for each_flight_data in data:
    await aws_jms(flight_number=None, mock=True)
