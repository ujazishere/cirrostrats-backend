"""
Task Handlers Module

This module contains the business logic for all Celery tasks, separated from
the task definitions themselves. This allows for:
- Testing individual handlers in isolation
- Reusing handlers outside of Celery
- Better code organization and maintainability
"""
import asyncio
import logging
import json
import datetime as dt
import redis
from typing import Optional, Dict, Any

from core.weather_fetch import Bulk_weather_fetch
from core.gate_processor import Gate_processor
from core.api.nas import NASExtracts
from core.tests.broad_test import Broad_test
from utils.tele import Tele_bot

logger = logging.getLogger(__name__)


class WeatherTaskHandlers:
    """Handlers for weather-related tasks"""
    
    @staticmethod
    async def fetch_datis() -> str:
        """Fetch and store DATIS weather data"""
        bwf = Bulk_weather_fetch()
        await bwf.bulk_fetch_and_store_by_type(weather_type='datis')
        zulutime = dt.datetime.now(dt.timezone.utc).strftime("%d %H:%M")
        return f'Celery task completed for fetching datis. timestamp - {zulutime}'
    
    @staticmethod
    async def fetch_metar() -> str:
        """Fetch and store METAR weather data"""
        bwf = Bulk_weather_fetch()
        await bwf.bulk_fetch_and_store_by_type(weather_type='metar')
        zulutime = dt.datetime.now(dt.timezone.utc).strftime("%d %H:%M")
        return f'Celery task completed for fetching metar. timestamp - {zulutime}'
    
    @staticmethod
    async def fetch_taf() -> str:
        """Fetch and store TAF weather data"""
        bwf = Bulk_weather_fetch()
        await bwf.bulk_fetch_and_store_by_type(weather_type='taf')
        zulutime = dt.datetime.now(dt.timezone.utc).strftime("%d %H:%M")
        return f'Celery task completed for fetching TAF. timestamp - {zulutime}'


class GateTaskHandlers:
    """Handlers for gate-related tasks"""
    
    @staticmethod
    def fetch_gates() -> str:
        """Scrape and store gate information"""
        gp = Gate_processor()
        gp.scrape_and_store()
        zulutime = dt.datetime.now(dt.timezone.utc).strftime("%d %H:%M")
        return f'Celery task completed for fetching gates. timestamp - {zulutime}'
    
    @staticmethod
    def update_gates_recurrent() -> str:
        """Update gate information for flights around current time"""
        gp = Gate_processor()
        gp.recurrent_updater()
        zulutime = dt.datetime.now(dt.timezone.utc).strftime("%d %H:%M")
        return f'Celery task completed for recurrent gate update. timestamp - {zulutime}'
    
    @staticmethod
    def clear_historical_gates(hours: int = 30) -> str:
        """Clear historical gate data older than specified hours"""
        gp = Gate_processor()
        gp.mdb_clear_historical(hours=hours)
        zulutime = dt.datetime.now(dt.timezone.utc).strftime("%d %H:%M")
        return f'Celery task completed for clearing historical gate data older than {hours} hours. timestamp - {zulutime}'


class NASTaskHandlers:
    """Handlers for NAS (National Airspace System) related tasks"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize NAS task handler
        
        Args:
            redis_client: Redis client instance. If None, creates a new one.
        """
        self.redis_client = redis_client or redis.Redis(host='redis', port=6379, db=0)
        self.tele_bot = Tele_bot()
    
    def _send_telegram_notification(self, message: str, error: bool = False) -> None:
        """Send telegram notification"""
        if error:
            send_to = [self.tele_bot.ISMAIL_CHAT_ID, self.tele_bot.UJ_CHAT_ID]
            logger.error('Error, sending notification to Ismail and UJ')
        else:
            logger.info('Sending to UJ only')
            send_to = [self.tele_bot.UJ_CHAT_ID]
        
        self.tele_bot.send_message(
            chat_id=send_to,
            MESSAGE=message,
            token=self.tele_bot.TELE_MAIN_BOT_TOKEN
        )
    
    def fetch_and_monitor_nas(
        self, 
        nas_type: str = 'ground_stop_packet',
        redis_key: str = 'juice'
    ) -> Dict[str, Any]:
        """
        Fetch NAS data and monitor for changes
        
        Args:
            nas_type: Type of NAS data to monitor
            redis_key: Redis key to store previous data for comparison
            
        Returns:
            Dictionary with status and data
        """
        nas = NASExtracts()
        nas_data = nas.nas_xml_processor()
        
        if not nas_data:
            self._send_telegram_notification("Error: NAS", error=True)
            return {
                'status': 'error',
                'message': "Error: NAS - nas_data empty"
            }
        
        juice = nas_data.get(nas_type)
        zulutime = dt.datetime.now(dt.timezone.utc).strftime("%d %H:%M")
        message = f"{nas_type} @ {zulutime} - {juice}"
        
        # Check for changes
        previous_juice = self.redis_client.get(redis_key)
        
        if previous_juice and json.loads(previous_juice.decode('utf-8')) != juice:
            # Data changed
            self.redis_client.set(redis_key, json.dumps(juice))
            self._send_telegram_notification("NAS: data changed, setting new data: " + message)
            return {
                'status': 'changed',
                'message': "NAS: data changed, setting new data",
                'data': juice
            }
        elif not previous_juice:
            # First run - no previous data
            self.redis_client.set(redis_key, json.dumps(juice))
            self._send_telegram_notification("NAS: Absolute new message: " + message)
            return {
                'status': 'new',
                'message': 'NAS: Absolute new message',
                'data': message
            }
        else:
            # No change
            return {
                'status': 'no_change',
                'message': "NAS: no change"
            }


class TestingTaskHandlers:
    """Handlers for testing tasks"""
    
    @staticmethod
    async def run_fs_test() -> None:
        """Run FlightStats test"""
        bt = Broad_test()
        await bt.fs_test()
    
    @staticmethod
    def run_all_tests() -> str:
        """
        Run all tests in core/tests/broad_test.py
        
        Returns:
            Completion message
        """
        bt = Broad_test()
        bt.jms_test()
        bt.weather_test()  # TODO test: weather test is throwing error currently within celery
        
        # Run async test
        asyncio.run(TestingTaskHandlers.run_fs_test())
        
        # TODO test: Remaining logic
        # bt.flight_aware_test()
        # bt.nas_test()
        # bt.gate_test()
        
        return 'Generic testing completed'
    
    @staticmethod
    def run_jms_test() -> None:
        """Run JMS test only"""
        bt = Broad_test()
        bt.jms_test()
    
    @staticmethod
    def run_weather_test() -> None:
        """Run weather test only"""
        bt = Broad_test()
        bt.weather_test()
    
    @staticmethod
    async def run_fs_test_isolated() -> None:
        """Run FlightStats test only"""
        await TestingTaskHandlers.run_fs_test()

