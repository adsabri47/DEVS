from django import forms
from .models import Evidence

class EvidenceUploadForm(forms.ModelForm):
    """
    FORENSIC INGESTION FORM:
    This form is the 'Entry Gate' for new exhibits. It translates our 
    database model into a clean HTML interface for investigators.
    """
    class Meta:
        # We're tying this form directly to the Evidence model to keep 
        # validation logic consistent with our database rules.
        model = Evidence
        
        # --- FIELD SELECTION ---
        # We only expose fields that the user needs to provide. 
        # Metadata like 'original_hash' and 'integrity_status' 
        # are handled by the backend to prevent unauthorized manipulation.
        fields = ['title', 'description', 'file_upload']

        # --- CUSTOM WIDGETS ---
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 3, 
                'placeholder': 'Provide a brief summary of the exhibit contents...'
            }),
            'title': forms.TextInput(attrs={
                'placeholder': 'e.g., CCTV Footage - Kampala Road Branch'
            }),
        }

    def __init__(self, *args, **kwargs):
        """
        UI ENHANCEMENT: Jazzmin & Bootstrap Compatibility
        This method runs when the form is loaded, allowing us to inject 
        CSS classes, professional formatting, and kill redundant UI elements.
        """
        super().__init__(*args, **kwargs)
        
        # 1. THE "NO-DASH" PROTOCOL (Strict Enforcement)
        # We replace the default Django '---------' with professional text or remove it.
        if 'uploaded_by' in self.fields:
            self.fields['uploaded_by'].empty_label = "Select Authorized Personnel..."

        if 'integrity_status' in self.fields:
            # Force the removal of the empty label
            self.fields['integrity_status'].empty_label = None 
            
            # Explicitly filter the choices list to remove any empty/dash options
            # This ensures that even if Django tries to inject a blank choice, it is purged.
            self.fields['integrity_status'].choices = [
                choice for choice in self.fields['integrity_status'].choices if choice[0] != ''
            ]

        # 2. UI POLISH: Injecting Bootstrap classes
        # This ensures the form matches the modern look of your Jazzmin dashboard.
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
            
        # 3. FORENSIC AWARENESS: Guidance for the User
        # This creates awareness BEFORE the user uploads, as per your Phase 4 requirement.
        self.fields['file_upload'].help_text = (
            "<strong>Forensic Requirements:</strong><br>"
            "- Accepted: PDF, JPEG, PNG, MP4, MP3, TXT.<br>"
            "- Maximum File Size: 500MB.<br>"
            "<em>All files undergo binary header inspection upon ingestion.</em>"
        )

        # 4. FIELD LABELING
        self.fields['file_upload'].label = "Digital Exhibit File"