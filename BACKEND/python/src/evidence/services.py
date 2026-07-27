import hashlib
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Evidence, AuditLog

def verify_evidence_integrity(evidence_id, user_id=None):
    """
    THE VERIFICATION PROTOCOL:
    This service acts as the 'Digital Watchdog.' It re-scans a file on disk
    to see if even a single pixel or character has changed since it was first logged.
    """
    try:
        # Fetching the specific exhibit from our vault.
        evidence = Evidence.objects.get(id=evidence_id)
        
        # --- IDENTITY CHECK ---
        # We resolve who is triggering this check (User vs. System Task).
        # This ensures the Audit Log shows exactly who initiated the verification.
        user_obj = None
        if user_id:
            try:
                user_obj = User.objects.get(id=user_id)
            except User.DoesNotExist:
                user_obj = None

        # --- STEP 1: GENERATE NEW FINGERPRINT ---
        # We read the file in small chunks (4KB) to stay memory-efficient,
        # especially important if we're dealing with large CCTV footage.
        sha256_hash = hashlib.sha256()
        with evidence.file_upload.open('rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        current_disk_hash = sha256_hash.hexdigest()

        # --- STEP 2: THE FORENSIC COMPARISON ---
        # We compare the fresh hash from the disk against the 'Original Hash' 
        # that was locked into the database at the moment of upload.
        if current_disk_hash == evidence.original_hash:
            evidence.integrity_status = 'INTACT'
            status_detail = "Verification Successful: File is identical to original."
            success = True
        else:
            # If they don't match, the evidence is legally compromised.
            evidence.integrity_status = 'FAILED'
            # We flag this as 'CRITICAL' in the notes for immediate review.
            status_detail = f"CRITICAL: Hash mismatch detected! Current: {current_disk_hash[:10]}..."
            success = False

        # Marking the exact time this verification happened for our records.
        evidence.last_verified_at = timezone.now()
        evidence.save()

        # --- STEP 3: PERMANENT AUDIT RECORD ---
        # We create an entry in the Chain of Custody log.
        # This captures the 'Disk Snapshot' (recorded_hash) at this exact moment.
        AuditLog.objects.create(
            evidence=evidence,
            user=user_obj,
            action='VERIFY',
            recorded_hash=current_disk_hash, 
            details=status_detail
        )
        
        return success

    except Exception as e:
        # If the file is missing or the database is unreachable, we log the failure.
        # This is vital for troubleshooting system health during an investigation.
        print(f"Verification system failure for Evidence {evidence_id}: {e}")
        return False