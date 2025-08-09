import os
import sys
import django

# Add the Django project to Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..'))

# Setup Django settings
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
LOG_FILE = '../logs/scrapy.log'

# Custom settings
JOBTRACKER_DUPLICATE_FILTER = True
JOBTRACKER_MAX_JOBS_PER_RUN = 100