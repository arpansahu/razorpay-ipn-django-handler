# Razorpay IPN Django Handler

A Django app to handle Razorpay IPN webhook notifications with built-in signal support for tracking payment and subscription events.

## Installation

Install the package using pip:

```bash
pip install razorpay-ipn-django-handler
```

## Configuration

1. **Add to `INSTALLED_APPS`:**

   In your Django settings file (`settings.py`), add `razorpay_ipn_django_handler` to `INSTALLED_APPS`:

   ```python
   INSTALLED_APPS = [
       ...
       "razorpay_ipn_django_handler",
   ]
   ```

2. **Add URL configuration:**

   In your main `urls.py`, include the app’s URL configuration to handle Razorpay webhook notifications:

   ```python
   from django.urls import path, include

   urlpatterns = [
       ...
       path("payment/razorpay/", include("razorpay_ipn_django_handler.urls")),
   ]
   ```

   If your server is running on `testing.com`, then webhook notifications will be processed at the URL: `https://testing.com/payment/razorpay/webhook/`

   **Note**: The `"payment/razorpay/"` part of the URL is customizable to suit your needs.

3. **Configure Razorpay Environment Variables:**

   Add your Razorpay credentials to `settings.py` using the following environment variables. Replace the placeholder values with your actual credentials from the Razorpay Dashboard:

   ```python
   RAZORPAY_WEBHOOK_SECRET = "your_webhook_secret_here"  # Check your Razorpay Dashboard for this secret
   RAZORPAY_API_KEY = "your_api_key_here"  # Check your Razorpay Dashboard for your API key
   RAZORPAY_API_SECRET = "your_api_secret_here"  # Check your Razorpay Dashboard for your API secret
   ```

4. **Run Migrations:**

   Run migrations to create the necessary database tables for tracking IPN events:

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

## Signal Setup

You can listen for valid and invalid IPN events using signals provided by `razorpay_ipn_django_handler`. Here’s how to set up signal handlers:

1. **Import the signals and register handlers** in one of your Django app files, such as `signals.py`:

   ```python
   from django.dispatch import receiver
   from razorpay_ipn_django_handler.signals import valid_razorpay_ipn_received, invalid_razorpay_ipn_received
   from razorpay_ipn_django_handler.models import RazorpayIPN

   # Handle valid IPN events
   @receiver(valid_razorpay_ipn_received)
   def handle_valid_ipn(sender, instance, **kwargs):
       # `instance` provides the Razorpay IPN object with event data
       print("Received valid IPN event:", instance.event)

   # Handle invalid IPN events
   @receiver(invalid_razorpay_ipn_received)
   def handle_invalid_ipn(sender, **kwargs):
       print("Invalid IPN received")
       # Log or handle invalid IPN events
   ```

   Here, `instance` is the `RazorpayIPN` object containing event data, which you can use to access information such as `event`, `payment_id`, `subscription_id`, and other IPN-related details.
