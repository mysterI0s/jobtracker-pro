from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Job(models.Model):
    """Model representing a job posting"""
    
    JOB_TYPES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('freelance', 'Freelance'),
        ('internship', 'Internship'),
        ('temporary', 'Temporary'),
    ]
    
    EXPERIENCE_LEVELS = [
        ('entry', 'Entry Level'),
        ('junior', 'Junior'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior'),
        ('lead', 'Lead'),
        ('principal', 'Principal'),
        ('director', 'Director'),
    ]
    
    # Basic job information
    title = models.CharField(max_length=255)
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='jobs'
    )
    source = models.ForeignKey(
        'companies.JobSource',
        on_delete=models.CASCADE,
        related_name='jobs'
    )
    external_id = models.CharField(
        max_length=255,
        help_text="Job ID from the source website"
    )
    url = models.URLField()
    
    # Job details
    description = models.TextField()
    requirements = models.TextField(blank=True)
    benefits = models.TextField(blank=True)
    
    # Location and remote work
    location = models.CharField(max_length=255, blank=True)
    is_remote = models.BooleanField(default=False)
    remote_type = models.CharField(
        max_length=20,
        choices=[
            ('fully_remote', 'Fully Remote'),
            ('hybrid', 'Hybrid'),
            ('on_site', 'On-site'),
        ],
        default='on_site'
    )
    
    # Employment details
    job_type = models.CharField(max_length=20, choices=JOB_TYPES, default='full_time')
    experience_level = models.CharField(
        max_length=20,
        choices=EXPERIENCE_LEVELS,
        blank=True
    )
    
    # Salary information
    salary_min = models.PositiveIntegerField(blank=True, null=True)
    salary_max = models.PositiveIntegerField(blank=True, null=True)
    salary_currency = models.CharField(max_length=3, default='USD')
    salary_period = models.CharField(
        max_length=20,
        choices=[
            ('hourly', 'Hourly'),
            ('daily', 'Daily'),
            ('monthly', 'Monthly'),
            ('yearly', 'Yearly'),
        ],
        default='yearly'
    )
    
    # Dates and status
    posted_date = models.DateTimeField()
    scraped_date = models.DateTimeField(auto_now_add=True)
    expires_date = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    # Tags and categorization
    tags = models.JSONField(default=list, blank=True)
    skills_required = models.JSONField(default=list, blank=True)
    
    # User interaction tracking
    bookmarked_by = models.ManyToManyField(
        User,
        through='JobBookmark',
        related_name='bookmarked_jobs',
        blank=True
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-posted_date']
        unique_together = ['source', 'external_id']
        indexes = [
            models.Index(fields=['company']),
            models.Index(fields=['source']),
            models.Index(fields=['posted_date']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_remote']),
            models.Index(fields=['job_type']),
        ]
    
    def __str__(self):
        return f"{self.title} at {self.company.name}"
    
    @property
    def salary_display(self):
        """Human readable salary range"""
        if not self.salary_min and not self.salary_max:
            return "Not specified"
        
        currency_symbol = {'USD': '$', 'EUR': '€', 'GBP': '£'}.get(self.salary_currency, self.salary_currency)
        
        if self.salary_min and self.salary_max:
            return f"{currency_symbol}{self.salary_min:,} - {currency_symbol}{self.salary_max:,}"
        elif self.salary_min:
            return f"From {currency_symbol}{self.salary_min:,}"
        else:
            return f"Up to {currency_symbol}{self.salary_max:,}"
    
    @property
    def age_in_days(self):
        """Calculate how many days since job was posted"""
        return (timezone.now() - self.posted_date).days
    
    def is_recently_posted(self, days=7):
        """Check if job was posted within specified days"""
        return self.age_in_days <= days


class JobBookmark(models.Model):
    """Through model for job bookmarks with additional data"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'job']
    
    def __str__(self):
        return f"{self.user.username} bookmarked {self.job.title}"