from django.contrib import admin
from django.utils.html import format_html
from .models import Job, JobBookmark


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'company', 'location', 'job_type', 
        'is_remote', 'salary_display_admin', 'posted_date', 'is_active'
    ]
    list_filter = [
        'job_type', 'is_remote', 'remote_type', 'experience_level',
        'is_active', 'source', 'posted_date', 'company__size'
    ]
    search_fields = ['title', 'company__name', 'location', 'description']
    date_hierarchy = 'posted_date'
    readonly_fields = ['scraped_date', 'created_at', 'updated_at', 'external_id', 'age_in_days']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'company', 'source', 'external_id', 'url')
        }),
        ('Job Details', {
            'fields': ('description', 'requirements', 'benefits')
        }),
        ('Location & Remote', {
            'fields': ('location', 'is_remote', 'remote_type')
        }),
        ('Employment Details', {
            'fields': ('job_type', 'experience_level')
        }),
        ('Salary Information', {
            'fields': ('salary_min', 'salary_max', 'salary_currency', 'salary_period')
        }),
        ('Dates & Status', {
            'fields': ('posted_date', 'expires_date', 'is_active')
        }),
        ('Categorization', {
            'fields': ('tags', 'skills_required'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('scraped_date', 'age_in_days', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['mark_as_active', 'mark_as_inactive', 'refresh_job_data']
    
    def salary_display_admin(self, obj):
        return obj.salary_display
    salary_display_admin.short_description = 'Salary'
    
    def age_in_days(self, obj):
        days = obj.age_in_days
        if days == 0:
            return "Today"
        elif days == 1:
            return "1 day ago"
        else:
            return f"{days} days ago"
    age_in_days.short_description = 'Age'
    
    def mark_as_active(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} jobs marked as active.")
    mark_as_active.short_description = "Mark selected jobs as active"
    
    def mark_as_inactive(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} jobs marked as inactive.")
    mark_as_inactive.short_description = "Mark selected jobs as inactive"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company', 'source')


@admin.register(JobBookmark)
class JobBookmarkAdmin(admin.ModelAdmin):
    list_display = ['user', 'job_title', 'company_name', 'created_at']
    list_filter = ['created_at', 'job__company']
    search_fields = ['user__username', 'job__title', 'job__company__name']
    readonly_fields = ['created_at']
    
    def job_title(self, obj):
        return obj.job.title
    job_title.short_description = 'Job Title'
    
    def company_name(self, obj):
        return obj.job.company.name
    company_name.short_description = 'Company'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'job__company')