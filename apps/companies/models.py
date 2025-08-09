from django.db import models
from django.utils import timezone


class Company(models.Model):
    """Model representing a company that posts jobs"""
    
    COMPANY_SIZES = [
        ('startup', '1-10 employees'),
        ('small', '11-50 employees'),
        ('medium', '51-200 employees'),
        ('large', '201-1000 employees'),
        ('enterprise', '1000+ employees'),
        ('unknown', 'Unknown'),
    ]
    
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    website = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True)
    industry = models.CharField(max_length=100, blank=True)
    size = models.CharField(max_length=20, choices=COMPANY_SIZES, default='unknown')
    logo_url = models.URLField(blank=True, null=True)
    headquarters = models.CharField(max_length=255, blank=True)
    founded_year = models.PositiveIntegerField(blank=True, null=True)
    
    # Social media links
    linkedin_url = models.URLField(blank=True, null=True)
    twitter_url = models.URLField(blank=True, null=True)
    github_url = models.URLField(blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = "Companies"
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class JobSource(models.Model):
    """Model representing different job board sources"""
    
    name = models.CharField(max_length=100, unique=True)
    base_url = models.URLField()
    is_active = models.BooleanField(default=True)
    scrape_interval = models.PositiveIntegerField(
        default=3600,
        help_text="Scraping interval in seconds"
    )
    last_scraped = models.DateTimeField(blank=True, null=True)
    total_jobs_scraped = models.PositiveIntegerField(default=0)
    
    # Scraping configuration
    rate_limit = models.PositiveIntegerField(
        default=1,
        help_text="Delay between requests in seconds"
    )
    user_agent = models.CharField(
        max_length=255,
        blank=True,
        help_text="Custom user agent for scraping"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def mark_as_scraped(self):
        """Update last_scraped timestamp"""
        self.last_scraped = timezone.now()
        self.save(update_fields=['last_scraped'])
    
    def increment_jobs_count(self, count=1):
        """Increment total jobs scraped counter"""
        self.total_jobs_scraped += count
        self.save(update_fields=['total_jobs_scraped'])