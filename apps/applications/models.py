from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Application(models.Model):
    """Model representing a job application"""
    
    STATUS_CHOICES = [
        ('interested', 'Interested'),
        ('applied', 'Applied'),
        ('screening', 'Phone/Video Screening'),
        ('interview', 'Interview'),
        ('technical', 'Technical Assessment'),
        ('final', 'Final Interview'),
        ('offer', 'Offer Received'),
        ('accepted', 'Offer Accepted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
        ('ghosted', 'No Response'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('dream', 'Dream Job'),
    ]
    
    # Core relationships
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    job = models.ForeignKey('jobs.Job', on_delete=models.CASCADE, related_name='applications')
    
    # Application status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='interested')
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    
    # Important dates
    applied_date = models.DateTimeField(blank=True, null=True)
    response_date = models.DateTimeField(blank=True, null=True)
    interview_date = models.DateTimeField(blank=True, null=True)
    follow_up_date = models.DateField(blank=True, null=True)
    
    # Application materials
    cover_letter = models.TextField(blank=True)
    resume_version = models.CharField(max_length=100, blank=True)
    portfolio_link = models.URLField(blank=True)
    
    # Contact information
    recruiter_name = models.CharField(max_length=255, blank=True)
    recruiter_email = models.EmailField(blank=True)
    hiring_manager_name = models.CharField(max_length=255, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    
    # Application tracking
    application_method = models.CharField(
        max_length=50,
        choices=[
            ('website', 'Company Website'),
            ('linkedin', 'LinkedIn'),
            ('email', 'Email'),
            ('referral', 'Referral'),
            ('job_board', 'Job Board'),
            ('recruiter', 'Recruiter'),
        ],
        default='website'
    )
    
    # Offer details (if applicable)
    salary_offered = models.PositiveIntegerField(blank=True, null=True)
    salary_currency = models.CharField(max_length=3, default='USD')
    benefits_offered = models.TextField(blank=True)
    start_date = models.DateField(blank=True, null=True)
    
    # Notes and feedback
    notes = models.TextField(
        blank=True,
        help_text="Personal notes about this application"
    )
    interview_feedback = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'job']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['applied_date']),
            models.Index(fields=['follow_up_date']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.job.title} at {self.job.company.name}"
    
    @property
    def days_since_applied(self):
        """Calculate days since application was submitted"""
        if not self.applied_date:
            return None
        return (timezone.now() - self.applied_date).days
    
    @property 
    def needs_follow_up(self):
        """Check if application needs follow up"""
        if not self.follow_up_date:
            return False
        return timezone.now().date() >= self.follow_up_date
    
    @property
    def is_active(self):
        """Check if application is still in progress"""
        inactive_statuses = ['accepted', 'rejected', 'withdrawn']
        return self.status not in inactive_statuses
    
    def mark_as_applied(self):
        """Update status to applied with timestamp"""
        self.status = 'applied'
        if not self.applied_date:
            self.applied_date = timezone.now()
        self.save(update_fields=['status', 'applied_date'])
    
    def set_follow_up_reminder(self, days=7):
        """Set follow up date X days from now"""
        self.follow_up_date = timezone.now().date() + timezone.timedelta(days=days)
        self.save(update_fields=['follow_up_date'])


class ApplicationDocument(models.Model):
    """Model for storing application-related documents"""
    
    DOCUMENT_TYPES = [
        ('resume', 'Resume'),
        ('cover_letter', 'Cover Letter'),
        ('portfolio', 'Portfolio'),
        ('transcript', 'Transcript'),
        ('certificate', 'Certificate'),
        ('other', 'Other'),
    ]
    
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to='application_documents/%Y/%m/')
    filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()  # in bytes
    description = models.CharField(max_length=255, blank=True)
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.get_document_type_display()} for {self.application}"
    
    def save(self, *args, **kwargs):
        if self.file and not self.filename:
            self.filename = self.file.name
        if self.file and not self.file_size:
            self.file_size = self.file.size
        super().save(*args, **kwargs)


class ApplicationNote(models.Model):
    """Model for timestamped notes on applications"""
    
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='timeline_notes'
    )
    note = models.TextField()
    is_important = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Note for {self.application} - {self.created_at.strftime('%Y-%m-%d')}"