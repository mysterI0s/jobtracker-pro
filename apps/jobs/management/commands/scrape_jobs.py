# apps/jobs/management/commands/scrape_jobs.py
from django.core.management.base import BaseCommand
from apps.companies.models import JobSource
from apps.jobs.tasks import scrape_jobs_from_source, scrape_all_sources
from django.utils import timezone


class Command(BaseCommand):
    help = 'Scrape jobs from job sources'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            help='Specific source to scrape (WeWorkRemotely, RemoteOK, AngelList)'
        )
        parser.add_argument(
            '--max-jobs',
            type=int,
            default=20,
            help='Maximum number of jobs to scrape'
        )
        parser.add_argument(
            '--sync',
            action='store_true',
            help='Run synchronously instead of as Celery task'
        )
        parser.add_argument(
            '--list-sources',
            action='store_true',
            help='List all available job sources'
        )
    
    def handle(self, *args, **options):
        if options['list_sources']:
            self._list_sources()
            return
        
        if options['source']:
            self._scrape_single_source(options['source'], options['max_jobs'], options['sync'])
        else:
            self._scrape_all_sources(options['sync'])
    
    def _list_sources(self):
        """List all job sources"""
        sources = JobSource.objects.all().order_by('name')
        
        if not sources:
            self.stdout.write(self.style.WARNING('No job sources found. Run create_sample_data first.'))
            return
        
        self.stdout.write(self.style.SUCCESS('Available Job Sources:'))
        self.stdout.write('-' * 50)
        
        for source in sources:
            status = '✅ Active' if source.is_active else '❌ Inactive'
            last_scraped = source.last_scraped.strftime('%Y-%m-%d %H:%M') if source.last_scraped else 'Never'
            
            self.stdout.write(f"{source.name:<20} {status:<12} Jobs: {source.total_jobs_scraped:<5} Last: {last_scraped}")
    
    def _scrape_single_source(self, source_name, max_jobs, sync):
        """Scrape jobs from a single source"""
        try:
            source = JobSource.objects.get(name=source_name)
        except JobSource.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Source "{source_name}" not found. Use --list-sources to see available sources.')
            )
            return
        
        if not source.is_active:
            self.stdout.write(
                self.style.WARNING(f'Source "{source_name}" is inactive. Activate it in the admin panel.')
            )
            return
        
        self.stdout.write(f'Starting scrape for {source_name} (max {max_jobs} jobs)...')
        
        if sync:
            # Run directly (not recommended for production)
            from apps.jobs.tasks import scrape_jobs_from_source
            result = scrape_jobs_from_source(source_name, max_jobs)
            self._display_result(result)
        else:
            # Run as Celery task
            task = scrape_jobs_from_source.delay(source_name, max_jobs)
            self.stdout.write(f'Scraping task started with ID: {task.id}')
            self.stdout.write('Monitor progress in Celery worker logs or Django admin.')
    
    def _scrape_all_sources(self, sync):
        """Scrape jobs from all active sources"""
        active_sources = JobSource.objects.filter(is_active=True)
        
        if not active_sources:
            self.stdout.write(self.style.WARNING('No active job sources found.'))
            return
        
        self.stdout.write(f'Starting scrape for {active_sources.count()} active sources...')
        
        if sync:
            self.stdout.write(self.style.WARNING('Synchronous scraping of all sources not recommended. Use --source instead.'))
            return
        else:
            # Run as Celery task
            task = scrape_all_sources.delay()
            self.stdout.write(f'Scraping task started with ID: {task.id}')
            self.stdout.write('Monitor progress in Celery worker logs or Django admin.')
    
    def _display_result(self, result):
        """Display scraping result"""
        if result.get('success'):
            self.stdout.write(
                self.style.SUCCESS(f"✅ Successfully scraped {result['source']}")
            )
        else:
            self.stdout.write(
                self.style.ERROR(f"❌ Failed to scrape: {result.get('error', 'Unknown error')}")
            )