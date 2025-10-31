from datetime import datetime, timezone, timedelta
import logging
from core.tests.weather_test import Weather_test
from routes.flight_aggregator_routes import flight_stats_url
from services.notification_service import send_telegram_notification_service
from config.database import collection_weather_uj
from config.database import collection_flights

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')  # noqa: F821
logger = logging.getLogger()

class Broad_test:
    def __init__(self):
        pass

    def health_check(self):
        # Everyday 9am EST
        send_telegram_notification_service(message='Celery is up!')

    async def fs_test(self):
        """ Test that the FlightStats API returns data for 4 flights that go out everyday """
        flightIDs = ['UA414','B62584', 'AA2759', 'DL1658']
        for flightID in flightIDs:
            fs_returns = await flight_stats_url(flightID)
            if not fs_returns:
                message = f'FlightStats test failed for {flightID}'
                send_telegram_notification_service(message)
            
    def jms_test(self):
        """ Find the most recent flight by sorting on the latest version timestamp """

        pipeline = [
            {"$sort": {"versions.version_created_at": -1}},
            {"$limit": 1},
            {"$project": {
                "flightID": 1,
                "latest_version_time": {"$arrayElemAt": ["$versions.version_created_at", -1]}
            }}
        ]
        
        result = list(collection_flights.aggregate(pipeline))
        if not result:
            message = "JMS Test: No flights found in database"
            send_telegram_notification_service(message=message)
            logger.warning(message)
            return
        
        latest_flight = result[0]
        latest_version_time = latest_flight['latest_version_time']
        today = datetime.now(timezone.utc).date()
        
        # Check if the latest version was created today
        if latest_version_time.date() != today:
            message = (f"JMS Test ALERT: Latest flight {latest_flight['flightID']} "
                    f"was last updated on {latest_version_time.date()}, not today ({today})")
            send_telegram_notification_service(message=message)
            logger.error(message)
        else:
            logger.info(f"JMS Test: Latest flight {latest_flight['flightID']} updated today at {latest_version_time}")

    def flight_aware_test(self):
        pass

    def weather_test(self):
        """Test that weather data for PHL is fresh (within last 2 hours)"""

        current_utc = datetime.now(timezone.utc)
        two_hours_ago = current_utc - timedelta(hours=3)

        test_codes = ['EWR', 'PHL', 'ORD', 'STL', 'RIC']
        
        for code in test_codes:
            weather_doc = collection_weather_uj.find_one({'code': code})
            if not weather_doc:
                message = "Weather Test: No weather document found"
                send_telegram_notification_service(message=message)
                # TODO memory optimize - this logger can probably use rotation or counter so that it doesn't blow up the size.
                logger.error(message)
                return
        
            # Extract nested weather data
            weather_data = weather_doc.get('weather', {})
            
            wt = Weather_test()
            issues = wt.metar_time_test(weather_data, current_utc, two_hours_ago)
            
            # Report results
            if issues:
                message = "Weather Test ALERT:\n" + "\n".join(issues)
                send_telegram_notification_service(message=message)
                logger.error(message)
            else:
                message = "Weather Test PASS: weather data is fresh (within 2 hours)"
                logger.info(message)

    def nas_test(self):
        pass

    def gate_test(self):
        pass

