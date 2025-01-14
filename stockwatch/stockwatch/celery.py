from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stockwatch.settings')

app = Celery('stockwatch')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django android configs.
app.autodiscover_tasks()

# Optional configuration, see the application user guide.
# You can add any Celery configuration settings here if needed.

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
