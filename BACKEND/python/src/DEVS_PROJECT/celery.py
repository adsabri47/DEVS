import os
from celery import Celery

# Telling Celery which project settings to look at. 
# This links the background worker to our main DEVS_PROJECT configuration.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DEVS_PROJECT.settings')

# Initializing the Celery app instance. 
# This 'app' variable is the core manager for all our asynchronous tasks.
app = Celery('DEVS_PROJECT')

# We're telling Celery to pull its configuration directly from our Django settings.
# The 'CELERY' namespace means it will specifically look for variables 
# starting with 'CELERY_' (like CELERY_BROKER_URL).
app.config_from_object('django.conf:settings', namespace='CELERY')

# This is a 'set it and forget it' line. 
# It tells Celery to automatically scan all our installed apps (like 'evidence') 
# to find any functions inside a 'tasks.py' file.
app.autodiscover_tasks()