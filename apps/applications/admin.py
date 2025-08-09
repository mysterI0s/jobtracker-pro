from django.contrib import admin
from .models import Application, ApplicationDocument, ApplicationNote


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'job_title', 'company_name', 'status', 
        'priority', 'applied_date', 'follow_up_date'
    ]
    list_filter = [
        'status', 'priority', 'applied_date', 'application_method',
        'job__company', 'created_at'
    ]
    search_fields = [
        'job__title', 'job__company__name', 'user__username',
        'recruiter_name', 'notes'
    ]
    date_hierarchy = 'applied_date'
    readonly_fields = ['created_at', 'updated_at', 'days_since_applied']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'job', 'status', 'priority')
        }),
        ('Important Dates', {
            'fields': ('applied_date', 'response_date', 'interview_date', 'follow_up_date')
        }),
        ('Application Materials', {
            'fields': ('cover_letter', 'resume_version', 'portfolio_link', 'application_method')
        }),
        ('Contact Information', {
            'fields': ('recruiter_name', 'recruiter_email', 'hiring_manager_name', 'contact_phone'),
            'classes': ('collapse',)
        }),
        ('Offer Details', {
            'fields': ('salary_offered', 'salary_currency', 'benefits_offered', 'start_date'),
            'classes': ('collapse',)
        }),
        ('Notes & Feedback', {
            'fields': ('notes', 'interview_feedback', 'rejection_reason')
        }),
        ('Metadata', {
            'fields': ('days_since_applied', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['mark_as_applied', 'set_follow_up_reminder']
    
    def job_title(self, obj):
        return obj.job.title
    job_title.short_description = 'Job Title'
    
    def company_name(self, obj):
        return obj.job.company.name
    company_name.short_description = 'Company'
    
    def days_since_applied(self, obj):
        days = obj.days_since_applied
        if days is None:
            return "Not applied yet"
        elif days == 0:
            return "Today"
        elif days == 1:
            return "1 day ago"
        else:
            return f"{days} days ago"
    days_since_applied.short_description = 'Days Since Applied'
    
    def mark_as_applied(self, request, queryset):
        for application in queryset:
            application.mark_as_applied()
        self.message_user(request, f"{queryset.count()} applications marked as applied.")
    mark_as_applied.short_description = "Mark as applied"
    
    def set_follow_up_reminder(self, request, queryset):
        for application in queryset:
            application.set_follow_up_reminder()
        self.message_user(request, f"Follow-up reminders set for {queryset.count()} applications.")
    set_follow_up_reminder.short_description = "Set follow-up reminder (7 days)"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'job__company')


@admin.register(ApplicationDocument)
class ApplicationDocumentAdmin(admin.ModelAdmin):
    list_display = ['application', 'document_type', 'filename', 'file_size_display', 'uploaded_at']
    list_filter = ['document_type', 'uploaded_at']
    search_fields = ['application__job__title', 'filename', 'description']
    readonly_fields = ['file_size', 'uploaded_at']
    
    def file_size_display(self, obj):
        size = obj.file_size
        for unit in ['bytes', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    file_size_display.short_description = 'File Size'


@admin.register(ApplicationNote)
class ApplicationNoteAdmin(admin.ModelAdmin):
    list_display = ['application', 'note_preview', 'is_important', 'created_at']
    list_filter = ['is_important', 'created_at']
    search_fields = ['application__job__title', 'note']
    readonly_fields = ['created_at']
    
    def note_preview(self, obj):
        return obj.note[:50] + "..." if len(obj.note) > 50 else obj.note
    note_preview.short_description = 'Note Preview'