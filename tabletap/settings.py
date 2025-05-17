import os
from dotenv import load_dotenv
from urllib.parse import urlparse
load_dotenv()
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-key-for-dev')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*', '.vercel.app']
VERCEL_DEPLOYMENT = os.environ.get('VERCEL_DEPLOYMENT', 'False') == 'True'

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    
    # Third-party apps
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.github',
    'crispy_forms',
    'crispy_bootstrap5',
    
    # Our apps
    'accounts',
    'restaurants',
    'orders',
    'customer',
]

# Auth settings
AUTH_USER_MODEL = 'accounts.User'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Django-allauth settings
SITE_ID = 1
LOGIN_REDIRECT_URL = '/restaurant/dashboard/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'
ACCOUNT_EMAIL_VERIFICATION = 'none'  # Disable email verification for development

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Middleware configuration
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Untuk static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',  # Untuk django-allauth
]

ROOT_URLCONF = 'tabletap.urls'

# Template configuration
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'tabletap.wsgi.application'

# Database configuration with error handling
import os
from urllib.parse import urlparse

# Get database URL securely with fallback
DATABASE_URL = os.environ.get('DATABASE_URL', '')

# Setup database with error handling
if DATABASE_URL:
    try:
        # Parse database URL
        url = urlparse(DATABASE_URL)
        
        # Configure PostgreSQL database
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': url.path[1:],  # Remove leading slash
                'USER': url.username,
                'PASSWORD': url.password,
                'HOST': url.hostname,
                'PORT': url.port or '5432',
                'OPTIONS': {
                    'sslmode': 'require',
                },
            }
        }
        print(f"Database configured: {url.hostname}")
    except Exception as e:
        print(f"Error configuring database: {e}")
        # Fallback to SQLite for safety
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }
else:
    # Development database (SQLite)
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

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
if VERCEL_DEPLOYMENT:
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles_build', 'static')
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media_build', 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# WhiteNoise configuration
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Static files configuration for Vercel
if VERCEL_DEPLOYMENT:
    # Force collectstatic to run during deploy
    if os.environ.get('VERCEL_REBUILD'):
        # This block won't run in the Vercel build, but would locally
        import subprocess
        subprocess.run(['python', 'manage.py', 'collectstatic', '--noinput'])

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'ERROR',
        },
    },
}