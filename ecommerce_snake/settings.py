"""
Django settings for ecommerce_snake project.
"""

from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False #True #False

# CONFIGURACIÓN DE HOSTS Y NGROK (AJUSTE DINÁMICO)
ALLOWED_HOSTS = ['snake-shop.fly.dev', 'localhost', '127.0.0.1',] #'tu-app.onrender.com', '.ngrok-free.app', '.ngrok-free.dev'

# USAR COMODINES (*) para que funcione con cualquier túnel de ngrok activo
CSRF_TRUSTED_ORIGINS = [
    # 'https://tu-app.onrender.com',
    'https://snake-shop.fly.dev',
    # 'https://*.ngrok-free.app',
    # 'https://*.ngrok-free.dev',
    'http://127.0.0.1:8000',
    'http://localhost:8000',
]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'snake_shop',
    'django_extensions',
    'widget_tweaks',
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

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

ROOT_URLCONF = 'ecommerce_snake.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'snake_shop.context_processors.cart_counter',
            ],
        },
    },
]

WSGI_APPLICATION = 'ecommerce_snake.wsgi.application'


#Database
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
# }
DATABASES = {
    # 'default': {
    #     'ENGINE': 'django.db.backends.postgresql',
    #     'NAME': os.environ.get('DB_NAME'),
    #     'USER': os.environ.get('DB_USER'),
    #     'PASSWORD': os.environ.get('DB_PASSWORD'),
    #     'HOST': os.environ.get('DB_HOST'),
    #     'PORT': os.environ.get('DB_PORT'), # , '5432'
    # },
    'default': dj_database_url.config(
        default=os.getenv("DATABASE_URL"),
        conn_max_age=600,
        ssl_require=False
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
LANGUAGE_CODE = 'es'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'snake_shop'/ 'static',
    # os.path.join(BASE_DIR, 'snake_shop', 'static'),
]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuración de Sesión y Carrito
CART_SESSION_ID = 'cart'
LOGIN_REDIRECT_URL = '/'

# CONFIGURACIÓN DE EMAIL PARA DESARROLLO (Emails por consola)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'soporte@snakeshop.com'

# CONFIGURACIÓN DE PASARELA DE PAGOS FLOW
# Credenciales para ambiente Sandbox

FLOW_API_KEY = os.environ.get('FLOW_API_KEY')
FLOW_SECRET_KEY = os.environ.get('FLOW_SECRET_KEY')
FLOW_URL_BASE = os.environ.get('FLOW_URL_BASE', 'https://sandbox.flow.cl/api')



#redireccionar al inicio swapués de finalizar el pago
LOGIN_URL = 'login'