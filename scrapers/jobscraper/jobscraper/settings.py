import os
import sys
import django

# Ensure the Django project root is on PYTHONPATH so 'jobtracker' is importable
current_dir = os.path.dirname(os.path.abspath(__file__))  # .../scrapers/jobscraper/jobscraper
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))  # go up to repo root
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure Django settings and initialize Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobtracker.settings')
django.setup()

# Scrapy settings for jobscraper project
BOT_NAME = 'jobscraper'

SPIDER_MODULES = ['jobscraper.spiders']
NEWSPIDER_MODULE = 'jobscraper.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure pipelines
ITEM_PIPELINES = {
    'jobscraper.pipelines.DuplicatesPipeline': 200,
    'jobscraper.pipelines.ValidationPipeline': 300,
    'jobscraper.pipelines.DjangoWriterPipeline': 800,
}

# Configure delays to be respectful
DOWNLOAD_DELAY = 2
RANDOMIZE_DOWNLOAD_DELAY = 0.5
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8

# User agent
USER_AGENT = 'jobscraper (+http://www.yourdomain.com)'

# AutoThrottle settings
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0

# Logging
LOG_LEVEL = 'INFO'
# Write Scrapy logs to the project's logs directory
LOG_FILE = os.path.join(project_root, 'logs', 'scrapy.log')

# Custom settings
JOBTRACKER_DUPLICATE_FILTER = True
JOBTRACKER_MAX_JOBS_PER_RUN = 100