"""
Django settings for reporting project.

Generated by 'django-admin startproject' using Django 1.10.5.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '5)!dc%xc6622p!!wa54qaf+$_8v5a29ax04+$b)nc8x@-jtu$_'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# authentication

AUTHENTICATION_BACKENDS = [
]

# Application definition

INSTALLED_APPS = [
    'leave',
    'lpp',
    'reporting',
    'supervisors',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_tables2',
]

APPS_LIST = [
    'leave',
    'lpp',
    'supervisors',
]

APPS_SHORT = {
    'leave': 'Leave',
    'lpp': 'LPP',
    'supervisors': 'Supervisors',
}

APPS_LONG = {
    'leave': 'Annual Leave',
    'lpp': 'Low performing pass-rates',
    'supervisors': 'Live Supervisor Register',
}

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'reporting.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            'reporting/templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'debug': True,
        },
    },
]

# only use TemporaryFileUploadHandler for file uploads
FILE_UPLOAD_HANDLERS = (
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
)

WSGI_APPLICATION = 'reporting.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

# custom database settings?
try:
    import reporting.settings_db
    DATABASES = reporting.settings_db.DATABASES
    print("Using database settings from 'settings_db.py'")
except ImportError:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }
    print("""
        Using default database settings
        Create 'settings_db.py' for custom settings, e.g.:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                'NAME': 'db_name',
                'USER': 'db_user',
                'PASSWORD': 'db_user_password',
                'HOST': '',
                'PORT': 'db_port_number',
            }
        }
        """)


# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    'reporting/static/',
]

# LDAP settings

# custom settings?
try:
    import reporting.settings_ldap
    print("Using settings from 'settings_ldap.py'")
    #INSTALLED_APPS.append('django_python3_ldap')
    #AUTHENTICATION_BACKENDS.append('django_python3_ldap.auth.LDAPBackend')
except ImportError:
    print("""
        Using default LDAP settings
        Create 'settings_ldap.py' for custom settings, see example:"
        https://pythonhosted.org/django-auth-ldap/example.html
        """)

# LPP settings

# custom settings?
try:
    import reporting.settings_lpp
    PERL = reporting.settings_lpp.PERL
    LPP_SCRIPT = reporting.settings_lpp.LPP_SCRIPT
    print("Using settings from 'settings_lpp.py'")
except ImportError:
    PERL = "/usr/bin/perl"
    LPP_SCRIPT = "/usr/local/bin/LPP/pass-rates"
    print("""
        Using default LPP settings
        Create 'settings_lpp.py' for custom settings, e.g.:"
        PERL = "/usr/bin/perl"
        LPP_SCRIPT = "/usr/local/bin/LPP/pass-rates"
        """)

