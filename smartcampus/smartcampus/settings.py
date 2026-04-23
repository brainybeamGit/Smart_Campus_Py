import os
from pathlib import Path

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: Isse secret rakhna bhai!
SECRET_KEY = 'django-insecure-)e!xj_mj^i#8$!^wnti9wi5#x_r03fk75%($dgub$t6e8-c%jg'

# SECURITY WARNING: Deploy karte waqt ise False kar dena
DEBUG = True

# Yahan '*' ka matlab hai koi bhi isse access kar sakta hai (Testing ke liye best hai)
ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'campus', # Tumhari main app
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'smartcampus.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], # Templates folder ka rasta
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

WSGI_APPLICATION = 'smartcampus.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata' # Bhai India ka time set kar diya hai
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"] # Static folder ka rasta
STATIC_ROOT = BASE_DIR / "staticfiles" # Deploy ke waqt kaam aayega

# Media files (QR Codes aur Student Photos ke liye)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Email Settings (Ekdum Perfect) ---
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_SSL_CONTEXT = None 
EMAIL_HOST_USER = 'bhagyeshpatel2022@gmail.com'
EMAIL_HOST_PASSWORD = 'tose xslj jbuz lgoj' # Bhai ye password kisi ko dikhana mat!

# --- Login/Logout Redirects ---
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'master_admin' # Login ke baad seedha dashboard par
LOGOUT_REDIRECT_URL = 'login'

# settings.py mein purani EMAIL settings ko comment karke ye daal do:
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'