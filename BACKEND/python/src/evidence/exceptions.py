# evidence/exceptions.py
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

# --- CORE FORENSIC ERROR TYPES ---
# We're defining these to differentiate between a simple "page not found" 
# and a serious issue with evidence data.

class ForensicError(Exception):
    """The parent class for all DEVS-related security or data failures."""
    pass

class IntegrityVerificationFailed(ForensicError):
    """Triggered if the system can't even finish checking a file's safety."""
    pass

class FileCorruptionError(ForensicError):
    """Triggered when an exhibit is unreadable, empty, or damaged during upload."""
    pass

class HashMismatchError(ForensicError):
    """
    The 'Red Alert' error. 
    This is raised if a file's digital fingerprint has changed since it was first logged.
    """
    pass

# --- GLOBAL ERROR TRANSLATOR ---

def devs_exception_handler(exc, context):
    """
    This function intercepts errors before they reach the user.
    It translates raw Python crashes into clean, professional JSON for the API.
    """
    
    # First, let Django Rest Framework handle the standard stuff (like 404s).
    response = exception_handler(exc, context)

    # Now, we look for our specialized ForensicErrors.
    # If a file fails a security check, we want the API to return a 'Protocol Violation'.
    if isinstance(exc, ForensicError):
        data = {
            'error': 'Forensic Protocol Violation', 
            'detail': str(exc),
            'timestamp': str(status.HTTP_400_BAD_REQUEST) # Tracking when the 'violation' occurred
        }
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    # If it's a regular error (like a missing page), we just attach the status code
    # to the response so the frontend knows exactly what went wrong.
    if response is not None:
        response.data['status_code'] = response.status_code
        
    return response