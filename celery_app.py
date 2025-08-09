import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobtracker.settings')

# Create Celery app
app = Celery('jobtracker')

# Configure Celery using settings from Django settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load tasks from all registered Django apps
app.autodiscover_tasks()

# Optional: Add periodic tasks
from celery.schedules import crontab

app.conf.beat_schedule = {
    'scrape-jobs-every-hour': {
        'task': 'apps.jobs.tasks.scrape_all_sources',
        'schedule': crontab(minute=0),  # Run every hour
    },
    'cleanup-old-jobs-daily': {
        'task': 'apps.jobs.tasks.cleanup_old_jobs',
        'schedule': crontab(hour=2, minute=0),  # Run at 2 AM daily
    },
}

app.conf.timezone = 'UTC'