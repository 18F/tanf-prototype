"""
Django settings for tanf project.

Generated by 'django-admin startproject' using Django 2.2.4.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os
import random
import string
import json
import jwcrypto.jwk as jwk
import logging


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
def random_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))


if 'SECRET_KEY' in os.environ:
    SECRET_KEY = os.environ['SECRET_KEY']
else:
    SECRET_KEY = random_generator(100)


# SECURITY WARNING: don't run with debug turned on in production!
if 'DEBUG' in os.environ:
    DEBUG = os.environ['DEBUG']
else:
    DEBUG = False

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'upload.apps.UploadConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'djangooidc',
    'background_task',
    'users',
]

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

ROOT_URLCONF = 'tanf.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'tanf/upload/templates'),
        ],
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

WSGI_APPLICATION = 'tanf.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'

# custom user model so we don't have passwords
AUTH_USER_MODEL = 'users.TANFUser'

# oidc client config
if 'NOLOGINGOV' in os.environ:
    print('disabling OIDC auth')
    NOLOGINGOV = True
else:
    NOLOGINGOV = False
    AUTHENTICATION_BACKENDS = [
        'djangooidc.backends.OpenIdConnectBackend'
    ]

# the PEM file here is generated by the deploy script and stored in the env.
priv_key = jwk.JWK.from_pem(bytes(os.environ['JWT_KEY'], "utf-8"))
with open('/tmp/priv_key.jwk', 'w') as f:
    key = json.loads(priv_key.export())
    keyset = {'keys': [key]}
    f.write(json.dumps(keyset))

# Manage users through the admin url
OIDC_CREATE_UNKNOWN_USER = False

# We're disabling dynamic client registration.
OIDC_ALLOW_DYNAMIC_OP = False

# Default OIDC behavoir will be the 'code' workflow
OIDC_DEFAULT_BEHAVIOUR = {
    "response_type": "code",
    "scope": ["openid", "email", "first_name", "last_name"],
}

# conditionally set which URI to go to
if 'VCAP_APPLICATION' in os.environ:
    appjson = os.environ['VCAP_APPLICATION']
    appinfo = json.loads(appjson)
    appuri = 'https://' + appinfo['application_uris'][0] + '/openid/callback/login/'
else:
    appuri = 'http://localhost:8000/openid/callback/login/'

# Set up our OIDC providers
OIDC_PROVIDERS = {
    "logingov": {
        "srv_discovery_url": "https://secure.login.gov/",
        "behaviour": OIDC_DEFAULT_BEHAVIOUR,
        "client_registration": {
            "client_id": os.environ['OIDC_RP_CLIENT_ID'],
            "redirect_uris": [appuri],
            'token_endpoint_auth_method': ['private_key_jwt'],
            "enc_kid": priv_key.key_id,
            "keyset_jwk_file": "file:///tmp/priv_key.jwk",
            'acr_value': 'http://idmanagement.gov/ns/assurance/loa/1',
        }
    },
    "logingov_test": {
        "srv_discovery_url": "https://idp.int.identitysandbox.gov/",
        "behaviour": OIDC_DEFAULT_BEHAVIOUR,
        "client_registration": {
            "client_id": os.environ['OIDC_RP_CLIENT_ID'],
            "redirect_uris": [appuri],
            'token_endpoint_auth_method': ['private_key_jwt'],
            "enc_kid": priv_key.key_id,
            "keyset_jwk_file": "file:///tmp/priv_key.jwk",
            'acr_value': 'http://idmanagement.gov/ns/assurance/loa/1',
        }
    }
}

# configure things set up by cloudfoundry
if 'VCAP_SERVICES' in os.environ:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    servicejson = os.environ['VCAP_SERVICES']
    services = json.loads(servicejson)
    AWS_STORAGE_BUCKET_NAME = services['s3'][0]['credentials']['bucket']
    AWS_S3_REGION_NAME = services['s3'][0]['credentials']['region']
    AWS_ACCESS_KEY_ID = services['s3'][0]['credentials']['access_key_id']
    AWS_SECRET_ACCESS_KEY = services['s3'][0]['credentials']['secret_access_key']
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': services['aws-rds'][0]['credentials']['db_name'],
            'USER': services['aws-rds'][0]['credentials']['username'],
            'PASSWORD': services['aws-rds'][0]['credentials']['password'],
            'HOST': services['aws-rds'][0]['credentials']['host'],
            'PORT': services['aws-rds'][0]['credentials']['port'],
        }
    }
    STATIC_ROOT = os.path.join(BASE_DIR, "static/")

    if 'NOLOGINGOV' not in os.environ:
        # configure the OIDC provider
        # When this gets to production, we will probably want to set this to 'logingov'
        LOGIN_URL = '/openid/openid/logingov_test'
else:
    # we are in local development mode
    MEDIA_ROOT = '/tmp/tanf'

    if 'NOLOGINGOV' not in os.environ:
        # configure the OIDC provider
        # When this gets to production, we will probably want to set this to 'logingov'
        LOGIN_URL = '/openid/openid/logingov_test'


# Use this to turn on lots of debugging output
if 'DEBUG' in os.environ:
    logging.basicConfig(level=logging.DEBUG)
