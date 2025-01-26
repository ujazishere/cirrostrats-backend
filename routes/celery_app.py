import asyncio
from celery import Celery
from celery.schedules import crontab
from routes.root.weather_fetch import Weather_fetch  # Used for periodic scheduling
from routes.root.gate_scrape import Gate_Scrape
import datetime as dt

'''     ***CAUTION***
    Celery doesnt work with async directly so avoid using asyncio directly on celery_app.task function.
    instead use asyncio.run(async_function()) and this async_function() can be an async function. check example below for asyncio.run()
'''

celery_app = Celery(
    'tasks',
    broker='redis://redis:6379/0',
    backend='redis://redis:6379/0'
)

# celery_app.conf.broker_url = 'redis://redis:6379/0'     # TODO: Do I need this since I already have it in the Celery args.

@celery_app.task
def MetarFetch():
    asyncio.run(run_metar_fetch_async_function())          # run_metar_fetch() is an async function. MetarFetch() is a celery task that cannot be an async function.

async def run_metar_fetch_async_function():
    # yyyymmddhhmm = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d%H%M")
    Wf = Weather_fetch()
    await Wf.fetch_and_store_by_type(weather_type='metar')

    return 'Celery task completed for fetching metar'


@celery_app.task
def DatisFetch():
    asyncio.run(run_datis_fetch())

async def run_datis_fetch():    
    # yyyymmddhhmm = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d%H%M")
    Wf = Weather_fetch()
    await Wf.fetch_and_store_by_type(weather_type='datis')


@celery_app.task
def TAFFetch():
    asyncio.run(run_TAF_fetch())

async def run_TAF_fetch():    
    # yyyymmddhhmm = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d%H%M")
    Wf = Weather_fetch()
    await Wf.fetch_and_store_by_type(weather_type='taf')


@celery_app.task
def GateFetch():
    # yyyymmddhhmm = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d%H%M")
    gs = Gate_Scrape()
    gs.fetch_and_store()


celery_app.conf.timezone = 'UTC'  # Adjust to UTC timezone.


# Add periodic task scheduling
celery_app.conf.beat_schedule = {
    # TODO: Check if this works and fetches the weather data, when it doesn't fetch the weather data it should log or retry every minute or so.
    'run-metarfetch-every-53-mins-past-hour': {
        'task': 'routes.celery_app.MetarFetch',      # The task function that needs to be scheduled
        'schedule': crontab(minute=53),  # frequency of the task. In this case every 53 mins past the hour.
        # 'args': (16, 16)          # Arguments to pass to the task function
    },
    'run-datisfetch-every-53-mins-past-hour': {
        'task': 'routes.celery_app.DatisFetch',      # The task function that needs to be scheduled
        'schedule': crontab(minute=53),  # frequency of the task. In this case every 53 mins past the hour.
        # 'args': (16, 16)          # Arguments to pass to the task function
    },
    'run-TAFfetch-every-4-hours': {
        'task': 'routes.celery_app.TAFFetch',      # The task function that needs to be scheduled
        'schedule': crontab(minute=21, hour='5,11,17,23'),  # Run at 05:21, 11:21, 17:21, and 23:21 UTC
        # 'args': (16, 16)          # Arguments to pass to the task function
    },
    'gatefetch-func_run_frequently': {
        'task': 'routes.celery_app.GateFetch',
        'schedule': 1800,  # Every x seconds
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
