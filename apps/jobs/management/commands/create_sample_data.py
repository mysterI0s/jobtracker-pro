# apps/jobs/management/commands/create_sample_data.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.companies.models import Company, JobSource
from apps.jobs.models import Job
from datetime import timedelta
import random


class Command(BaseCommand):
    help = 'Create sample data for testing'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--jobs',
            type=int,
            default=50,
            help='Number of sample jobs to create'
        )
    
    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create job sources
        sources = [
            {
                'name': 'WeWorkRemotely',
                'base_url': 'https://weworkremotely.com',
                'scrape_interval': 3600,
            },
            {
                'name': 'RemoteOK',
                'base_url': 'https://remoteok.io',
                'scrape_interval': 1800,
            },
            {
                'name': 'AngelList',
                'base_url': 'https://angel.co',
                'scrape_interval': 7200,
            },
        ]
        
        created_sources = []
        for source_data in sources:
            source, created = JobSource.objects.get_or_create(
                name=source_data['name'],
                defaults=source_data
            )
            created_sources.append(source)
            if created:
                self.stdout.write(f'Created source: {source.name}')
        
        # Create companies
        companies_data = [
            {'name': 'TechCorp Inc', 'industry': 'Technology', 'size': 'large'},
            {'name': 'StartupXYZ', 'industry': 'Fintech', 'size': 'startup'},
            {'name': 'DataSolutions LLC', 'industry': 'Analytics', 'size': 'medium'},
            {'name': 'CloudFirst Co', 'industry': 'Cloud Services', 'size': 'medium'},
            {'name': 'AI Innovations', 'industry': 'Artificial Intelligence', 'size': 'small'},
            {'name': 'CyberSecure Ltd', 'industry': 'Cybersecurity', 'size': 'large'},
            {'name': 'GreenTech Energy', 'industry': 'Clean Energy', 'size': 'medium'},
            {'name': 'HealthTech Plus', 'industry': 'Healthcare Technology', 'size': 'startup'},
            {'name': 'EduPlatform', 'industry': 'EdTech', 'size': 'small'},
            {'name': 'RetailGenius', 'industry': 'E-commerce', 'size': 'enterprise'},
        ]
        
        created_companies = []
        for company_data in companies_data:
            company, created = Company.objects.get_or_create(
                name=company_data['name'],
                defaults=company_data
            )
            created_companies.append(company)
            if created:
                self.stdout.write(f'Created company: {company.name}')
        
        # Create sample jobs
        job_titles = [
            'Senior Python Developer',
            'Full Stack Engineer',
            'DevOps Engineer',
            'Data Scientist',
            'Product Manager',
            'UX/UI Designer',
            'Machine Learning Engineer',
            'Backend Developer',
            'Frontend Developer',
            'Site Reliability Engineer',
            'Security Analyst',
            'Mobile App Developer',
            'Cloud Architect',
            'QA Engineer',
            'Technical Writer',
        ]
        
        locations = [
            'San Francisco, CA', 'New York, NY', 'Austin, TX', 'Seattle, WA',
            'Remote - US', 'Remote - Worldwide', 'London, UK', 'Berlin, Germany',
            'Toronto, Canada', 'Sydney, Australia'
        ]
        
        job_types = ['full_time', 'contract', 'part_time']
        experience_levels = ['junior', 'mid', 'senior', 'lead']
        
        jobs_created = 0
        for i in range(options['jobs']):
            # Random job data
            title = random.choice(job_titles)
            company = random.choice(created_companies)
            source = random.choice(created_sources)
            location = random.choice(locations)
            is_remote = 'Remote' in location or random.choice([True, False])
            
            # Generate salary range
            base_salary = random.randint(60, 200) * 1000
            salary_min = base_salary
            salary_max = base_salary + random.randint(10, 50) * 1000
            
            # Random posting date (last 30 days)
            days_ago = random.randint(0, 30)
            posted_date = timezone.now() - timedelta(days=days_ago)
            
            job_data = {
                'title': title,
                'company': company,
                'source': source,
                'external_id': f'job_{i}_{source.name.lower()}',
                'url': f'{source.base_url}/jobs/{i}',
                'description': self.generate_job_description(),
                'requirements': self.generate_requirements(),
                'location': location,
                'is_remote': is_remote,
                'remote_type': 'fully_remote' if is_remote else 'on_site',
                'job_type': random.choice(job_types),
                'experience_level': random.choice(experience_levels),
                'salary_min': salary_min,
                'salary_max': salary_max,
                'posted_date': posted_date,
                'tags': random.sample(['python', 'django', 'react', 'aws', 'docker', 'kubernetes'], k=3),
                'skills_required': random.sample(['Python', 'JavaScript', 'SQL', 'Git', 'AWS'], k=3),
            }
            
            job, created = Job.objects.get_or_create(
                source=source,
                external_id=job_data['external_id'],
                defaults=job_data
            )
            
            if created:
                jobs_created += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {jobs_created} sample jobs!')
        )
    
    def generate_job_description(self):
        descriptions = [
            "We are looking for a talented developer to join our growing team. You will work on exciting projects using modern technologies.",
            "Join our innovative company and help build the next generation of products. Great opportunity for growth and learning.",
            "We're seeking a passionate professional to contribute to our mission of making technology accessible to everyone.",
            "Exciting opportunity to work with cutting-edge technology and a collaborative team environment.",
        ]
        return random.choice(descriptions)
    
    def generate_requirements(self):
        requirements = [
            "• 3+ years of experience\n• Strong problem-solving skills\n• Team collaboration experience",
            "• Bachelor's degree or equivalent\n• Experience with modern frameworks\n• Excellent communication skills",
            "• Proven track record in similar role\n• Knowledge of best practices\n• Passion for continuous learning",
        ]
        return random.choice(requirements)