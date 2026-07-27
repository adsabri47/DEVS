from rest_framework import permissions

class IsAdvocate(permissions.BasePermission):
    """
    PROTOCOL: Role-Based Access Control (RBAC)
    We're ensuring that only verified members of the 'Advocates' group
    can even attempt to enter this part of the system. 
    """
    def has_permission(self, request, view):
        # We check the user's organizational group. 
        # If they aren't labeled as an 'Advocate', the gate stays closed.
        return request.user.groups.filter(name='Advocates').exists()

class IsOwnerOrAssigned(permissions.BasePermission):
    """
    PROTOCOL: Object-Level Security
    Just because you're an Advocate doesn't mean you have clearance for every file.
    This check ensures a strict 'Need to Know' basis for individual exhibits.
    """
    def has_object_permission(self, request, view, obj):
        # ADMIN OVERRIDE: 
        # Superusers (system leads) can bypass this for maintenance or emergency audits.
        if request.user.is_superuser:
            return True
            
        # CHAIN OF CUSTODY CHECK:
        # We compare the file's 'uploaded_by' metadata against the current user's ID.
        # If they don't match, access is denied to prevent unauthorized viewing.
        return obj.uploaded_by == request.user