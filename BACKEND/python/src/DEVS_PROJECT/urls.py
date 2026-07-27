from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from rest_framework.routers import DefaultRouter

# Tools for generating our interactive API documentation
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

# Pulling in our custom logic for report generation and general views
from evidence.views import download_evidence_report, support_view
from evidence import views 
# Importing the dashboard view for the admin override
from evidence.dashboard_views import forensic_dashboard_stats

# --- API ROUTING SETUP ---
# We're using the DefaultRouter to automatically handle the standard 
# GET/POST/PUT/DELETE routes for our evidence assets.
router = DefaultRouter()
router.register(r'evidence', views.EvidenceViewSet, basename='evidence-api')

urlpatterns = [
    # --- LANDING LOGIC ---
    # When someone hits the base URL, we want them straight at the login screen.
    path('', lambda request: redirect('admin:login')),

    # --- FORENSIC SUPPORT & FAQ ---
    # This must be defined before admin.site.urls to avoid being swallowed by the admin regex
    path('admin/support/', support_view, name='admin-support'),

    # --- FORENSIC REPORT GENERATION ---
    # Specialized path for downloading secure reports via UUID.
    path('admin/evidence/<uuid:evidence_id>/report/', download_evidence_report, name='admin_download_report'),

    # --- THE COMMAND CENTER (OVERRIDE) ---
    # 1. We override the default admin index BEFORE the standard admin.site.urls.
    # This makes the forensic dashboard the first thing users see upon login.
    path('admin/', forensic_dashboard_stats, name='admin_index'),
    
    # 2. The standard Django/Jazzmin admin gateway for all other admin routes.
    path('admin/', admin.site.urls),

    # --- API DOCUMENTATION & SCHEMA ---
    # 'Schema' is the raw data; 'Docs' is the interactive Swagger interface.
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # --- CORE USER INTERFACE ---
    # Web pages for uploading and viewing the digital evidence vault.
    path('upload/', views.upload_evidence, name='upload_evidence'),
    path('success/', views.upload_success, name='upload_success'),
    path('vault/', views.evidence_list, name='evidence_list'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # --- PROGRAMMATIC ACCESS ---
    # All endpoints managed by our router (like /api/evidence/) live under this prefix.
    path('api/', include(router.urls)),
]

# --- FILE SERVING (STATIC & MEDIA) ---
# This ensures that images, CSS, and forensic uploads are accessible.
# Configured to work in both DEBUG and Production-like demo environments.
if settings.DEBUG or not settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)