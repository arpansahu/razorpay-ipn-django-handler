import uuid
from django.db import models
from django.utils import timezone
from .signals import valid_razorpay_ipn_received, invalid_razorpay_ipn_received
import logging
import json
import hmac
import hashlib
from django.conf import settings


# Create your models here.
class BillingAddress(models.Model):
    """
    Represents the billing address for a customer.
    """
    # Unique identifier for the refund, using UUID as primary key
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique identifier for the Payment")

    id = models.CharField(max_length=255, help_text="Unique identifier for the billing address.")
    primary = models.BooleanField(default=False, help_text="Indicates if this is the primary billing address.")
    line1 = models.CharField(max_length=255, help_text="First line of the address.")
    line2 = models.CharField(max_length=255, null=True, blank=True, help_text="Second line of the address.")
    city = models.CharField(max_length=100, help_text="City of the address.")
    zipcode = models.CharField(max_length=20, help_text="Zip code of the address.")
    state = models.CharField(max_length=100, help_text="State of the address.")
    country = models.CharField(max_length=100, help_text="Country of the address.")


class ShippingAddress(models.Model):
    """
    Represents the shipping address for a customer.
    """
    # Unique identifier for the refund, using UUID as primary key
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique identifier for the Payment")

    id = models.CharField(max_length=255, help_text="Unique identifier for the shipping address.")
    primary = models.BooleanField(default=False, help_text="Indicates if this is the primary shipping address.")
    line1 = models.CharField(max_length=255, help_text="First line of the address.")
    line2 = models.CharField(max_length=255, null=True, blank=True, help_text="Second line of the address.")
    city = models.CharField(max_length=100, help_text="City of the address.")
    zipcode = models.CharField(max_length=20, help_text="Zip code of the address.")
    state = models.CharField(max_length=100, help_text="State of the address.")
    country = models.CharField(max_length=100, help_text="Country of the address.")

class CustomerDetails(models.Model):
    """
    Represents details of the customer associated with the invoice.
    """
    # Unique identifier for the refund, using UUID as primary key
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique identifier for the Payment")

    id = models.CharField(max_length=255, null=True, blank=True, help_text="Unique identifier of the customer.")
    name = models.CharField(max_length=50, null=True, blank=True, help_text="Customer's name.")
    email = models.EmailField(max_length=64, null=True, blank=True, help_text="Customer's email address.")
    contact = models.CharField(max_length=15, null=True, blank=True, help_text="Customer's contact number.")
    billing_address = models.OneToOneField(BillingAddress, on_delete=models.CASCADE, null=True, blank=True, help_text="Billing address of the customer.")
    shipping_address = models.OneToOneField(ShippingAddress, on_delete=models.CASCADE, null=True, blank=True, help_text="Shipping address of the customer.")


class Item(models.Model):
    """
    Represents an item that can be billed in the invoice.
    """
    # Unique identifier for the refund, using UUID as primary key
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique identifier for the Payment")

    id = models.CharField(max_length=255, help_text="Unique identifier for the item.")
    name = models.CharField(max_length=255, help_text="Name of the item.")
    description = models.TextField(null=True, blank=True, help_text="Description of the item.")
    amount = models.IntegerField(help_text="Price of the item.")
    unit_amount = models.IntegerField(null=True, blank=True, help_text="Unit amount of the item.")
    currency = models.CharField(max_length=10, default="INR", help_text="Currency for the item.")
    type = models.CharField(max_length=50, default="invoice", help_text="Type of the item.")
    unit = models.CharField(max_length=50, null=True, blank=True, help_text="Unit of the item.")
    tax_inclusive = models.BooleanField(default=False, help_text="Indicates if the price is tax-inclusive.")
    hsn_code = models.CharField(max_length=50, null=True, blank=True, help_text="HSN code for the item.")
    sac_code = models.CharField(max_length=50, null=True, blank=True, help_text="SAC code for the item.")
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Tax rate for the item.")


class LineItem(models.Model):
    """
    Represents a line item in an invoice.
    """
    # Unique identifier for the refund, using UUID as primary key
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique identifier for the Payment")

    id = models.CharField(max_length=255, help_text="Unique identifier for the line item.")
    item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, blank=True, help_text="Reference to the billed item.")
    name = models.CharField(max_length=255, help_text="Name of the line item.")
    description = models.TextField(null=True, blank=True, help_text="Description of the line item.")
    amount = models.IntegerField(help_text="Total price of the line item.")
    quantity = models.IntegerField(default=1, help_text="Quantity of the line item.")

class Invoice(models.Model):
    """
    Represents an invoice, which can include multiple line items.
    """
    # Unique identifier for the refund, using UUID as primary key
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique identifier for the Payment")

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('issued', 'Issued'),
        ('partially_paid', 'Partially Paid'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('deleted', 'Deleted'),
    ]

    SMS_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
    ]

    EMAIL_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
    ]
    
    id = models.CharField(max_length=255, help_text="Invoice ID.")
    receipt = models.CharField(max_length=255, null=True, blank=True, help_text="Invoice receipt number.")
    number = models.CharField(max_length=255, null=True, blank=True, help_text="Invoice number.")
    customer_id = models.CharField(max_length=255, null=True, blank=True, help_text="Customer ID associated with the invoice.")
    customer_details = models.OneToOneField(CustomerDetails, on_delete=models.CASCADE, null=True, blank=True, help_text="Customer details for the invoice.")
    order_id = models.CharField(max_length=255, null=True, blank=True, help_text="Order ID associated with the invoice.")
    subscription_id = models.CharField(max_length=255, null=True, blank=True, help_text="Subscription ID associated with the invoice.")
    payment_id = models.CharField(max_length=255, null=True, blank=True, help_text="Payment ID associated with the invoice.")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, null=True, blank=True, help_text="Status of the invoice.")
    expire_by = models.DateTimeField(null=True, blank=True, help_text="Invoice expiration timestamp.")
    issued_at = models.DateTimeField(null=True, blank=True, help_text="Invoice issue timestamp.")
    paid_at = models.DateTimeField(null=True, blank=True, help_text="Invoice payment timestamp.")
    cancelled_at = models.DateTimeField(null=True, blank=True, help_text="Invoice cancellation timestamp.")
    expired_at = models.DateTimeField(null=True, blank=True, help_text="Invoice expiration timestamp.")
    sms_status = models.CharField(max_length=50, choices=SMS_STATUS_CHOICES, null=True, blank=True, help_text="SMS status.")
    email_status = models.CharField(max_length=50, choices=EMAIL_STATUS_CHOICES, null=True, blank=True, help_text="Email status.")
    date = models.DateTimeField(null=True, blank=True, help_text="Invoice date.")
    terms = models.TextField(null=True, blank=True, help_text="Invoice terms.")
    partial_payment = models.BooleanField(default=False, help_text="Indicates if partial payment is allowed.")
    gross_amount = models.IntegerField(null=True, blank=True, help_text="Gross amount of the invoice.")
    tax_amount = models.IntegerField(null=True, blank=True, help_text="Tax amount on the invoice.")
    taxable_amount = models.IntegerField(null=True, blank=True, help_text="Taxable amount.")
    amount = models.IntegerField(null=True, blank=True, help_text="Total amount.")
    amount_paid = models.IntegerField(null=True, blank=True, help_text="Amount paid.")
    amount_due = models.IntegerField(null=True, blank=True, help_text="Amount due.")
    currency = models.CharField(max_length=10, default="INR", help_text="Currency for the invoice.")
    description = models.TextField(null=True, blank=True, help_text="Description of the invoice.")
    notes = models.JSONField(null=True, blank=True, help_text="Additional notes.")
    line_items = models.ManyToManyField(LineItem, related_name="invoices", blank=True, help_text="Line items in the invoice.")



class UPIDetails(models.Model):
    """
    Represents UPI details for a payment.
    """
    # Unique identifier for the refund, using UUID as primary key
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique identifier for the Payment")

    payer_account_type_choices = [
        ('bank_account', 'Bank Account'),
        ('credit_card', 'Credit Card'),
        ('wallet', 'Wallet'),
    ]

    vpa = models.CharField(max_length=255, null=True, blank=True, help_text="Customer's VPA for the UPI payment")
    flow = models.CharField(max_length=50, null=True, blank=True, help_text="Type of UPI flow, e.g., 'in_app'")
    payer_account_type = models.CharField(max_length=20, choices=payer_account_type_choices, null=True, blank=True, help_text="Type of payer account for UPI payment")


class CardDetails(models.Model):
    """
    Represents card details for a payment.
    """
    # Unique identifier for the refund, using UUID as primary key
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique identifier for the Payment")

    network_choices = [
        ('American Express', 'American Express'),
        ('Diners Club', 'Diners Club'),
        ('Maestro', 'Maestro'),
        ('MasterCard', 'MasterCard'),
        ('RuPay', 'RuPay'),
        ('Unknown', 'Unknown'),
        ('Visa', 'Visa'),
    ]
    card_type_choices = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
        ('prepaid', 'Prepaid'),
        ('unknown', 'Unknown'),
    ]
    sub_type_choices = [
        ('customer', 'Customer'),
        ('business', 'Business'),
    ]
    
    card_id = models.CharField(max_length=255, null=True, blank=True, help_text="ID of the card used")
    name = models.CharField(max_length=255, null=True, blank=True, help_text="Name of the cardholder")
    last4 = models.CharField(max_length=4, null=True, blank=True, help_text="Last 4 digits of the card number")
    network = models.CharField(max_length=50, choices=network_choices, null=True, blank=True)
    card_type = models.CharField(max_length=10, choices=card_type_choices, null=True, blank=True)
    sub_type = models.CharField(max_length=10, choices=sub_type_choices, null=True, blank=True)
    international = models.BooleanField(default=False, help_text="Indicates if the card is international")
    emi = models.BooleanField(default=False, help_text="Indicates if the card supports EMI payment")
    issuer = models.CharField(max_length=255, null=True, blank=True, help_text="Issuer bank of the card")
    token_iin = models.CharField(max_length=255, null=True, blank=True, help_text="Card token identifier (IIN)")




class Payment(models.Model):
    """
    Represents the details of a payment.
    """

    # Unique identifier for the refund, using UUID as primary key
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique identifier for the Payment")


    # Existing fields and choices remain unchanged
    status_choices = [
        ('created', 'Created'),
        ('authorized', 'Authorized'),
        ('captured', 'Captured'),
        ('refunded', 'Refunded'),
        ('failed', 'Failed'),
    ]
    method_choices = [
        ('card', 'Card'),
        ('netbanking', 'Net Banking'),
        ('wallet', 'Wallet'),
        ('emi', 'EMI'),
        ('upi', 'UPI'),
    ]
    refund_status_choices = [
        (None, 'None'),
        ('partial', 'Partial'),
        ('full', 'Full'),
    ]

    id = models.CharField(max_length=255, help_text="Payment ID associated with the event")
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Total amount for the payment")
    currency = models.CharField(max_length=10, null=True, blank=True, help_text="Currency for the payment amount")
    base_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Base amount before adjustments")
    status = models.CharField(max_length=10, choices=status_choices, null=True, blank=True)
    method = models.CharField(max_length=20, choices=method_choices, null=True, blank=True)
    captured = models.BooleanField(default=False, help_text="Whether the payment was captured")
    amount_refunded = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    amount_transferred = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    refund_status = models.CharField(max_length=10, choices=refund_status_choices, null=True, blank=True, help_text="Refund status: null, partial, or full")
    order_id = models.CharField(max_length=255, null=True, blank=True, help_text="Order ID associated with the payment")
    invoice_id = models.CharField(max_length=255, null=True, blank=True, help_text="Invoice ID associated with the payment")
    international = models.BooleanField(default=False)
    token_id = models.CharField(max_length=255, null=True, blank=True, help_text="Token ID associated with the payment")

    # New fields added based on the JSON payload
    vpa = models.CharField(max_length=255, null=True, blank=True, help_text="UPI VPA for UPI payments")
    email = models.EmailField(null=True, blank=True, help_text="Customer email associated with the payment")
    contact = models.CharField(max_length=15, null=True, blank=True, help_text="Customer contact number")
    bank = models.CharField(max_length=255, null=True, blank=True, help_text="Bank name associated with the payment")
    wallet = models.CharField(max_length=255, null=True, blank=True, help_text="Wallet name used for payment")
    reward = models.CharField(max_length=255, null=True, blank=True, help_text="Reward details, if any")    
    customer_id = models.CharField(max_length=255, null=True, blank=True, help_text="Customer ID for the subscription")

    # Relationships
    upi_details = models.OneToOneField(UPIDetails, on_delete=models.SET_NULL, null=True, blank=True, help_text="UPI details for the payment")
    card_details = models.OneToOneField(CardDetails, on_delete=models.SET_NULL, null=True, blank=True, help_text="Card details for the payment")
    acquirer_data = models.JSONField(null=True, blank=True, help_text="Acquirer data for the payment")

    # Financial and Additional Metadata
    fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notes = models.JSONField(null=True, blank=True)
    error_code = models.CharField(max_length=50, null=True, blank=True)
    error_description = models.TextField(null=True, blank=True)
    error_source = models.CharField(max_length=255, null=True, blank=True)
    error_step = models.CharField(max_length=255, null=True, blank=True)
    error_reason = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)



class Subscription(models.Model):
    # Unique identifier for the refund, using UUID as primary key
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique identifier for the Subscription")


    """
    Represents subscription details with specific choices and relevant fields.
    """

    # Choices for fields with fixed options
    CUSTOMER_NOTIFY_CHOICES = [
        (True, 'Razorpay handles communication'),
        (False, 'Business handles communication'),
    ]
    HAS_SCHEDULED_CHANGES_CHOICES = [
        (True, 'Has scheduled changes'),
        (False, 'No scheduled changes'),
    ]
    SCHEDULE_CHANGE_AT_CHOICES = [
        ('now', 'Now'),
        ('cycle_end', 'Cycle End'),
    ]
    SUBSCRIPTION_STATUS_CHOICES = [
        ('created', 'Created'),
        ('authenticated', 'Authenticated'),
        ('active', 'Active'),
        ('pending', 'Pending'),
        ('halted', 'Halted'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
    ]

    # Subscription Fields
    id = models.CharField(max_length=255, help_text="Subscription ID for associated subscription events")
    plan_id = models.CharField(max_length=255, null=True, blank=True, help_text="Plan ID associated with the subscription")
    customer_id = models.CharField(max_length=255, null=True, blank=True, help_text="Customer ID for the subscription")
    quantity = models.IntegerField(null=True, blank=True, help_text="Quantity in the subscription")
    total_count = models.IntegerField(null=True, blank=True, help_text="Total count of subscription cycles")
    paid_count = models.IntegerField(null=True, blank=True, help_text="Paid cycles count of the subscription")
    remaining_count = models.IntegerField(null=True, blank=True, help_text="Remaining count of subscription cycles")

    current_start = models.DateTimeField(null=True, blank=True, help_text="Current cycle start time")
    current_end = models.DateTimeField(null=True, blank=True, help_text="Current cycle end time")
    start_at = models.DateTimeField(null=True, blank=True, help_text="Subscription start time")
    end_at = models.DateTimeField(null=True, blank=True, help_text="Subscription end time")
    charge_at = models.DateTimeField(null=True, blank=True, help_text="Next charge time")
    auth_attempts = models.IntegerField(null=True, blank=True, help_text="Number of authorization attempts")
    expire_by = models.DateTimeField(null=True, blank=True, help_text="Subscription expiration time")

    # Choice fields with pre-defined options
    customer_notify = models.BooleanField(
        choices=CUSTOMER_NOTIFY_CHOICES,
        default=True,
        help_text="Indicates whether communication to the customer is handled by the business or Razorpay",
    )
    has_scheduled_changes = models.BooleanField(
        choices=HAS_SCHEDULED_CHANGES_CHOICES,
        default=False,
        help_text="Indicates if the subscription has any scheduled changes",
    )
    schedule_change_at = models.CharField(
        max_length=10,
        choices=SCHEDULE_CHANGE_AT_CHOICES,
        default='now',
        help_text="When the subscription should be updated",
    )
    status = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_STATUS_CHOICES,
        default='created',
        help_text="Status of the subscription",
    )

    # Additional Metadata Fields
    source = models.CharField(max_length=50, null=True, blank=True, help_text="Source of subscription creation")
    payment_method = models.CharField(max_length=50, null=True, blank=True, help_text="Payment method for the subscription")
    offer_id = models.CharField(max_length=255, null=True, blank=True, help_text="Offer ID if applicable")
    notes = models.JSONField(null=True, blank=True, help_text="JSON data for any custom notes specific to the subscription")

    ended_at = models.DateTimeField(null=True, blank=True, help_text="Subscription end timestamp, if any")
    created_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when subscription was created")
    change_scheduled_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when the subscription change is scheduled")


class Order(models.Model):
    """
    Represents order details, including status, payment amounts, and partial payment support.
    """
    # Unique identifier for the refund, using UUID as primary key
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique identifier for the Order")

    # Order Status Choices
    ORDER_STATUS_CHOICES = [
        ('created', 'Created'),
        ('attempted', 'Attempted'),
        ('paid', 'Paid'),
    ]
    
    # Core Order Fields
    id = models.CharField(max_length=255, help_text="Unique identifier of the order")
    amount = models.IntegerField(help_text="Payment amount in the smallest currency sub-unit")
    partial_payment = models.BooleanField(default=False, help_text="Indicates whether the customer can make a partial payment")
    amount_paid = models.IntegerField(null=True, blank=True, help_text="The amount paid against the order")
    amount_due = models.IntegerField(null=True, blank=True, help_text="The amount pending against the order")
    currency = models.CharField(max_length=3, help_text="ISO code for the currency in which you want to accept the payment")

    # Optional Order Information
    receipt = models.CharField(max_length=40, null=True, blank=True, help_text="Receipt number that corresponds to this order. Must be unique")
    status = models.CharField(
        max_length=10,
        choices=ORDER_STATUS_CHOICES,
        default='created',
        help_text="The status of the order"
    )
    attempts = models.IntegerField(null=True, blank=True, help_text="The number of payment attempts, successful and failed, against this order")
    created_at = models.DateTimeField(null=True, blank=True, help_text="Unix timestamp when this order was created")

    # JSON Field for Custom Notes
    notes = models.JSONField(null=True, blank=True, help_text="Key-value pairs to store additional information about the order. Max 15 pairs")
    offer_id = models.CharField(max_length=255, null=True, blank=True, help_text="Offer ID associated with the order")


class Refund(models.Model):
    """
    Represents a refund object for a payment.
    """
    # Unique identifier for the refund, using UUID as primary key
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique identifier for the refund")

    # Core Refund Fields
    id = models.CharField(max_length=255, help_text="The unique identifier of the refund.")
    amount = models.IntegerField(help_text="The amount to be refunded in the smallest unit of currency.")
    currency = models.CharField(max_length=10, help_text="The currency of the payment amount for which the refund is initiated.")
    payment_id = models.CharField(max_length=255, help_text="The unique identifier of the payment for which the refund is initiated.")

    # Speed and Processing Information
    speed = models.CharField(
        max_length=10,
        choices=[
            ('normal', 'Normal'),
            ('optimum', 'Optimum')
        ],
        help_text="Speed at which the refund is to be processed."
    )
    created_at = models.DateTimeField(help_text="Unix timestamp at which the refund was created.")
    batch_id = models.CharField(max_length=255, null=True, blank=True, help_text="If refund created as part of a batch upload.")
    receipt = models.CharField(max_length=255, null=True, blank=True, help_text="A unique identifier for internal reference.")

    # Status Information
    status = models.CharField(
        max_length=10,
        choices=[
            ('pending', 'Pending'),
            ('processed', 'Processed'),
            ('failed', 'Failed')
        ],
        help_text="Indicates the state of the refund."
    )
    speed_requested = models.CharField(
        max_length=10,
        choices=[
            ('normal', 'Normal'),
            ('optimum', 'Optimum')
        ],
        null=True,
        blank=True,
        help_text="Processing mode of the refund as seen in the refund response."
    )
    speed_processed = models.CharField(
        max_length=10,
        choices=[
            ('instant', 'Instant'),
            ('normal', 'Normal')
        ],
        null=True,
        blank=True,
        help_text="Describes the mode used to process a refund in the response."
    )

    # Additional Information
    notes = models.JSONField(null=True, blank=True, help_text="Key-value store for storing reference data.")
    acquirer_data = models.JSONField(null=True, blank=True, help_text="Acquirer data for the payment")


class RazorpayWebhook(models.Model):
    """
    Base model representing a Razorpay Webhook event.
    """

    # Core Event Details
    # Event Type Choices
    EVENT_TYPE_CHOICES = [
        ('refund.created', 'Refund Created'),
        ('refund.processed', 'Refund Processed'),
        ('payment.authorized', 'Payment Authorized'),
        ('payment.captured', 'Payment Captured'),
        ('order.paid', 'Order Paid'),
        ('invoice.paid', 'Invoice Paid'),
        ('subscription.authenticated', 'Subscription Authenticated'),
        ('subscription.charged', 'Subscription Charged'),
        ('subscription.activated', 'Subscription Activated'),
        ('subscription.cancelled', 'Subscription Cancelled'),
        ('subscription.paused', 'Subscription Paused'),
    ]
    # Unique identifier for the refund, using UUID as primary key
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique identifier for the Payment")

    event_id = models.CharField(max_length=255, help_text="Unique identifier for the Razorpay event")
    event_type = models.CharField(max_length=100, choices=EVENT_TYPE_CHOICES, help_text="Type of event received from Razorpay")
    account_id = models.CharField(max_length=255, help_text="Razorpay Account ID related to the event")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the webhook was created")  # New field

    # Related Models
    payment = models.OneToOneField('Payment', on_delete=models.SET_NULL, null=True, blank=True, help_text="Related Payment details")
    subscription = models.OneToOneField('Subscription', on_delete=models.SET_NULL, null=True, blank=True, help_text="Related Subscription details")
    order = models.OneToOneField('Order', on_delete=models.SET_NULL, null=True, blank=True, help_text="Related Order details")
    invoice = models.OneToOneField('Invoice', on_delete=models.SET_NULL, null=True, blank=True, help_text="Related Invoice details")
    refund = models.OneToOneField('Refund', on_delete=models.SET_NULL, null=True, blank=True, help_text="Related Refund details")

    # Status for processing
    processed = models.BooleanField(default=False, help_text="Whether the webhook event has been processed")


class RazorpayIPN(RazorpayWebhook):
    """
    Model for handling and storing Razorpay IPN events, inheriting from RazorpayWebhook.
    """
    
    payload = models.JSONField(help_text="Raw event data payload from Razorpay")
    signature_verified = models.BooleanField(default=False, help_text="Indicates if the IPN signature was verified")

    class Meta:
        verbose_name = "Razorpay IPN"
        verbose_name_plural = "Razorpay IPNs"

    def verify_signature(self, body, signature):
        """
        Verifies the signature using Razorpay's secret key.
        """
        try:
            generated_signature = hmac.new(
                settings.RAZORPAY_WEBHOOK_SECRET.encode(),
                body.encode(),
                hashlib.sha256
            ).hexdigest()
            self.signature_verified = hmac.compare_digest(generated_signature, signature)
            return self.signature_verified
        except Exception as e:
            logger.error(f"Error verifying Razorpay signature: {e}")
            return False