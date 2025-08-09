from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, JobAlert


# Extend the existing User admin
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


class CustomUserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]


# Unregister the original User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = [
        'display_name', 'current_title', 'career_level', 
        'job_search_status', 'is_actively_searching', 'location'
    ]
    list_filter = [
        'career_level', 'job_search_status', 'is_actively_searching',
        'willing_to_relocate', 'preferred_remote_type', 'created_at'
    ]
    search_fields = [
        'user__username', 'user__first_name', 'user__last_name',
        'current_title', 'location', 'skills'
    ]
    readonly_fields = ['created_at', 'updated_at', 'resume_updated_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'current_title', 'career_level', 'years_of_experience')
        }),
        ('Contact & Location', {
            'fields': ('phone', 'location', 'timezone')
        }),
        ('Professional Links', {
            'fields': ('linkedin_url', 'github_url', 'portfolio_url', 'website_url'),
            'classes': ('collapse',)
        }),
        ('Salary Expectations', {
            'fields': ('desired_salary_min', 'desired_salary_max', 'salary_currency')
        }),
        ('Job Preferences', {
            'fields': (
                'preferred_job_types', 'preferred_remote_type', 
                'willing_to_relocate', 'preferred_locations'
            )
        }),
        ('Skills & Interests', {
            'fields': ('skills', 'industries_of_interest', 'company_sizes_preferred'),
            'classes': ('collapse',)
        }),
        ('Job Search Status', {
            'fields': ('is_actively_searching', 'is_open_to_opportunities', 'job_search_status')
        }),
        ('Notifications', {
            'fields': (
                'email_notifications', 'daily_job_digest', 
                'weekly_summary', 'application_reminders'
            ),
            'classes': ('collapse',)
        }),
        ('Resume', {
            'fields': ('current_resume', 'resume_updated_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def display_name(self, obj):
        return obj.display_name
    display_name.short_description = 'Name'


@admin.register(JobAlert)
class JobAlertAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'name', 'keywords', 'location', 
        'is_active', 'email_frequency', 'jobs_found_count', 'last_sent'
    ]
    list_filter = ['is_active', 'email_frequency', 'remote_only', 'created_at']
    search_fields = ['user__username', 'name', 'keywords', 'location']
    readonly_fields = ['jobs_found_count', 'last_sent', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name', 'is_active')
        }),
        ('Search Criteria', {
            'fields': (
                'keywords', 'location', 'job_types', 'remote_only',
                'salary_min', 'company_sizes', 'experience_levels'
            )
        }),
        ('Alert Settings', {
            'fields': ('email_frequency',)
        }),
        ('Statistics', {
            'fields': ('jobs_found_count', 'last_sent'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['activate_alerts', 'deactivate_alerts']
    
    def activate_alerts(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} alerts activated.")
    activate_alerts.short_description = "Activate selected alerts"
    
    def deactivate_alerts(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} alerts deactivated.")
    deactivate_alerts.short_description = "Deactivate selected alerts"