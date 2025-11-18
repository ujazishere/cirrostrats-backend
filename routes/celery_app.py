"""
Celery Task Definitions

This module defines Celery tasks that wrap the business logic handlers.
All business logic is separated into routes/task_handlers.py for better
testability and maintainability.

***CAUTION***
Celery doesn't work with async directly, so avoid using asyncio directly
on celery_app.task functions. Instead use asyncio.run(async_function())
where the async_function() can be any async function you want to schedule.
"""
import asyncio
import logging
from celery import Celery
from celery.schedules import crontab

from routes.task_handlers import (
    WeatherTaskHandlers,
    GateTaskHandlers,
    NASTaskHandlers,
    TestingTaskHandlers
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Celery app
celery_app = Celery(
    'tasks',
    broker='redis://redis:6379/0',
    backend='redis://redis:6379/0'
)

celery_app.conf.timezone = 'UTC'

# Initialize task handlers
_weather_handlers = WeatherTaskHandlers()
_gate_handlers = GateTaskHandlers()
_nas_handlers = NASTaskHandlers()
_testing_handlers = TestingTaskHandlers()


# ============================================================================
# Weather Tasks
# ============================================================================

@celery_app.task
def DatisFetch():
    """Fetch and store DATIS weather data"""
    return asyncio.run(_weather_handlers.fetch_datis())


@celery_app.task
def MetarFetch():
    """Fetch and store METAR weather data"""
    return asyncio.run(_weather_handlers.fetch_metar())


@celery_app.task
def TAFFetch():
    """Fetch and store TAF weather data"""
    return asyncio.run(_weather_handlers.fetch_taf())


# ============================================================================
# Gate Tasks
# ============================================================================

@celery_app.task
def GateFetch():
    """Scrape and store gate information"""
    return _gate_handlers.fetch_gates()


@celery_app.task
def GateRecurrentUpdater():
    """Update gate information for flights around current time"""
    return _gate_handlers.update_gates_recurrent()


@celery_app.task
def GateClear():
    """Clear historical gate data older than 30 hours"""
    return _gate_handlers.clear_historical_gates(hours=30)


# ============================================================================
# NAS Tasks
# ============================================================================

@celery_app.task
def nasFetch():
    """
    NAS fetcher that checks for changes in specific nas data and sends
    telegram notification on change.
    """
    result = _nas_handlers.fetch_and_monitor_nas(
        nas_type='ground_stop_packet',
        redis_key='juice'
    )
    
    # Return format compatible with existing code
    if result['status'] == 'error':
        return result['message']
    elif result['status'] == 'changed':
        return result['message'], result['data']
    elif result['status'] == 'new':
        return result['message'], result['data']
    else:
        return result['message']


# ============================================================================
# Testing Tasks
# ============================================================================

@celery_app.task
def generic_testing():
    """
    Generic testing function that runs all the tests in core/tests/broad_test.py
    """
    return _testing_handlers.run_all_tests()


# ============================================================================
# Periodic Task Scheduling
# ============================================================================

# Add periodic task scheduling
celery_app.conf.beat_schedule = {

    # TODO Test: This beat schedule at times has not been working. Need a mechanism that makes sure that these schedules are run successfully and
                # loggs it in a rolling file -possiby redis cache like one in NASFetch
            # -- Following maybe too complicated and may require constant mx--> Maybe decrease variables and loose endpoints to reduce complexity.
                # when it doesn't fetch the weather data it should log or retry every min or so increasing every iteration and stop when it becomes available.
                # once stopped return to original schedule of 53 past?
                # If data unavailable for extended period then stop fetching completely and return to original schedule, notify about issue after 3 hours of inactive fetch.
            # Reducce complexity- What is important? weather should exist and should be accurate. If its not send notification at a threshold and continue fetch.
            #  spin up an instance to run these tasks if the celery task fails? but that may not be necessary.
                #  Only attend to it when critical failure occurs?

    'run-datisfetch-every-10-mins': {
        'task': 'routes.celery_app.DatisFetch',      # The task function that needs to be scheduled
        'schedule': crontab(minute='5-55/10'),          # frequency of the task. In this case every 10 mins starting from 5 to 55 minutes past the hour
        # 'args': (16, 16)          # Arguments to pass to the task function
    },
    'run-metarfetch-every-53-mins-past-hour': {
        'task': 'routes.celery_app.MetarFetch',      # The task function that needs to be scheduled
        'schedule': crontab(minute=54),  # frequency of the task. In this case every 53 mins past the hour.
        # 'args': (16, 16)          # Arguments to pass to the task function
    },
    'run-TAFfetch-every-4-hours': {
        'task': 'routes.celery_app.TAFFetch',      # The task function that needs to be scheduled
        'schedule': crontab(minute=21, hour='5,11,17,23'),  # Run at 05:21, 11:21, 17:21, and 23:21 UTC
        # 'args': (16, 16)          # Arguments to pass to the task function
    },

    # Gate Fetches - 1. Typical, 2. Recurrent, 3. Clear Historical
    'gateFetch-typical-every-2-hours-daytime': {
        'task': 'routes.celery_app.GateFetch',
        # 'schedule': crontab(minute=35, hour='3'),     # test
        'schedule': crontab(minute=0, hour='0,8-23/2'),  # Run at 00z and, 08-23z every 2 hours.
    },
    'gateRecurrentUpdater-every-4mins-daytime': {
        'task': 'routes.celery_app.GateRecurrentUpdater',
        # 'schedule': crontab(minute=35, hour='3'),     # test
        'schedule': crontab(minute='2-58/4', hour='0-3,8-23'),  # Run every 4 minutes 2 past to 58 past and between 800-2300z
    },
    'gateClear-eveyr-5-hours-daytime': {
        'task': 'routes.celery_app.GateClear',
        # 'schedule': crontab(minute=45, hour='3'),     # test
        'schedule': crontab(minute=5, hour='0,8-23/5'),  # Run 10 mins past the hour every 5 hours from 08:00 to 21:00 UTC
    },

    # TODO cache: Cache this NAS for display on frontend instead of active NAS api fetch to reduce load and latency.
    'NAS-everyminute': {
        'task': 'routes.celery_app.nasFetch',
        # 'schedule': crontab(minute='*'),  # Test run every minute
        'schedule': crontab(minute='*'),  # Runs every minute
    },

    'generic-testing': {
        'task': 'routes.celery_app.generic_testing',
        'schedule': crontab(minute='59', hour='*/3')        # Run every 3 hours at 59 minutes past the hour
    },

    # uncomment the following if you need a function to run every x seconds. Change the task to its desired function.
    # 'func_run_frequently': {
    #     'task': 'routes.celery_app.DatisFetch',
    #     'schedule': 30,  # Every x seconds
    #     # 'args': (16, 16)          # Arguments to pass to the task function
    # },
}



# Import the tasks so they're registered with the app
# celery_app.autodiscover_tasks(['cel_trial'])
