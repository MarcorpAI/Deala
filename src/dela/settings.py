import dj_database_url
import os

from pathlib import Path
# from delapp.models import User

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
from dotenv import load_dotenv
from datetime import timedelta
from corsheaders.defaults import default_headers

load_dotenv()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!

DEBUG = 'RENDER' not in os.environ


# ALLOWED_HOSTS = ['localhost', '127.0.0.1',  '127.0.0.1:5173', "a32c-105-112-178-95.ngrok-free.app", "fff1-105-112-178-95.ngrok-free.app", "try-deala.shop" ] 

ALLOWED_HOSTS = [
    "mysite-sdvw.onrender.com",  # Your Render domain
    'try-deala.shop',    # Your Vercel frontend domain
    'localhost',
    '127.0.0.1'
]


FRONTEND_URL = "https://try-deala.shop"


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
    "corsheaders",
    'rest_framework_simplejwt',
    
]



SITE_ID = 1




REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}



SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}






MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    'whitenoise.middleware.WhiteNoiseMiddleware',
    "corsheaders.middleware.CorsMiddleware",
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
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'



CORS_ALLOW_HEADERS = list(default_headers) + [
    'ngrok-skip-browser-warning',
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:8000",
    "https://try-deala.shop"
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
    'default': dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
    )
}


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
LEMON_SQUEEZY_REDIRECT_URL = 'https://a32c-105-112-178-95.ngrok-free.app/deala'
LEMON_SQUEEZY_DEFAULT_PLAN_ID = os.getenv('LEMON_SQUEEZY_DEFAULT_PLAN_ID')

LEMON_SQUEEZY_WEBHOOK_SECRET = os.getenv('LEMON_SQUEEZY_WEBHOOK_SECRET')

LEMON_SQUEEZY_API_BASE_URL = "https://api.lemonsqueezy.com/v1/"
LEMON_SQUEEZY_RECEIPT_LINK_URL = "https://a32c-105-112-178-95.ngrok-free.app/deala"
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

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")  # Gmail App password, not your Gmail account password
