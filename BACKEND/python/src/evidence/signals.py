from django.db.models.signals import post_migrate, post_save, post_delete, m2m_changed
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver

from .models import Evidence, AuditLog 
from .tasks import run_forensic_analysis_task  # Forensic background engine

# --- 1. AUTOMATED SECURITY BOOTSTRAPPING ---

@receiver(post_migrate)
def create_user_groups(sender, **kwargs):
    """
    SYSTEM INITIALIZATION:
    Automatically sets up the DEVS hierarchy (Clerks, Advocates, Admin) 
    every time the database schema is updated.
    """
    if sender.name != 'evidence':  
        return

    # 1. Establish the forensic roles
    clerk_group, _ = Group.objects.get_or_create(name='Clerks')
    advocate_group, _ = Group.objects.get_or_create(name='Advocates')
    admin_group, _ = Group.objects.get_or_create(name='Admin')

    # 2. Fetch permissions specific to our Evidence vault
    content_type = ContentType.objects.get_for_model(Evidence)
    view_p = Permission.objects.get(codename='view_evidence', content_type=content_type)
    add_p = Permission.objects.get(codename='add_evidence', content_type=content_type)
    change_p = Permission.objects.get(codename='change_evidence', content_type=content_type)

    # --- PERMISSION ASSIGNMENT ---
    clerk_group.permissions.add(view_p, add_p)
    advocate_group.permissions.add(view_p, add_p, change_p)
    
    # Admins get log viewing permissions automatically
    log_content_type = ContentType.objects.get_for_model(AuditLog)
    view_log_p = Permission.objects.get(codename='view_auditlog', content_type=log_content_type)
    admin_group.permissions.add(view_log_p)

    print("--- DEVS Roles Initialized: Clerk, Advocate, & Admin levels enforced ---")


# --- 2. AUTOMATIC ROLE INHERITANCE ---

@receiver(m2m_changed, sender=User.groups.through)
def auto_assign_forensic_roles(sender, instance, action, pk_set, **kwargs):
    """
    DYNAMIC ROLE ASSIGNMENT:
    When a user is added to a Group, this signal automatically pushes the 
    correct technical permissions to that specific user account.
    """
    if action == "post_add":
        for group_id in pk_set:
            group = Group.objects.get(pk=group_id)
            
            perms = []
            if group.name == 'Clerks':
                perms = ['add_evidence', 'view_evidence']
            elif group.name == 'Advocates':
                perms = ['view_evidence', 'change_evidence', 'add_evidence']
            elif group.name == 'Admin':
                perms = ['view_auditlog', 'add_user', 'change_user', 'view_user']

            for p_code in perms:
                try:
                    p = Permission.objects.get(codename=p_code)
                    instance.user_permissions.add(p)
                except Permission.DoesNotExist:
                    continue
        
        print(f"--- Technical Permissions Sync Complete for User: {instance.username} ---")


# --- 3. THE FORENSIC TRIGGER (Automatic Analysis) ---

@receiver(post_save, sender=Evidence)
def trigger_auto_verification(sender, instance, created, **kwargs):
    """
    AUTOMATED FORENSIC ENGINE:
    The moment a file is saved, this triggers the Celery task to 
    perform deep forensic analysis (EXIF, Pixel checks, and hashing).
    """
    if created and instance.file_upload:
        # This offloads the heavy processing to a background worker
        run_forensic_analysis_task.delay(instance.id)
        print(f"--- Forensic Scan Queued for Exhibit: {instance.title} ---")


# --- 4. THE SILENT OBSERVER (Chain of Custody) ---

@receiver(post_save, sender=Evidence)
def log_evidence_activity(sender, instance, created, **kwargs):
    """
    AUTOMATED AUDITING:
    Watches the Evidence model. Creates a permanent Audit Log entry 
    every time evidence is touched.
    """
    if created:
        action_name = 'UPLOAD'
        detail_msg = f"New exhibit ingested. Initial Hash: {instance.original_hash[:10] if instance.original_hash else 'CALCULATING'}..."
    else:
        action_name = 'UPDATE'
        detail_msg = f"Metadata/Status modified. Integrity: {instance.integrity_status}"

    AuditLog.objects.create(
        evidence=instance,
        user=instance.uploaded_by,
        action=action_name,
        details=detail_msg,
        recorded_hash=instance.original_hash or "PENDING"
    )
    
    print(f"--- Chain of Custody Updated: {action_name} recorded for {instance.title} ---")


# --- 5. THE "TOMBSTONE" PROTOCOL (Deletions) ---

@receiver(post_delete, sender=Evidence)
def log_evidence_deletion(sender, instance, **kwargs):
    """
    LEGAL TRACEABILITY:
    Ensures that even if an exhibit is deleted, a 'tombstone' record 
    persists in the Audit Log for forensic history.
    """
    AuditLog.objects.create(
        evidence=None, 
        user=instance.uploaded_by,
        action='DELETE',
        recorded_hash=instance.original_hash,
        details=(
            f"CRITICAL: Evidence '{instance.title}' (ID: {instance.id}) was purged. "
            f"Original Hash: {instance.original_hash}"
        )
    )
    
    print(f"--- Permanent Audit Record created for DELETED item: {instance.title} ---")