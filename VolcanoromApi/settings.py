import os
from pathlib import Path
import ssl
import certifi
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-6#_ki_4t1h7ol&hh(v3fh7$#na$35xd%hq=u_f^f$ocai@p^sx'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "corsheaders",
    'rest_framework',
    'accounts',
    'AdminDashboard',
    'SoftwareManagements',
    'drf_spectacular',
    'whitenoise',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'VolcanoromApi.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'VolcanoromApi.wsgi.application'
# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:5173",
# ]
CORS_ALLOW_ALL_ORIGINS = True

# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'umuzylvc_volcanorom',
        'USER': 'umuzylvc_admin',
        'PASSWORD': 'Ngoga@1patrick',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
AUTH_USER_MODEL = 'accounts.User'

MAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST = "mail.privateemail.com"          # Namecheap SMTP server
EMAIL_PORT = 465                          # SSL port
EMAIL_USE_TLS = False                     # disable TLS
EMAIL_USE_SSL = True                      # enable SSL for port 465

EMAIL_HOST_USER = "no-reply@mynextmarket.com"
EMAIL_HOST_PASSWORD = "Ngoga@1patrick"

DEFAULT_FROM_EMAIL = "Volcanorom <no-reply@mynextmarket.com>"
# EMAIL_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'housemajorrwanda@gmail.com'
# EMAIL_HOST_PASSWORD = 'kpxr khxv wjoy hprg'  # NOT your Gmail password!
# DEFAULT_FROM_EMAIL = 'House Major <housemajorrwanda@gmail.com>'
CRYPTOMUS_API_KEY = "YOUR_API_KEY"
CRYPTOMUS_MERCHANT_ID = "YOUR_MERCHANT_ID"
CRYPTOMUS_URL = "https://api.cryptomus.com/v1/payment"
# Documentation Settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'Software Download API',
    'DESCRIPTION': 'API documentation for software download platform with wallet and deposits',
    'VERSION': '1.0.0',
}