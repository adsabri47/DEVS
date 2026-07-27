import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse  # Added for Status API

# DRF Imports for the API backbone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

# Swagger/Schema Imports for professional API documentation
from drf_spectacular.utils import extend_schema

# Forensic Imports - Bringing in our custom DEVS logic
from .forms import EvidenceUploadForm
from .models import Evidence, AuditLog, SupportFaq  # Added SupportFaq here
from .serializers import EvidenceSerializer 
from .reports import generate_verification_certificate 
from .permissions import IsAdvocate, IsOwnerOrAssigned 

# Custom Forensic Exceptions for specific error handling
from .exceptions import FileCorruptionError, HashMismatchError, ForensicError

# Initializing the logger for system monitoring
logger = logging.getLogger(__name__)

# --- API SECTION: MANAGING DIGITAL EXHIBITS ---

@extend_schema(tags=['Evidence Management'])
class EvidenceViewSet(viewsets.ModelViewSet):
    """
    THE DIGITAL VAULT API:
    Handles all programmatic interactions with evidence.
    Updated with Phase 4 Privacy: Users only retrieve what they are authorized to see.
    """
    serializer_class = EvidenceSerializer
    filter_backends = [DjangoFilterBackend]
    
    filterset_fields = {
        'mime_type': ['exact'],
        'uploaded_at': ['gte', 'lte'],
        'uploaded_by': ['exact'],
    }

    def get_queryset(self):
        """
        API LEVEL PRIVACY:
        Restricts the API results based on user roles.
        """
        user = self.request.user
        if not user.is_authenticated:
            return Evidence.objects.none()
            
        if user.is_superuser or user.groups.filter(name='Judges').exists():
            return Evidence.objects.all().order_by('-uploaded_at')
        return Evidence.objects.filter(uploaded_by=user).order_by('-uploaded_at')

    def get_permissions(self):
        """
        DYNAMIC SECURITY PROTOCOL:
        Assigns different clearance levels based on the action.
        """
        if self.action == 'destroy':
            return [permissions.IsAdminUser()]
        elif self.action == 'create':
            return [permissions.IsAuthenticated()]
        else:
            return [permissions.IsAuthenticated(), IsAdvocate(), IsOwnerOrAssigned()]

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated, IsOwnerOrAssigned])
    def status(self, request, pk=None):
        """
        AUTOMATIC LOGIC STATUS CHECK:
        Provides the latest forensic status of the exhibit.
        Used by the frontend to see if the background scan is finished.
        """
        evidence = self.get_object()
        return Response({
            'id': evidence.id,
            'status': evidence.integrity_status,
            'last_verified': evidence.last_verified_at.strftime("%Y-%m-%d %H:%M:%S") if evidence.last_verified_at else "Pending Scan...",
            'forensic_notes': getattr(evidence, 'tamper_details', "Analysis in progress or clean.") 
        })

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsAdvocate])
    def verify(self, request, pk=None):
        """
        API VERIFICATION TRIGGER:
        Allows an Advocate/Judge to manually trigger a re-hash of the exhibit.
        """
        evidence = self.get_object()
        new_status = evidence.check_integrity()
        
        latest_log = AuditLog.objects.filter(evidence=evidence, action='VERIFY').order_by('-timestamp').first()
        if latest_log:
            latest_log.user = request.user
            latest_log.save()

        return Response({
            "message": "Forensic Integrity Check Complete",
            "exhibit_id": evidence.id,
            "current_status": new_status,
            "verified_by": request.user.username,
            "timestamp": evidence.last_verified_at
        }, status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        file = self.request.FILES.get('file_upload')
        if file and file.size == 0:
            raise FileCorruptionError("The uploaded file appears to be empty or corrupted.")
            
        try:
            serializer.save(uploaded_by=self.request.user)
        except (IOError, OSError) as e:
            logger.error(f"CRITICAL STORAGE FAILURE: {e}")
            raise ForensicError("The Digital Vault is temporarily offline.")

# --- WEB VIEW SECTION: THE INVESTIGATOR DASHBOARD ---

@login_required
def check_status(request, evidence_id):
    """
    Standard Django View for Status Checking.
    Useful for AJAX calls from the simple Evidence List page.
    """
    try:
        if request.user.is_superuser or request.user.groups.filter(name='Judges').exists():
            obj = Evidence.objects.get(id=evidence_id)
        else:
            obj = Evidence.objects.get(id=evidence_id, uploaded_by=request.user)

        return JsonResponse({
            'status': obj.integrity_status,
            'details': getattr(obj, 'tamper_details', "No tampering detected."),
            'last_verified': obj.last_verified_at.strftime("%Y-%m-%d %H:%M:%S") if obj.last_verified_at else "N/A"
        })
    except Evidence.DoesNotExist:
        return JsonResponse({'error': 'Evidence not found or access denied'}, status=404)

@login_required
def dashboard_view(request):
    """
    Displays summary statistics.
    PHASE 4 UPDATE: Statistics are filtered by user access level.
    """
    user = request.user
    if user.is_superuser or user.groups.filter(name='Judges').exists():
        base_evidence = Evidence.objects.all()
    else:
        base_evidence = Evidence.objects.filter(uploaded_by=user)

    context = {
        'total_evidence': base_evidence.count(),
        'recent_evidence': base_evidence.order_by('-uploaded_at')[:5],
        'total_logs': AuditLog.objects.filter(user=user).count() if not user.is_superuser else AuditLog.objects.count(),
    }
    return render(request, 'evidence/dashboard.html', context)

@login_required
def upload_evidence(request):
    """
    Handles the web-based upload form.
    """
    if request.method == 'POST':
        form = EvidenceUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                uploaded_file = request.FILES.get('file_upload')
                if uploaded_file and uploaded_file.size == 0:
                    raise FileCorruptionError("Forensic Alert: The uploaded file contains no data.")

                evidence = form.save(commit=False)
                evidence.uploaded_by = request.user
                evidence.save() 
                return redirect('upload_success')

            except FileCorruptionError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"System Error: {str(e)}")
    else:
        form = EvidenceUploadForm()
    return render(request, 'evidence/upload.html', {'form': form})

@login_required
def upload_success(request):
    return render(request, 'evidence/success.html')

@login_required
def evidence_list(request):
    """
    PHASE 4: RESTRICTED SEARCHABLE ARCHIVE
    """
    if request.user.is_superuser or request.user.groups.filter(name='Judges').exists():
        base_queryset = Evidence.objects.all()
    else:
        base_queryset = Evidence.objects.filter(uploaded_by=request.user)

    query = request.GET.get('q')
    if query:
        items = base_queryset.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) | 
            Q(id__icontains=query) |
            Q(device_info__icontains=query) |
            Q(captured_at__icontains=query) |
            Q(location_data__icontains=query)
        ).order_by('-uploaded_at')
    else:
        items = base_queryset.order_by('-uploaded_at')
        
    return render(request, 'evidence/list.html', {
        'evidence_items': items, 
        'query': query
    })

# --- SUPPORT & FAQ SECTION ---

@login_required
def support_view(request):
    """
    View to display FAQ and Contact information for the AF Mpanga DEVS theme.
    """
    faqs = SupportFaq.objects.all()
    context = {
        'faqs': faqs,
        'contact_email': 'support@afmpanga-devs.co.ug',
        'contact_phone': '+256 700 000 000',
    }
    return render(request, 'admin/support.html', context)

# --- PROFESSIONAL SECURE REPORT VIEW ---

@extend_schema(tags=['Forensic Reporting'])
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsAdvocate, IsOwnerOrAssigned])
def download_evidence_report(request, evidence_id):
    """
    AUTHORIZED EXPORT PROTOCOL:
    Strictly restricted to authorized personnel with accountability logging.
    """
    evidence = get_object_or_404(Evidence, id=evidence_id)
    
    AuditLog.objects.create(
        evidence=evidence,
        user=request.user,
        action='DOWNLOAD',
        details=f"Advocate generated a Forensic Certificate for: {evidence.title}",
        recorded_hash=evidence.original_hash
    )
        
    return generate_verification_certificate(evidence)