import hashlib
from celery import shared_task
from django.utils import timezone
from PIL import Image, ImageStat
from .models import Evidence, AuditLog, User
from .utils import calculate_sha256

# --- ASYNCHRONOUS FORENSIC ENGINE ---

@shared_task
def run_forensic_analysis_task(evidence_id):
    """
    DEEP FORENSIC SCAN:
    Detects byte-level tampering and pixel-level modifications.
    Records findings into the 'tamper_details' field for Admin visibility.
    """
    try:
        obj = Evidence.objects.get(id=evidence_id)
    except Evidence.DoesNotExist:
        return f"Error: Evidence {evidence_id} not found."

    if not obj.file_upload:
        return "No file attached for analysis."

    file_path = obj.file_upload.path
    tamper_alerts = []
    
    # 1. HASH INTEGRITY CHECK (Binary level)
    current_hash = calculate_sha256(obj.file_upload)
    
    if current_hash != obj.original_hash:
        tamper_alerts.append("BINARY_MISMATCH: The file's underlying code has been altered.")
        
        # 2. VISUAL ANALYSIS (Pixel and Metadata level)
        if obj.mime_type and 'image' in obj.mime_type:
            try:
                # Use context manager to prevent file locking
                with Image.open(file_path) as img:
                    # Detect Brightness/Exposure Shifts
                    stat = ImageStat.Stat(img)
                    avg_brightness = sum(stat.mean) / len(stat.mean)
                    # Note: You can compare this against a stored 'original_brightness' if added to models
                    
                    # Detect Cropping/Resolution Changes
                    current_res = f"{img.width}x{img.height}"
                    if obj.resolution and current_res != obj.resolution:
                         tamper_alerts.append(f"CROP_DETECTED: Resolution changed from {obj.resolution} to {current_res}.")
                    
                    # Detect Metadata (EXIF) Stripping
                    if not getattr(img, '_getexif', lambda: None)():
                        tamper_alerts.append("METADATA_STRIPPED: Forensic EXIF headers have been removed.")
                
            except Exception as e:
                tamper_alerts.append(f"VISUAL_ANALYSIS_FAILED: {str(e)}")

        # --- UPDATE RECORD FOR FAILURE ---
        details_summary = " | ".join(tamper_alerts)
        
        # Using .save() instead of .update() here to ensure tamper_details is handled
        obj.integrity_status = "FAILED"
        obj.tamper_details = details_summary
        obj.last_verified_at = timezone.now()
        obj.save()

        # Log to Audit Trail
        AuditLog.objects.create(
            evidence=obj,
            action='VERIFY',
            recorded_hash=current_hash,
            details=f"TAMPERING DETECTED: {details_summary}"
        )
        return f"Forensic Alert: {details_summary}"

    else:
        # --- UPDATE RECORD FOR SUCCESS ---
        obj.integrity_status = "INTACT"
        obj.tamper_details = "No integrity issues detected. Hash matches original ingestion seal."
        obj.last_verified_at = timezone.now()
        obj.save()
        
        return f"Success: Evidence {obj.id} verified as INTACT."


@shared_task
def run_integrity_check_task(evidence_id, user_id=None):
    """
    Wrapper for consistency across the system.
    """
    return run_forensic_analysis_task(evidence_id)


@shared_task
def run_all_integrity_checks():
    """
    SYSTEM-WIDE AUDIT PROTOCOL:
    Iterates through the entire vault and triggers forensic scans for every file.
    """
    evidences = Evidence.objects.all()
    for e in evidences:
        run_forensic_analysis_task.delay(e.id) 
    
    return f"Queued {evidences.count()} files for the scheduled forensic audit."