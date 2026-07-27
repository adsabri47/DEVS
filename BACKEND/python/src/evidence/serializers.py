from rest_framework import serializers
from .models import Evidence

class EvidenceSerializer(serializers.ModelSerializer):
    """
    THE DATA TRANSLATOR:
    This class converts our complex Evidence model into a clean JSON format
    so it can be sent over the network to the frontend or mobile apps.
    """
    class Meta:
        # Linking directly to our Evidence vault model
        model = Evidence
        
        # --- EXPORTED DATA FIELDS ---
        # These are the specific pieces of information we allow the API to see.
        # We've included the MIME type and Hash to match our forensic reporting.
        fields = [
            'id', 
            'file_upload', 
            'original_hash', 
            'mime_type',      
            'uploaded_at', 
            'title', 
            'description', 
            'uploaded_by'
        ]

        # --- SECURITY LOCKS (Read-Only) ---
        # We're making critical forensic data read-only.
        # This prevents anyone from using the API to manually change 
        # a file's hash, ID, or upload timestamp—preserving the Chain of Custody.
        read_only_fields = ['id', 'original_hash', 'uploaded_at', 'mime_type']