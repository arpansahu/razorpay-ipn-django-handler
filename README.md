
# Razorpay IPN Django Handler

A Django app for handling Razorpay Instant Payment Notification (IPN) webhook events, designed to manage payment, order, and subscription notifications seamlessly with support for signal-based event tracking.

## Features

- Full support for handling Razorpay webhook events
- Built-in models for storing payment, subscription, refund, and other event data
- Signal-based notifications for valid and invalid IPN events
- Signature verification for secure processing

## Installation

Install the package via pip:

```bash
pip install razorpay-ipn-django-handler
```

## Configuration

### Step 1: Add to Installed Apps

In your Django `settings.py`, add `razorpay_ipn_django_handler`:

```python
INSTALLED_APPS = [
    ...,
    "razorpay_ipn_django_handler",
]
```

### Step 2: Configure URLs

In your project’s `urls.py`, include the app’s URL configuration for webhook notifications:

```python
from django.urls import path, include

urlpatterns = [
    ...,
    path("payment/razorpay/", include("razorpay_ipn_django_handler.urls")),
]
```

For example, if your server is `https://yourdomain.com`, Razorpay notifications will be processed at `https://yourdomain.com/payment/razorpay/webhook/`.

> **Note**: Customize the `"payment/razorpay/"` URL to suit your structure if needed.

### Step 3: Set Environment Variables

Add your Razorpay credentials in `settings.py` using environment variables:

```python
RAZORPAY_WEBHOOK_SECRET = "your_webhook_secret_here"
RAZORPAY_API_KEY = "your_api_key_here"
RAZORPAY_API_SECRET = "your_api_secret_here"
```

Replace the placeholders with your actual credentials from the Razorpay Dashboard.

### Step 4: Migrate Database

Run migrations to create the necessary database tables:

```bash
python manage.py makemigrations
python manage.py migrate
```

## Signal Setup

The app provides signals for handling valid and invalid IPN events, allowing custom processing based on event types.

### Setting Up Signal Handlers

In one of your app files, such as `signals.py`, register handlers for IPN events:

```python
from django.dispatch import receiver
from razorpay_ipn_django_handler.signals import valid_razorpay_ipn_received, invalid_razorpay_ipn_received
from razorpay_ipn_django_handler.models import RazorpayIPN

# Handle valid IPN events
@receiver(valid_razorpay_ipn_received)
def handle_valid_ipn(sender, instance, **kwargs):
    print("Received valid IPN event:", instance.event)
    # Process the IPN instance as needed

# Handle invalid IPN events
@receiver(invalid_razorpay_ipn_received)
def handle_invalid_ipn(sender, **kwargs):
    print("Invalid IPN received")
    # Log or handle invalid IPN events
```

Here, `instance` provides a `RazorpayIPN` object containing event data like `event_type`, `payment_id`, and other Razorpay IPN-related information.

## Models Overview

The following models are included to manage event data and related details effectively:

### 1. **RazorpayIPN**

Represents an IPN event with fields to track event type, account ID, signature verification, and related details.

### 2. **Payment**

Tracks payment details including amount, status, method, and optional metadata such as UPI, card, or wallet details.

### 3. **Subscription**

Captures subscription events, including plan ID, quantity, status, schedule changes, and metadata.

### 4. **Refund**

Records refund details, including refund amount, status, batch ID, and additional notes.

### 5. **Order**

Stores order-specific details such as amount, status, receipt number, and custom notes.

> These models make it easier to track Razorpay events, allowing you to link each IPN event to associated payments, subscriptions, refunds, and orders as per your requirements.

## Example Usage

To verify a Razorpay webhook signature, use the `verify_signature` method on a `RazorpayIPN` instance:

```python
ipn_instance = RazorpayIPN.objects.create(payload=payload_data)
signature_valid = ipn_instance.verify_signature(body=request_body, signature=header_signature)
if signature_valid:
    # Process the event
else:
    # Handle invalid signature
```

### Example Event Processing

In your signal handler, you can access the event data for custom processing:

```python
@receiver(valid_razorpay_ipn_received)
def process_payment_event(sender, instance, **kwargs):
    if instance.event_type == 'payment.authorized':
        # Add logic to handle authorized payment events
    elif instance.event_type == 'subscription.activated':
        # Add logic to handle subscription activation
```

## Contributing

We welcome contributions to enhance the functionality of this library. Feel free to open issues, suggest features, or submit pull requests on [GitHub](https://github.com/your-repo).

## License

This project is licensed under the MIT License. See the LICENSE file for more details.

## About the Author

I am [Arpan Sahu], a developer specializing in web development, payment integrations, and more. Feel free to check out my portfolio to learn more about my work:

[Visit My Portfolio](https://arpansahu.me)

If you have any questions or are interested in collaborating, please reach out via my portfolio contact form or directly through [LinkedIn](https://linkedin.com/in/arpansahu).
