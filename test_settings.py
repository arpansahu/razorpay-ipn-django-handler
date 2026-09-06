SECRET_KEY = "test-secret-key"
ROOT_URLCONF = "razorpay_ipn_django_handler.urls"

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "razorpay_ipn_django_handler",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

USE_TZ = True