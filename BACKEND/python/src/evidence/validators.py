# evidence/validators.py
import os
import magic  # libmagic is essential for verifying file headers
from django.core.exceptions import ValidationError

def validate_file_size(value):
    """
    SECURITY GUARD: Resource Management
    Ensures that massive files don't crash the server or fill up storage.
    Limits ingestion to 500MB to maintain system performance.
    """
    filesize = value.size
    limit_mb = 500
    limit_bytes = limit_mb * 1024 * 1024

    # This print statement is a "Live Monitor" for your terminal.
    # It proves the system is actively analyzing the file during your demo.
    print(f"--- FORENSIC SIZE CHECK: {filesize} bytes ---")

    if filesize > limit_bytes:
        current_size_mb = filesize / (1024 * 1024)
        raise ValidationError(
            f"Forensic Violation: The maximum file size allowed is {limit_mb}MB. "
            f"Your file is {current_size_mb:.2f}MB. Upload rejected."
        )

def validate_forensic_file_type(value):
    """
    FORENSIC GATEKEEPER: Dual-Layer Verification
    1. Extension Check: Filters by allowed file endings.
    2. Deep Packet Inspection: Verifies true MIME type via Magic Numbers.
    """
    
    # --- LAYER 1: EXTENSION VALIDATION ---
    valid_extensions = [
        # Visual Evidence
        '.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.raw', 
        # Multimedia
        '.mp4', '.mkv', '.avi', '.mov', '.mp3', '.wav', 
        # Documentary Evidence
        '.pdf', '.docx', '.txt', '.csv', '.xlsx',
        # Forensic Disk Images & Archives
        '.iso', '.zip', '.e01', '.ad1', '.7z', '.rar'
    ]
    
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in valid_extensions:
        raise ValidationError(
            f"Unsupported Forensic Format: '{ext}'. "
            f"Please upload a recognized forensic file type."
        )

    # --- LAYER 2: DEEP PACKET INSPECTION (MIME) ---
    # Acceptable forensic categories (broadly grouped for flexibility)
    ALLOWED_MIME_CATEGORIES = [
        'image/', 'video/', 'audio/', 'application/pdf', 'text/plain',
        'application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed',
        'application/octet-stream', 'application/msword', 
        'application/vnd.openxmlformats-officedocument', 'text/csv'
    ]

    # Read the first 2048 bytes to identify the file signature (Magic Numbers)
    file_content = value.read(2048)
    
    # CRITICAL: 'rewind' the file pointer so the next function can read it from the start.
    value.seek(0)  
    
    mime_type = magic.from_buffer(file_content, mime=True)

    print(f"--- FORENSIC TYPE CHECK: {mime_type} (Ext: {ext}) ---")

    # Check if the detected MIME starts with any of our allowed categories
    is_valid_mime = any(mime_type.startswith(cat) for cat in ALLOWED_MIME_CATEGORIES)

    if not is_valid_mime:
        raise ValidationError(
            f"Forensic Alert: Header mismatch. The file content type ({mime_type}) "
            "does not match permitted forensic standards."
        )