import os
from pathlib import Path
from celery.schedules import crontab

# Setting up the project root
BASE_DIR = Path(__file__).resolve().parent.parent

# --- SECURITY & ACCESS ---
DEBUG = True
ALLOWED_HOSTS = ['192.168.137.1', '172.17.16.1', '127.0.0.1', 'localhost', '*']
SECRET_KEY = 'django-insecure-your-secret-key-here' 

INSTALLED_APPS = [
    'evidence',          # Our core logic lives here
    'jazzmin',           # Modernizing the admin look (must stay above 'admin')
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles', 
    'rest_framework',
    'rest_framework.authtoken', 
    'django_filters',  
    'drf_spectacular',   # This generates our API documentation
    'whitenoise.runserver_nostatic', 
]

# --- REGIONAL SETTINGS ---
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Kampala'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# --- API BEHAVIOR (REST FRAMEWORK) ---
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '10/minute',
        'user': '100/minute',
    },
    'EXCEPTION_HANDLER': 'evidence.exceptions.devs_exception_handler',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'DEVS API - Digital Evidence Verification System',
    'DESCRIPTION': 'Forensic backend for AF Mpanga Legal Practitioners',
    'VERSION': '1.0.0',
}

# --- THE REQUEST PIPELINE ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'DEVS_PROJECT.urls' 

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], 
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'DEVS_PROJECT.wsgi.application'

# --- DATA STORAGE ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'devs_db',
        'USER': 'postgres',
        'PASSWORD': '@Slimboy70', 
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# --- ASSETS & FILE HANDLING ---
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# --- HEAVY LIFTING CONFIG ---
DATA_UPLOAD_MAX_MEMORY_SIZE = 534773760 
FILE_UPLOAD_MAX_MEMORY_SIZE = 534773760

# --- BACKGROUND TASKS (CELERY) ---
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Africa/Kampala'

CELERY_BEAT_SCHEDULE = {
    'daily-integrity-check': {
        'task': 'evidence.tasks.run_all_integrity_checks',
        'schedule': crontab(hour=0, minute=0), 
    },
}

# --- ADMIN INTERFACE CUSTOMIZATION (JAZZMIN) ---
JAZZMIN_SETTINGS = {
    # Site Branding
    "site_title": "AF Mpanga DEVS",
    "site_header": "DEVS",
    "site_brand": "AF Mpanga DEVS",
    "site_logo": "images/logo.png", 
    "welcome_sign": "Welcome to the DEVS Forensic Portal",
    "copyright": "2026 AF Mpanga DEVS Ltd",
    "user_avatar": None,

    # UI Behavior
    "show_sidebar": True,
    "navigation_expanded": True,
    "use_google_fonts": True,
    "show_ui_builder": False,
    "changeform_format": "horizontal_tabs",

    # --- SIDEBAR & CONTENT LISTING ---
    # We use the App labels here to group the models properly
    "side_menu_list": [
        "evidence",          # Group 1: Forensic Tools (App Label)
        "auth",              # Group 2: User Management (App Label)
    ],

    # Icons for specific models within the apps
    "icons": {
        "auth.user": "fas fa-user-shield",
        "auth.Group": "fas fa-users",
        "evidence.Evidence": "fas fa-file-medical",
        "evidence.AuditLog": "fas fa-clipboard-list",
        "evidence.SupportFaq": "fas fa-question-circle",
    },

    # --- ORDERING: Controls the sequence within the sidebar and dashboard ---
    "order_with_respect_to": [
        "evidence.Evidence", 
        "evidence.AuditLog", 
        "evidence.SupportFaq", 
        "auth"
    ],
    
    "search_model": ["evidence.Evidence"],

    # --- TOP MENU LOGIC ---
    "topmenu_links": [
        {"name": "Home", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Support", "url": "/admin/support/", "new_window": False}, 
        {"model": "evidence.Evidence"},
        {"model": "evidence.AuditLog"},
        {"model": "auth.User"},
    ],

    # --- USER MENU LOGIC ---
    "usermenu_links": [
        {"name": "Developer Profile", "url": "https://www.linkedin.com/in/sabri-alfred-duku-slimboy-7b475b358", "new_window": True},
        {"model": "auth.user"},
    ],
}

# UI Theme Tweaks
JAZZMIN_UI_TWEAKS = {
    "navbar_cls": "navbar-dark",
    "navbar": "navbar-primary", 
    "brand_colour": "navbar-primary",
    "accent": "accent-primary",
    "navbar_fixed": True,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "no_navbar_border": False,
    "sidebar_link_nav_small_text": False,
    "visual_berri_theme": False,
    "show_ui_builder": False,
}

# --- AUTHENTICATION REDIRECTS ---
LOGIN_REDIRECT_URL = '/admin/' 
LOGOUT_REDIRECT_URL = '/admin/login/'