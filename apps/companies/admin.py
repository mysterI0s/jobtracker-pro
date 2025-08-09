from django.contrib import admin
from .models import Company, JobSource


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'industry', 'size', 'headquarters', 'created_at']
    list_filter = ['size', 'industry', 'created_at']
    search_fields = ['name', 'industry', 'headquarters']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'website', 'description')
        }),
        ('Company Details', {
            'fields': ('industry', 'size', 'headquarters', 'founded_year', 'logo_url')
        }),
        ('Social Media', {
            'fields': ('linkedin_url', 'twitter_url', 'github_url'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(JobSource)
class JobSourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'last_scraped', 'total_jobs_scraped', 'scrape_interval']
    list_filter = ['is_active', 'last_scraped']
    search_fields = ['name', 'base_url']
    readonly_fields = ['last_scraped', 'total_jobs_scraped', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'base_url', 'is_active')
        }),
        ('Scraping Configuration', {
            'fields': ('scrape_interval', 'rate_limit', 'user_agent')
        }),
        ('Statistics', {
            'fields': ('last_scraped', 'total_jobs_scraped'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['reset_scraping_stats', 'activate_sources', 'deactivate_sources']
    
    def reset_scraping_stats(self, request, queryset):
        queryset.update(total_jobs_scraped=0, last_scraped=None)
        self.message_user(request, "Scraping statistics reset for selected sources.")
    reset_scraping_stats.short_description = "Reset scraping statistics"
    
    def activate_sources(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, "Selected sources activated.")
    activate_sources.short_description = "Activate selected sources"
    
    def deactivate_sources(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, "Selected sources deactivated.")
    deactivate_sources.short_description = "Deactivate selected sources"