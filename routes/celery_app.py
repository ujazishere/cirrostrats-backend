import asyncio
from celery import Celery
from celery.schedules import crontab
from routes.root.weather_fetch import Weather_fetch  # Used for periodic scheduling
from routes.root.gate_processor import Gate_processor
import datetime as dt

'''     ***CAUTION***
    Celery doesnt work with async directly so avoid using asyncio directly on celery_app.task function.
    instead use asyncio.run(async_function()) and this async_function() can be any async function you want to schedule. check example below for asyncio.run()
'''

celery_app = Celery(
    'tasks',
    broker='redis://redis:6379/0',
    backend='redis://redis:6379/0'
)

# TODO LP: Do I need this since I already have it in the Celery args.
# celery_app.conf.broker_url = 'redis://redis:6379/0'

utc_now = dt.datetime.now(dt.UTC)
zulutime = utc_now.strftime("%d %H:%M")

@celery_app.task
def DatisFetch():
    # Read caution note for explanation on asyncio use here.
    asyncio.run(run_datis_fetch())           # run_datis_fetch() is an async function. DatisFetch() is a celery task that cannot be an async function.

async def run_datis_fetch():    
    Wf = Weather_fetch()
    await Wf.bulk_fetch_and_store_by_type(weather_type='datis')
    return f'Celery task completed for fetching datis. timestamp - {zulutime}'


@celery_app.task
def MetarFetch():
    asyncio.run(run_metar_fetch_async_function())          # run_metar_fetch() is an async function. MetarFetch() is a celery task that cannot be an async function.

async def run_metar_fetch_async_function():
    Wf = Weather_fetch()
    await Wf.bulk_fetch_and_store_by_type(weather_type='metar')
    return f'Celery task completed for fetching metar. timestamp - {zulutime}'


@celery_app.task
def TAFFetch():
    asyncio.run(run_TAF_fetch())

async def run_TAF_fetch():    
    Wf = Weather_fetch()
    await Wf.bulk_fetch_and_store_by_type(weather_type='taf')
    return f'Celery task completed for fetching TAF. timestamp - {zulutime}'

# Gate fetchers
@celery_app.task
def GateFetch():
    gp = Gate_processor()
    gp.scrape_and_store()
    return f'Celery task completed for fetching gates. timestamp - {zulutime}'
@celery_app.task
def GateRecurrentUpdater():
    gp = Gate_processor()
    gp.recurrent_updater()
    return f'Celery task completed for recurrent gate update. timestamp - {zulutime}'
@celery_app.task
def GateClear():
    gp = Gate_processor()
    gp.mdb_clear_historical(hours=30)
    return f'Celery task completed for clearing historical gate data older than 30 hours. timestamp - {zulutime}'

celery_app.conf.timezone = 'UTC'  # Adjust to UTC timezone.

# TODO VHP: There have been times when the task is not running - celery-beat inadvertently shutsoff...
        # Retries should be made for unsuccessful tasks - consistent outlaws should be flagged and trashed to save processing power.
            # Design tests to consistently check output of the task...
            # Something that resembles a supervisor or a watchdog that checks for data validation.

# Add periodic task scheduling
celery_app.conf.beat_schedule = {
    # TODO Test: Check if this works and fetches the weather data, when it doesn't fetch the weather data it should log or retry every min or so increasing every iteration and stop when it becomes available.
                # once stopped return to original schedule of 53 past. 
                # If data unavailable for extended period then stop fetching completely and return to original schedule, notify about issue after 3 hours of inactive fetch.
                # -- This maybe too complicated and may require constant mx--> Maybe decrease variables and loose endpoints to reduce complexity.
                # What is important? weather should exist and should be accurate. If its not send notification at a threshold and continue fetch.
                #  Only attend to it when critical failure occurs.
    'run-datisfetch-every-53-mins-past-hour': {
        'task': 'routes.celery_app.DatisFetch',      # The task function that needs to be scheduled
        'schedule': crontab(minute=53),  # frequency of the task. In this case every 53 mins past the hour.
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

    # TODO VHP: Need a mechanism to check if the task is running or not and if not then spin up an instance to run it or check validity of data.
    # Gate Fetches - 1. Typical, 2. Recurrent, 3. Clear Historical
    'gateFetch-typical-every-2-hours-daytime': {
        'task': 'routes.celery_app.GateFetch',
        # 'schedule': crontab(minute=35, hour='3'),     # test
        'schedule': crontab(minute=0, hour='0,8-23/2'),  # Run at 00z and, 08-23z every 2 hours.
    },
    'gateRecurrentUpdater-every-4mins-daytime': {
        'task': 'routes.celery_app.GateRecurrentUpdater',
        # 'schedule': crontab(minute=35, hour='3'),     # test
        'schedule': crontab(minute='2-58/4', hour='0,1,8-23'),  # Run every 4 minutes 2 past to 58 past and between 800-2300z
    },
    'gateClear-eveyr-5-hours-daytime': {
        'task': 'routes.celery_app.GateClear',
        # 'schedule': crontab(minute=45, hour='3'),     # test
        'schedule': crontab(minute=5, hour='0,8-23/5'),  # Run 10 mins past the hour every 5 hours from 08:00 to 21:00 UTC
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
