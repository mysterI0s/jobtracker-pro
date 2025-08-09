from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserProfile(models.Model):
    """Extended user profile for job tracking preferences"""
    
    CAREER_LEVELS = [
        ('entry', 'Entry Level (0-2 years)'),
        ('junior', 'Junior (2-4 years)'),
        ('mid', 'Mid Level (4-7 years)'),
        ('senior', 'Senior (7-10 years)'),
        ('lead', 'Lead (10+ years)'),
        ('principal', 'Principal/Staff (12+ years)'),
        ('director', 'Director/VP (15+ years)'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Professional information
    current_title = models.CharField(max_length=255, blank=True)
    career_level = models.CharField(max_length=20, choices=CAREER_LEVELS, blank=True)
    years_of_experience = models.PositiveIntegerField(blank=True, null=True)
    
    # Contact and location
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=255, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Professional links
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    website_url = models.URLField(blank=True)
    
    # Job search preferences
    desired_salary_min = models.PositiveIntegerField(blank=True, null=True)
    desired_salary_max = models.PositiveIntegerField(blank=True, null=True)
    salary_currency = models.CharField(max_length=3, default='USD')
    
    preferred_job_types = models.JSONField(
        default=list,
        help_text="List of preferred job types: full_time, part_time, contract, etc."
    )
    preferred_remote_type = models.CharField(
        max_length=20,
        choices=[
            ('fully_remote', 'Fully Remote Only'),
            ('hybrid', 'Hybrid/Flexible'),
            ('on_site', 'On-site Only'),
            ('any', 'Any'),
        ],
        default='any'
    )
    willing_to_relocate = models.BooleanField(default=False)
    preferred_locations = models.JSONField(
        default=list,
        help_text="List of preferred work locations"
    )
    
    # Skills and interests
    skills = models.JSONField(
        default=list,
        help_text="List of technical skills"
    )
    industries_of_interest = models.JSONField(
        default=list,
        help_text="Industries the user is interested in"
    )
    company_sizes_preferred = models.JSONField(
        default=list,
        help_text="Preferred company sizes: startup, small, medium, large, enterprise"
    )
    
    # Job search settings
    is_actively_searching = models.BooleanField(default=True)
    is_open_to_opportunities = models.BooleanField(default=False)
    job_search_status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Actively Searching'),
            ('passive', 'Open to Opportunities'),
            ('not_looking', 'Not Looking'),
            ('employed', 'Recently Employed'),
        ],
        default='active'
    )
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    daily_job_digest = models.BooleanField(default=False)
    weekly_summary = models.BooleanField(default=True)
    application_reminders = models.BooleanField(default=True)
    
    # Resume and documents
    current_resume = models.FileField(
        upload_to='resumes/%Y/%m/',
        blank=True,
        null=True
    )
    resume_updated_at = models.DateTimeField(blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}".strip()
    
    @property
    def display_name(self):
        return self.full_name if self.full_name else self.user.username
    
    def get_salary_range_display(self):
        """Human readable salary expectation"""
        if not self.desired_salary_min and not self.desired_salary_max:
            return "Not specified"
        
        currency_symbol = {'USD': '$', 'EUR': '€', 'GBP': '£'}.get(self.salary_currency, self.salary_currency)
        
        if self.desired_salary_min and self.desired_salary_max:
            return f"{currency_symbol}{self.desired_salary_min:,} - {currency_symbol}{self.desired_salary_max:,}"
        elif self.desired_salary_min:
            return f"From {currency_symbol}{self.desired_salary_min:,}"
        else:
            return f"Up to {currency_symbol}{self.desired_salary_max:,}"


class JobAlert(models.Model):
    """Model for saved job search alerts"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_alerts')
    name = models.CharField(max_length=255)
    
    # Search criteria
    keywords = models.CharField(max_length=500, blank=True)
    location = models.CharField(max_length=255, blank=True)
    job_types = models.JSONField(default=list)
    remote_only = models.BooleanField(default=False)
    salary_min = models.PositiveIntegerField(blank=True, null=True)
    company_sizes = models.JSONField(default=list)
    experience_levels = models.JSONField(default=list)
    
    # Alert settings
    is_active = models.BooleanField(default=True)
    email_frequency = models.CharField(
        max_length=20,
        choices=[
            ('immediate', 'Immediate'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('never', 'Never (Save Only)'),
        ],
        default='daily'
    )
    
    # Tracking
    last_sent = models.DateTimeField(blank=True, null=True)
    jobs_found_count = models.PositiveIntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"
    
    def matches_job(self, job):
        """Check if a job matches this alert criteria"""
        # Simple matching logic - can be enhanced later
        if self.keywords:
            keywords_list = [k.strip().lower() for k in self.keywords.split(',')]
            job_text = f"{job.title} {job.description}".lower()
            if not any(keyword in job_text for keyword in keywords_list):
                return False
        
        if self.location and self.location.lower() not in job.location.lower():
            return False
        
        if self.remote_only and not job.is_remote:
            return False
        
        if self.job_types and job.job_type not in self.job_types:
            return False
        
        if self.salary_min and job.salary_max and job.salary_max < self.salary_min:
            return False
        
        return True