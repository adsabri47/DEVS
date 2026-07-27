from django.shortcuts import render
from .models import Evidence, AuditLog
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

def forensic_dashboard_stats(request):
    """
    Unified Forensic Dashboard Logic.
    Combines strict key matching with case-insensitive string matching 
    to ensure all integrity and activity metrics are captured correctly.
    """

    # --- 1. CORE INTEGRITY COUNTERS ---
    # We use Q objects to check for BOTH the short code and the descriptive label
    # to prevent data from slipping through if the model choices change.
    verified_count = Evidence.objects.filter(
        Q(integrity_status='INTACT') | Q(integrity_status__icontains='Match')
    ).count()

    tampered_count = Evidence.objects.filter(
        Q(integrity_status='FAILED') | Q(integrity_status__icontains='Mismatch')
    ).count()

    pending_count = Evidence.objects.filter(
        Q(integrity_status='PENDING') | Q(integrity_status__icontains='Pending')
    ).count()

    total_evidence = Evidence.objects.count()

    # --- 2. ACTION-BASED STATISTICS (Last 30 Days) ---
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # Filtering logs within the 30-day window
    recent_logs_query = AuditLog.objects.filter(timestamp__gte=thirty_days_ago)

    # Capturing specific actions using icontains for flexibility
    u_count = recent_logs_query.filter(action__icontains='UPLOAD').count()
    d_count = recent_logs_query.filter(action__icontains='DELETE').count()
    dw_count = recent_logs_query.filter(action__icontains='DOWNLOAD').count()
    
    # Calculate 'Others' (Viewing, Verifying, Extracting, etc.)
    total_recent_logs = recent_logs_query.count()
    other_actions = total_recent_logs - (u_count + d_count + dw_count)

    # --- 3. THE CONTEXT DICTIONARY ---
    # This matches the variables used in your HTML/Chart.js templates
    context = {
        # Evidence Stats
        'total': total_evidence,
        'verified': verified_count,
        'tampered': tampered_count,
        'pending': pending_count,
        
        # Activity Stats (30 Day Window)
        'uploaded': u_count,
        'deleted': d_count,
        'downloaded': dw_count,
        'others': max(0, other_actions), # Ensuring we never pass a negative number
        
        # Live Forensic Feed (The 8 most recent system events)
        'recent_activities': AuditLog.objects.all().order_by('-timestamp')[:8],
    }
    
    # Rendering to the custom admin index template
    return render(request, 'admin/index.html', context)