from django.apps import AppConfig

class EvidenceConfig(AppConfig):
    """
    APPLICATION CONFIGURATION:
    This class handles the initialization of the Evidence app. 
    It ensures that all forensic listeners and security protocols are 
    activated the moment the server starts.
    """

    # This sets the default ID type for our database tables (BigInt).
    default_auto_field = 'django.db.models.BigAutoField'
    
    # The internal name Django uses to track this app.
    name = 'evidence'

    def ready(self):
        """
        The 'ready' method runs as soon as Django starts up.
        It imports the signals to ensure they are registered.
        """
        
        # 1. Register Forensic Signals:
        # This activates:
        # - The Security Bootstrapper (Creates Clerks, Advocates, Judges)
        # - The Forensic Analysis Trigger (Celery tasks)
        # - The Chain of Custody Logger (Auto-Audit)
        # - The Tombstone Protocol (Deletion tracking)
        try:
            import evidence.signals 
            print("--- DEVS Forensic Engine: Signals connected and active ---")
        except ImportError as e:
            print(f"--- DEVS Forensic Engine Warning: signals.py registration failed: {e} ---")

        # 2. Additional Startup Checks:
        # Logic for checking system health (Redis, storage paths, etc.) can be placed here.
        # This ensures the backend environment is ready for forensic processing.