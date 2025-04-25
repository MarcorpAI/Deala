print("starting settings file ")

import dj_database_url
import os

from pathlib import Path
# from delapp.models import User

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
from dotenv import load_dotenv
from datetime import timedelta
from corsheaders.defaults import default_headers



load_dotenv(dotenv_path=os.path.join(BASE_DIR, '.env'))


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!

DEBUG = True

# Ensure trailing slashes in URLs
APPEND_SLASH = True

ALLOWED_HOSTS = [
    "mysite-sdvw.onrender.com",  # Your Render domain
    'try-deala.shop',    # Your Vercel frontend domain
    'localhost',
    '127.0.0.1'
]


FRONTEND_URL = "https://www.try-deala.shop"


DATABASE_URL = os.environ.get("DATABASE_URL")


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    'django.contrib.sites',
    
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "delapp",
    "products",
    "corsheaders",
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    
]



SITE_ID = 1



REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
    ),
    'DEFAULT_METADATA_CLASS': None,
}


if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True


    CACHE_MIDDLEWARE_SECONDS = 0
    CACHE_MIDDLEWARE_KEY_PREFIX = ''
    
    # Additional security headers
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True








SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),  # Increased to 7 days
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,  # Changed to True
    'UPDATE_LAST_LOGIN': False,  # Changed to False to prevent login conflicts

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': os.environ.get('SECRET_KEY'),
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    
    'JTI_CLAIM': 'jti',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    # Allow token reuse
    'REUSE_REFRESH_TOKENS': True,  # Add this to allow multiple device login
    
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=60),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=7),  # Match regular refresh lifetime
}




MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    'whitenoise.middleware.WhiteNoiseMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'delapp.middleware.DRFNoCacheMiddleware',
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]



AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]


# For development, you can use console email backend
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'



CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:8000",
    "https://www.try-deala.shop",
    "https://try-deala.shop",
    "https://mysite-sdvw.onrender.com"
]

CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https:\/\/(?:www\.)?try-deala\.shop$",  # Matches both www and non-www
    r"^http:\/\/localhost:[0-9]+$",  # Matches any localhost port
]


CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]






CORS_EXPOSE_HEADERS = [
    'Content-Type',
    'X-CSRFToken',
    'Cache-Control',
    'Pragma',
    'Expires',
]

CORS_ALLOW_HEADERS = list(default_headers) + [
    'cache-control',
    'pragma',
    'expires',
]




CORS_ALLOW_CREDENTIALS = True


CORS_ALLOWED_METHODS = [
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE',
    'OPTIONS'
]







ROOT_URLCONF = "dela.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, 'templates')],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "dela.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": BASE_DIR / "db.sqlite3",
#     }
# }



# Database documentation https://docs.djangoproject.com/en/5.0/ref/settings/#databases

# DATABASES = {
#     'default': dj_database_url.config(
#         # Replace this value with your local database's connection string.
#         default='postgresql://myuser:mypassword@localhost:5432/mydatabase',
#         conn_max_age=600
#     )
# }


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'mydatabase',        # Replace with your database name
        'USER': 'myuser',            # Replace with your database username
        'PASSWORD': 'mypassword',    # Replace with your database password
        'HOST': 'localhost',         # Use 'localhost' for local database
        'PORT': '5432',              # Default PostgreSQL port
    }
}









# DATABASES = {
#     'default': dj_database_url.config(
#         default=DATABASE_URL,
#         conn_max_age=600,
#     )
# }



# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "static/"

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static')
]



if not DEBUG:
    # Tell Django to copy static assets into a path called `staticfiles` (this is specific to Render)
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    # Enable the WhiteNoise storage backend, which compresses static files to reduce disk use
    # and renames the files with unique names for each version to support long-term caching
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"













###### LEMON SQUEEZY CONFIG

LEMON_SQUEEZY_API_KEY = os.getenv('LEMON_SQUEEZY_API_KEY')
LEMON_SQUEEZY_STORE_ID = os.getenv('LEMON_SQUEEZY_STORE_ID')
LEMON_SQUEEZY_REDIRECT_URL = 'https://try-deala.shop/deala'
LEMON_SQUEEZY_DEFAULT_PLAN_ID = os.getenv('LEMON_SQUEEZY_DEFAULT_PLAN_ID')

LEMON_SQUEEZY_WEBHOOK_SECRET = os.getenv('LEMON_SQUEEZY_WEBHOOK_SECRET')

LEMON_SQUEEZY_API_BASE_URL = "https://api.lemonsqueezy.com/v1/"
LEMON_SQUEEZY_RECEIPT_LINK_URL = "https://try-deala.shop/deala"
# LEMON_SQUEEZY_WEBHOOK_SECRET = 



AUTH_USER_MODEL = 'delapp.CustomUser'





### logging

# In your settings.py file



# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'formatters': {
#         'verbose': {
#             'format': '{levelname} {asctime} {module} {message}',
#             'style': '{',
#         },
#         'simple': {
#             'format': '{levelname} {message}',
#             'style': '{',
#         },
#     },
#     'handlers': {
#         'console': {
#             'class': 'logging.StreamHandler',
#             'formatter': 'verbose',
#         },
#     },
#     'loggers': {
#         'django': {
#             'handlers': ['console'],
#             'level': 'DEBUG',
#             'propagate': True,
#         },
#         'delapp': {
#             'handlers': ['console'],
#             'level': 'DEBUG',
#             'propagate': True,
#         },
#     },
# }




# settings.py
# Email Configuration - Place this in one location in your settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_TIMEOUT = 60  # Add this
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.environ.get("EMAIL_HOST_USER")  # Add this


SECURE_SSL_REDIRECT = False # Render provides SSL
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')