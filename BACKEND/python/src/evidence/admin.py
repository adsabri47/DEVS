import datetime
from django.contrib import admin, messages
from django.contrib.auth.models import Group, User
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin, UserAdmin as BaseUserAdmin
from django.core.exceptions import ValidationError
from django.urls import reverse, path
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.http import HttpResponseRedirect

# Import models
from .models import Evidence, AuditLog, SupportFaq
# Import the forensic engine task
from .tasks import run_forensic_analysis_task 

# --- 1. SECURITY: CLEAN USER MANAGEMENT ---
admin.site.unregister(User)

@admin.register(User)
class DevsUserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if not request.user.is_superuser:
            return fieldsets[:-1] 
        return fieldsets

# --- 2. SECURITY: FINAL "VIEW-ONLY" GROUP MANAGEMENT ---
admin.site.unregister(Group)

@admin.register(Group)
class DevsGroupAdmin(BaseGroupAdmin):
    """
    Final Clean Forensic Role Interface for AF Mpanga DEVS.
    Provides a view-only experience for role verification.
    """
    fieldsets = (
        ('Forensic Group Identity', {
            'fields': ('name', 'display_forensic_roles'),
        }),
    )
    
    readonly_fields = ('name', 'display_forensic_roles')

    def display_forensic_roles(self, obj):
        roles_map = {
            "Clerks": [
                "✅ Uploading digital evidence",
                "✅ Viewing the evidence list",
                "✅ Searching the evidence database"
            ],
            "Advocates": [
                "✅ Uploading digital evidence",
                "✅ Viewing the evidence list",
                "✅ Searching the evidence database",
                "✅ Verify integrity of exhibits",
                "✅ Generate Forensic PDF reports"
            ],
            "Admins": [
                "✅ Manage system users",
                "✅ View system audit logs",
                "✅ Full system configuration",
                "✅ All Clerk and Advocate capabilities"
            ]
        }
        current_roles = roles_map.get(obj.name, ["No specific forensic roles assigned to this group name."])
        role_list_html = mark_safe("<br>".join(current_roles))
        return format_html("{}", role_list_html)

    display_forensic_roles.short_description = "Assigned Forensic Roles"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.exclude(name__iexact='Judges')

    def has_add_permission(self, request): return False
    def has_delete_permission(self, request, obj=None): return False
    def has_change_permission(self, request, obj=None): return False

# --- 3. INLINE: AUDIT LOGS ---
class AuditLogInline(admin.TabularInline):
    model = AuditLog
    extra = 0
    readonly_fields = ('user', 'action', 'ip_address', 'timestamp', 'recorded_hash', 'details')
    can_delete = False
    def has_add_permission(self, request, obj=None): return False

# --- 4. THE BULLETPROOF EVIDENCE ADMIN ---
@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    actions = None 
    list_display_links = ('id', 'title')

    search_fields = ('title', 'description', 'id', 'original_hash', 'uploaded_by__username', 'integrity_status')
    list_filter = ('integrity_status', 'uploaded_at')
    inlines = [AuditLogInline]

    readonly_fields = (
        'id', 'integrity_status', 'last_verified_at', 'tamper_details', 
        'captured_at', 'device_info', 'location_data', 'duration', 
        'resolution', 'original_hash', 'mime_type', 'uploaded_at'
    )

    fieldsets = (
        ('General Information', {
            'fields': ('title', 'description', 'file_upload'),
            'description': 'Core exhibit details. Files uploaded here are immediately hashed.'
        }),
        ('Forensic Integrity', {
            'fields': ('integrity_status', 'last_verified_at', 'tamper_details', 'original_hash', 'mime_type'),
            'classes': ('collapse',), 
        }),
        ('Forensic Metadata', {
            'fields': ('captured_at', 'device_info', 'location_data', 'duration', 'resolution'),
            'classes': ('collapse',),
        }),
        ('System Identifiers', {
            'fields': ('id', 'uploaded_at'),
            'classes': ('collapse',),
        }),
    )

    def get_queryset(self, request):
        """Stores the request so forensic_actions can see the user session data"""
        self._current_request = request 
        return super().get_queryset(request)

    # --- FINAL CORRECTED FORENSIC ACTIONS ---
    def forensic_actions(self, obj):
        """
        Final fix for DEVS Forensic Management.
        Ensures format_html always has the required arguments to prevent 500 errors.
        """
        request = getattr(self, '_current_request', None)
        
        if not request:
            return "-"

        # Role identification (case-insensitive)
        is_superuser = request.user.is_superuser
        is_advocate = request.user.groups.filter(name__iexact='Advocates').exists() or \
                      request.user.groups.filter(name__iexact='Advocate').exists()
        is_clerk = request.user.groups.filter(name__iexact='Clerks').exists() or \
                   request.user.groups.filter(name__iexact='Clerk').exists()

        # URLs
        verify_url = reverse('admin:verify-evidence', args=[obj.pk])
        delete_url = reverse('admin:delete-evidence', args=[obj.pk])
        
        # 1. ADMINS: See both buttons
        if is_superuser:
            return format_html(
                '<a class="btn btn-sm btn-success" href="{}" style="background-color: #4ecca3; color: white; padding: 4px 8px; margin-right: 5px; border-radius: 4px; text-decoration: none;">🔍 Verify</a>'
                '<a class="btn btn-sm btn-danger" href="{}" style="background-color: #ff4b2b; color: white; padding: 4px 8px; border-radius: 4px; text-decoration: none;" onclick="return confirm(\'Confirm Purge?\')">🗑️ Delete</a>',
                verify_url, delete_url
            )
        
        # 2. ADVOCATES: See ONLY Verify
        if is_advocate:
            return format_html(
                '<a class="btn btn-sm btn-success" href="{}" style="background-color: #4ecca3; color: white; padding: 4px 8px; border-radius: 4px; text-decoration: none;">🔍 Verify</a>',
                verify_url
            )
        
        # 3. CLERKS: See View Only message
        if is_clerk:
            return format_html(
                '<span style="color: #999; font-style: italic;">{}</span>', 
                "View Only Access"
            )

        return "-"

    forensic_actions.short_description = 'Forensic Management'

    # --- CUSTOM PROCESSING URLS ---
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<uuid:pk>/verify/', self.admin_site.admin_view(self.process_verify), name='verify-evidence'),
            path('<uuid:pk>/delete-custom/', self.admin_site.admin_view(self.process_delete), name='delete-evidence'),
        ]
        return custom_urls + urls

    def process_verify(self, request, pk):
        obj = self.get_object(request, pk)
        run_forensic_analysis_task.delay(obj.id)
        self.message_user(request, f"Manual forensic scan queued for {obj.title}")
        return HttpResponseRedirect("../..")

    def process_delete(self, request, pk):
        if not request.user.is_superuser:
            self.message_user(request, "Forensic Integrity Protocol: Only Admins can purge exhibits.", level=messages.ERROR)
            return HttpResponseRedirect("../..")
        
        obj = self.get_object(request, pk)
        obj.delete()
        self.message_user(request, "Evidence purged from vault.")
        return HttpResponseRedirect("../..")

    def save_model(self, request, obj, form, change):
        if not change: 
            if not obj.device_info:
                obj.device_info = request.META.get('HTTP_USER_AGENT', 'Unknown Forensic Device')
            if not obj.captured_at:
                obj.captured_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            obj.uploaded_by = request.user
            obj.integrity_status = "PENDING"
        
        super().save_model(request, obj, form, change)
        run_forensic_analysis_task.delay(obj.id)

    def get_readonly_fields(self, request, obj=None):
        if not obj or request.user.is_superuser:
            return self.readonly_fields
        return [f.name for f in self.model._meta.fields]

    def get_list_display(self, request):
        fields = ['title', 'id', 'integrity_status', 'uploaded_at']
        is_advocate = request.user.groups.filter(name__iexact='Advocate').exists() or \
                      request.user.groups.filter(name__iexact='Advocates').exists()
        
        if is_advocate or request.user.is_superuser:
            fields.insert(3, 'download_report')
            
        fields.append('forensic_actions')
        return fields

    def download_report(self, obj):
        url = reverse('admin_download_report', args=[obj.id])
        return mark_safe(
            f'<a href="{url}" style="background-color: #26af60; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none; font-weight: bold;">PDF Report</a>'
        )
    download_report.short_description = 'Forensic Certificate'

# --- 5. READ-ONLY AUDIT LOG ADMIN ---
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('evidence', 'action', 'user', 'timestamp', 'recorded_hash')
    list_filter = ('action', 'timestamp')
    readonly_fields = ('evidence', 'user', 'action', 'timestamp', 'details', 'recorded_hash')
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False

# --- 6. SUPPORT & FAQ ADMIN ---
@admin.register(SupportFaq)
class SupportFaqAdmin(admin.ModelAdmin):
    list_display = ('question', 'order')
    search_fields = ('question', 'answer')
    list_editable = ('order',)