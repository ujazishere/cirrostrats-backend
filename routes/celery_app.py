from celery import Celery
from celery.schedules import crontab
# from routes.root.weather_fetch import Weather_fetch  # Used for periodic scheduling

import os
print(os.getcwd(), 'DIR->>',os.listdir())

celery_app = Celery(
    'tasks',
    broker='redis://redis:6379/0',
    backend='redis://redis:6379/0'
)

# celery_app.conf.broker_url = 'redis://redis:6379/0'     # TODO: Do I need this since I already have it in the Celery args.

@celery_app.task
def MetarFetch():

    print('Testing MetarFetch empty function')      # TODO: If this works then uncomment the below lines.
    # Wf = Weather_fetch()
    # print('Starting METAR fetch')
    # await Wf.fetch_and_store_metar()
    # print("finished fetching")
    # return None

@celery_app.task
def DatisFetch():

    print('Testing DATIS fetch empty function')         # TODO: If this works then uncomment the below lines.

    # Wf = Weather_fetch()
    # print('Starting DATIS fetch')
    # await Wf.fetch_and_store_datis()
    # print("finished fetching")
    # return None

celery_app.conf.timezone = 'UTC'  # Adjust to UTC timezone.

# Add periodic task scheduling
celery_app.conf.beat_schedule = {
    'run-every-55-mins-past-hour': {
        'task': 'celery_app.MetarFetch',      # The task function that needs to be scheduled
        'schedule': crontab(minute=33),  # frequency of the task. In this case every 53 mins past the hour.
        # 'args': (16, 16)          # Arguments to pass to the task function
    },
    'func_run_frequently': {
        'task': 'celery_app.DatisFetch',
        'schedule': 20,  # Every x seconds
    },
}

# Import the tasks so they're registered with the app
# celery_app.autodiscover_tasks(['cel_trial'])
