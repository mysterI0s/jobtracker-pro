import scrapy
from scrapy_djangoitem import DjangoItem
from apps.jobs.models import Job


class JobItem(DjangoItem):
    """Django item for Job model"""
    django_model = Job
    
    # Additional fields not in the model but useful for processing
    raw_salary = scrapy.Field()
    raw_location = scrapy.Field()
    raw_description = scrapy.Field()
    source_name = scrapy.Field()
    company_name = scrapy.Field()


class CompanyItem(scrapy.Field):
    """Simple item for company data"""
    name = scrapy.Field()
    website = scrapy.Field()
    industry = scrapy.Field()
    size = scrapy.Field()
    description = scrapy.Field()
    logo_url = scrapy.Field()