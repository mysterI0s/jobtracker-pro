# apps/jobs/tasks.py
import subprocess
import os
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from apps.companies.models import JobSource
from apps.jobs.models import Job
import logging

logger = logging.getLogger(__name__)


@shared_task
def scrape_jobs_from_source(source_name, max_jobs=50):
    """Scrape jobs from a specific source"""
    try:
        # Get the job source
        source = JobSource.objects.get(name=source_name, is_active=True)
        
        logger.info(f"Starting scrape for {source_name}")
        
        # Map source names to spider names
        spider_mapping = {
            'WeWorkRemotely': 'weworkremotely',
            'RemoteOK': 'remoteok',
            'AngelList': 'angellist',
        }
        
        spider_name = spider_mapping.get(source_name)
        if not spider_name:
            logger.error(f"No spider found for source: {source_name}")
            return {"error": f"No spider found for {source_name}"}
        
        # Build scrapy command
        scrapy_dir = os.path.join(os.getcwd(), 'scrapers', 'jobscraper')
        cmd = [
            'scrapy', 'crawl', spider_name,
            '-s', f'JOBTRACKER_MAX_JOBS_PER_RUN={max_jobs}',
            '-L', 'INFO'
        ]
        
        # Run scrapy in subprocess
        result = subprocess.run(
            cmd,
            cwd=scrapy_dir,
            capture_output=True,
            text=True,
            timeout=1800  # 30 minute timeout
        )
        
        if result.returncode == 0:
            # Update source last_scraped timestamp
            source.mark_as_scraped()
            
            logger.info(f"Successfully scraped {source_name}")
            return {
                "success": True,
                "source": source_name,
                "stdout": result.stdout[-500:],  # Last 500 chars
                "scraped_at": timezone.now().isoformat()
            }
        else:
            logger.error(f"Scraping failed for {source_name}: {result.stderr}")
            return {
                "success": False,
                "source": source_name,
                "error": result.stderr[-500:]  # Last 500 chars
            }
            
    except JobSource.DoesNotExist:
        error_msg = f"Job source '{source_name}' not found or inactive"
        logger.error(error_msg)
        return {"error": error_msg}
    
    except subprocess.TimeoutExpired:
        error_msg = f"Scraping timeout for {source_name}"
        logger.error(error_msg)
        return {"error": error_msg}
    
    except Exception as e:
        error_msg = f"Unexpected error scraping {source_name}: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}


@shared_task
def scrape_all_sources():
    """Scrape all active job sources"""
    results = []
    
    active_sources = JobSource.objects.filter(is_active=True)
    logger.info(f"Starting scrape for {active_sources.count()} sources")
    
    for source in active_sources:
        # Check if enough time has passed since last scrape
        if source.last_scraped:
            time_since_last_scrape = timezone.now() - source.last_scraped
            if time_since_last_scrape.seconds < source.scrape_interval:
                logger.info(f"Skipping {source.name} - too soon since last scrape")
                continue
        
        # Run scraping task
        result = scrape_jobs_from_source.delay(source.name)
        results.append({
            "source": source.name,
            "task_id": result.id
        })
    
    return {
        "message": f"Started scraping for {len(results)} sources",
        "tasks": results
    }


@shared_task
def cleanup_old_jobs(days_old=30):
    """Clean up old inactive jobs"""
    cutoff_date = timezone.now() - timedelta(days=days_old)
    
    # Mark old jobs as inactive
    old_jobs = Job.objects.filter(
        posted_date__lt=cutoff_date,
        is_active=True
    )
    
    count = old_jobs.count()
    old_jobs.update(is_active=False)
    
    logger.info(f"Marked {count} old jobs as inactive")
    
    return {
        "cleaned_jobs": count,
        "cutoff_date": cutoff_date.isoformat()
    }


@shared_task
def update_job_source_stats():
    """Update statistics for job sources"""
    sources_updated = 0
    
    for source in JobSource.objects.all():
        total_jobs = Job.objects.filter(source=source).count()
        active_jobs = Job.objects.filter(source=source, is_active=True).count()
        
        # Update if different
        if source.total_jobs_scraped != total_jobs:
            source.total_jobs_scraped = total_jobs
            source.save(update_fields=['total_jobs_scraped'])
            sources_updated += 1
    
    logger.info(f"Updated stats for {sources_updated} job sources")
    
    return {
        "sources_updated": sources_updated,
        "total_sources": JobSource.objects.count()
    }


@shared_task
def test_scraping_setup():
    """Test task to verify Celery is working"""
    logger.info("Testing scraping setup...")
    
    # Check if job sources exist
    sources_count = JobSource.objects.filter(is_active=True).count()
    
    # Check if scrapy is available
    scrapy_available = True
    try:
        result = subprocess.run(['scrapy', '--version'], capture_output=True, text=True)
        scrapy_version = result.stdout.strip() if result.returncode == 0 else "Not available"
    except FileNotFoundError:
        scrapy_available = False
        scrapy_version = "Not installed"
    
    return {
        "celery_working": True,
        "active_sources": sources_count,
        "scrapy_available": scrapy_available,
        "scrapy_version": scrapy_version,
        "timestamp": timezone.now().isoformat()
    }