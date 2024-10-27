# apps.py for the Razorpay IPN Handler app
import logging
from django.apps import AppConfig

class RazorpayIPNHandlerConfig(AppConfig):
    name = 'razorpay_ipn_django_handler'

    def ready(self):
        if not logging.getLogger().hasHandlers():
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
