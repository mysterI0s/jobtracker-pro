import re
import logging
from django.utils import timezone
from django.utils.text import slugify
from apps.jobs.models import Job
from apps.companies.models import Company, JobSource
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem


logger = logging.getLogger(__name__)


class DuplicatesPipeline:
    """Remove duplicate job items"""
    
    def __init__(self):
        self.seen_jobs = set()
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Create unique identifier
        identifier = f"{adapter.get('source_name')}-{adapter.get('external_id')}"
        
        if identifier in self.seen_jobs:
            logger.info(f"Duplicate job found: {identifier}")
            raise DropItem(f"Duplicate item found: {identifier}")
        else:
            self.seen_jobs.add(identifier)
            return item


class ValidationPipeline:
    """Validate and clean job data"""
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Required fields validation
        required_fields = ['title', 'company_name', 'external_id', 'url']
        for field in required_fields:
            if not adapter.get(field):
                raise DropItem(f"Missing required field: {field}")
        
        # Clean and validate title
        title = adapter.get('title', '').strip()
        if len(title) < 5:
            raise DropItem(f"Job title too short: {title}")
        adapter['title'] = title[:255]  # Ensure it fits in database
        
        # Process salary information
        self._process_salary(adapter)
        
        # Process location
        self._process_location(adapter)
        
        # Process description
        self._process_description(adapter)
        
        # Set default values
        if not adapter.get('posted_date'):
            adapter['posted_date'] = timezone.now()
        
        if not adapter.get('job_type'):
            adapter['job_type'] = 'full_time'
        
        return item
    
    def _process_salary(self, adapter):
        """Extract and clean salary information"""
        raw_salary = adapter.get('raw_salary', '')
        
        if not raw_salary:
            return
        
        # Simple salary extraction (can be made more sophisticated)
        salary_pattern = r'[\$£€]?([\d,]+)(?:\s*-\s*[\$£€]?([\d,]+))?'
        match = re.search(salary_pattern, raw_salary.replace(',', ''))
        
        if match:
            min_salary = int(match.group(1).replace(',', '')) if match.group(1) else None
            max_salary = int(match.group(2).replace(',', '')) if match.group(2) else None
            
            if min_salary:
                adapter['salary_min'] = min_salary
            if max_salary:
                adapter['salary_max'] = max_salary
            
            # Detect currency
            if '$' in raw_salary:
                adapter['salary_currency'] = 'USD'
            elif '£' in raw_salary:
                adapter['salary_currency'] = 'GBP'
            elif '€' in raw_salary:
                adapter['salary_currency'] = 'EUR'
    
    def _process_location(self, adapter):
        """Clean and standardize location"""
        raw_location = adapter.get('raw_location', '').strip()
        
        if not raw_location:
            adapter['location'] = ''
            return
        
        # Check for remote indicators
        remote_keywords = ['remote', 'anywhere', 'work from home', 'wfh', 'distributed']
        is_remote = any(keyword in raw_location.lower() for keyword in remote_keywords)
        
        adapter['is_remote'] = is_remote
        adapter['location'] = raw_location[:255]
        
        if is_remote:
            adapter['remote_type'] = 'fully_remote'
        else:
            adapter['remote_type'] = 'on_site'
    
    def _process_description(self, adapter):
        """Clean job description"""
        description = adapter.get('raw_description', '').strip()
        
        if description:
            # Remove excessive whitespace and HTML tags
            description = re.sub(r'\s+', ' ', description)
            description = re.sub(r'<[^>]+>', '', description)  # Basic HTML removal
            adapter['description'] = description
        else:
            adapter['description'] = 'No description provided.'


class DjangoWriterPipeline:
    """Save items to Django database"""
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        try:
            # Get or create company
            company = self._get_or_create_company(adapter)
            
            # Get job source
            source = self._get_job_source(adapter.get('source_name'))
            
            # Create or update job
            job = self._create_or_update_job(adapter, company, source)
            
            logger.info(f"Successfully processed job: {job.title} at {company.name}")
            return item
            
        except Exception as e:
            logger.error(f"Error saving job to database: {str(e)}")
            raise DropItem(f"Error saving job: {str(e)}")
    
    def _get_or_create_company(self, adapter):
        """Get or create company from job data"""
        company_name = adapter.get('company_name').strip()
        
        # Try to find existing company (case-insensitive)
        try:
            company = Company.objects.get(name__iexact=company_name)
        except Company.DoesNotExist:
            # Create new company
            company = Company.objects.create(
                name=company_name,
                slug=slugify(company_name),
                # Add more fields if available in the scraped data
                website=adapter.get('company_website', ''),
                description=adapter.get('company_description', ''),
                industry=adapter.get('company_industry', ''),
                size=adapter.get('company_size', 'unknown'),
            )
            logger.info(f"Created new company: {company.name}")
        
        return company
    
    def _get_job_source(self, source_name):
        """Get job source by name"""
        try:
            return JobSource.objects.get(name=source_name)
        except JobSource.DoesNotExist:
            logger.error(f"Job source '{source_name}' not found in database")
            raise DropItem(f"Unknown job source: {source_name}")
    
    def _create_or_update_job(self, adapter, company, source):
        """Create or update job in database"""
        external_id = adapter.get('external_id')
        
        # Check if job already exists
        try:
            job = Job.objects.get(source=source, external_id=external_id)
            # Update existing job
            self._update_job_fields(job, adapter, company)
            job.save()
            logger.info(f"Updated existing job: {job.id}")
        except Job.DoesNotExist:
            # Create new job
            job = Job(
                company=company,
                source=source,
                external_id=external_id,
            )
            self._update_job_fields(job, adapter, company)
            job.save()
            
            # Update source statistics
            source.increment_jobs_count()
            logger.info(f"Created new job: {job.id}")
        
        return job
    
    def _update_job_fields(self, job, adapter, company):
        """Update job fields from adapter data"""
        job.title = adapter.get('title')
        job.company = company
        job.url = adapter.get('url')
        job.description = adapter.get('description', '')
        job.requirements = adapter.get('requirements', '')
        job.benefits = adapter.get('benefits', '')
        job.location = adapter.get('location', '')
        job.is_remote = adapter.get('is_remote', False)
        job.remote_type = adapter.get('remote_type', 'on_site')
        job.job_type = adapter.get('job_type', 'full_time')
        job.experience_level = adapter.get('experience_level', '')
        job.salary_min = adapter.get('salary_min')
        job.salary_max = adapter.get('salary_max')
        job.salary_currency = adapter.get('salary_currency', 'USD')
        job.posted_date = adapter.get('posted_date', timezone.now())
        job.tags = adapter.get('tags', [])
        job.skills_required = adapter.get('skills_required', [])
        job.is_active = True