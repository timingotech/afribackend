import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # third party
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'drf_spectacular',

    # local
    'apps.users',
    'apps.trips',
    'apps.payments',
    'apps.notifications',
    'apps.errors',
    # Async / realtime
    'channels',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'backend_project.middleware.ErrorLoggingMiddleware',  # Log API errors
]

ROOT_URLCONF = 'backend_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'backend_project.wsgi.application'
ASGI_APPLICATION = 'backend_project.asgi.application'

# Database
import dj_database_url

DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {'default': dj_database_url.parse(DATABASE_URL)}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
MEDIA_URL = '/media/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_ROOT = BASE_DIR / 'media'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'users.User'

# DRF + SimpleJWT
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    # Refresh token lifetime set to ~400 days so users remain logged-in until they logout
    'REFRESH_TOKEN_LIFETIME': timedelta(days=400),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# Optional override: longer access token lifetime (seconds) for admin users
ADMIN_ACCESS_TOKEN_LIFETIME_SECONDS = int(os.getenv('ADMIN_ACCESS_TOKEN_LIFETIME_SECONDS', str(12 * 3600)))

# CORS
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# CSRF trusted origins (comma-separated env var). Add your frontend origin(s) here.
# Example for local dev: http://localhost:5173
# Include the production frontend origin by default so cross-site POSTs from
# the deployed site are accepted unless overridden via env var.
CSRF_TRUSTED_ORIGINS = os.getenv(
    'CSRF_TRUSTED_ORIGINS',
    'http://localhost:5173,https://aafriride.com,https://www.aafriride.com',
).split(',')
# Trim any accidental whitespace and drop empty entries
CSRF_TRUSTED_ORIGINS = [o.strip() for o in CSRF_TRUSTED_ORIGINS if o.strip()]

# Redis configuration (optional - kept for future use)
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Celery Configuration
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# In development, run tasks synchronously to avoid needing a separate worker process
# Also enable this if CELERY_TASK_ALWAYS_EAGER_FORCE env var is set (useful for production debugging)
# Force eager execution on Railway for now to ensure emails are sent synchronously
if os.getenv('CELERY_TASK_ALWAYS_EAGER_FORCE', 'False') == 'True':
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True

# Share token TTL (seconds) for public tracking links. Default 6 hours.
SHARE_TOKEN_TTL_SECONDS = int(os.getenv('SHARE_TOKEN_TTL_SECONDS', str(6 * 3600)))
# Redis key prefix for share tokens
SHARE_TOKEN_REDIS_PREFIX = os.getenv('SHARE_TOKEN_REDIS_PREFIX', 'share:token:')

# Channels / channel layers
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [os.getenv('REDIS_URL', REDIS_URL)],
        },
    },
}

# Email Configuration
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')

# On Linux (Railway), use custom backend to bypass SSL verification issues
# Also set a timeout to prevent Gunicorn worker kills
EMAIL_TIMEOUT = 10  # Reduced to 10s to allow for retries within Gunicorn's 30s limit

import platform
if (platform.system() != 'Windows' and 'ZohoEmailBackend' in EMAIL_BACKEND) or os.getenv('RAILWAY_ENVIRONMENT_NAME'):
    # Use our custom backend that ignores SSL cert errors
    EMAIL_BACKEND = 'apps.users.email_backend.UnverifiedEmailBackend'

EMAIL_HOST = os.getenv('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 25))
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False') == 'True'
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'False') == 'True'

# Force TLS on port 587 for Railway/Linux if using Zoho (alternative fix for timeouts)
if os.getenv('RAILWAY_ENVIRONMENT_NAME') and 'zoho' in EMAIL_HOST:
    EMAIL_PORT = 587
    EMAIL_USE_SSL = False
    EMAIL_USE_TLS = True

EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'webmaster@localhost')
EMAIL_SSL_CERTFILE = None
EMAIL_SSL_KEYFILE = None

# SMS Configuration (Twilio)
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER', '')

# SMS Provider (twilio or mock for testing)
SMS_PROVIDER = os.getenv('SMS_PROVIDER', 'mock')  # Set to 'twilio' in production

# drf-spectacular
SPECTACULAR_SETTINGS = {
    'TITLE': 'AAfriRide API',
    'DESCRIPTION': 'Backend API for AAfri ride mobile app',
    'VERSION': '1.0.0',
}

# Optional S3 media storage configuration (enable by setting USE_S3=true and AWS_* env vars)
USE_S3 = os.getenv('USE_S3', 'False') == 'True'
if USE_S3:
    INSTALLED_APPS += ['storages']
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', None)
    AWS_QUERYSTRING_AUTH = False
