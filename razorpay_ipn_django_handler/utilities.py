from razorpay_ipn_django_handler.models import (
    Payment, Refund, UPIDetails, CardDetails, Subscription, BillingAddress, 
    ShippingAddress, CustomerDetails, Item, LineItem, Invoice, Order
)
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def make_aware_if_naive(dt):
    """
    Convert a naive datetime to an aware datetime if timezone support is enabled.
    """
    from django.utils import timezone
    if dt and timezone.is_naive(dt):
        return timezone.make_aware(dt)
    return dt

def process_payment_data(payment_data):
    """
    Processes the payment data received in the webhook and creates a Payment instance.
    """
    upi_details_instance = None
    if "upi" in payment_data:
        upi_details_instance = UPIDetails.objects.create(
            vpa=payment_data["upi"].get("vpa"),
            flow=payment_data["upi"].get("flow"),
            payer_account_type=payment_data["upi"].get("payer_account_type"),
        )

    card_details_instance = None
    if "card" in payment_data:
        card_details_instance = CardDetails.objects.create(
            card_id=payment_data["card"].get("id"),
            name=payment_data["card"].get("name"),
            last4=payment_data["card"].get("last4"),
            network=payment_data["card"].get("network"),
            card_type=payment_data["card"].get("type"),
            sub_type=payment_data["card"].get("sub_type"),
            international=payment_data["card"].get("international", False),
            emi=payment_data["card"].get("emi", False),
            issuer=payment_data["card"].get("issuer"),
            token_iin=payment_data["card"].get("token_iin"),
        )

    payment = Payment.objects.create(
        id=payment_data.get("id"),
        amount=payment_data.get("amount"),
        currency=payment_data.get("currency"),
        base_amount=payment_data.get("base_amount"),
        status=payment_data.get("status"),
        method=payment_data.get("method"),
        captured=payment_data.get("captured"),
        amount_refunded=payment_data.get("amount_refunded"),
        amount_transferred=payment_data.get("amount_transferred"),
        refund_status=payment_data.get("refund_status"),
        order_id=payment_data.get("order_id"),
        invoice_id=payment_data.get("invoice_id"),
        international=payment_data.get("international", False),
        token_id=payment_data.get("token_id"),
        vpa=payment_data.get("vpa"),
        email=payment_data.get("email"),
        contact=payment_data.get("contact"),
        bank=payment_data.get("bank"),
        wallet=payment_data.get("wallet"),
        reward=payment_data.get("reward"),
        customer_id=payment_data.get("customer_id"),
        upi_details=upi_details_instance,
        card_details=card_details_instance,
        acquirer_data=payment_data.get("acquirer_data"),
        fee=payment_data.get("fee"),
        tax=payment_data.get("tax"),
        notes=payment_data.get("notes"),
        error_code=payment_data.get("error_code"),
        error_description=payment_data.get("error_description"),
        error_source=payment_data.get("error_source"),
        error_step=payment_data.get("error_step"),
        error_reason=payment_data.get("error_reason"),
        created_at=make_aware_if_naive(datetime.fromtimestamp(payment_data.get("created_at")) if payment_data.get("created_at") else None),
    )

    return payment

def process_refund_data(refund_data):
    refund = Refund.objects.create(
        id=refund_data.get("id"),
        amount=refund_data.get("amount", 0),
        currency=refund_data.get("currency"),
        payment_id=refund_data.get("payment_id"),
        speed=refund_data.get("speed", "normal"),
        created_at=make_aware_if_naive(datetime.fromtimestamp(refund_data.get("created_at")) if refund_data.get("created_at") else None),
        batch_id=refund_data.get("batch_id"),
        receipt=refund_data.get("receipt"),
        status=refund_data.get("status", "pending"),
        speed_requested=refund_data.get("speed_requested"),
        speed_processed=refund_data.get("speed_processed"),
        notes=refund_data.get("notes", {}),
        acquirer_data=refund_data.get("acquirer_data", {}),
    )

    return refund

def process_invoice_data(invoice_data):
    billing_address_instance = None
    if invoice_data.get("customer_details", {}).get("billing_address"):
        billing_address_data = invoice_data["customer_details"]["billing_address"]
        billing_address_instance = BillingAddress.objects.create(
            id=billing_address_data.get("id"),
            primary=billing_address_data.get("primary", False),
            line1=billing_address_data.get("line1"),
            line2=billing_address_data.get("line2"),
            city=billing_address_data.get("city"),
            zipcode=billing_address_data.get("zipcode"),
            state=billing_address_data.get("state"),
            country=billing_address_data.get("country"),
        )

    shipping_address_instance = None
    if invoice_data.get("customer_details", {}).get("shipping_address"):
        shipping_address_data = invoice_data["customer_details"]["shipping_address"]
        shipping_address_instance = ShippingAddress.objects.create(
            id=shipping_address_data.get("id"),
            primary=shipping_address_data.get("primary", False),
            line1=shipping_address_data.get("line1"),
            line2=shipping_address_data.get("line2"),
            city=shipping_address_data.get("city"),
            zipcode=shipping_address_data.get("zipcode"),
            state=shipping_address_data.get("state"),
            country=shipping_address_data.get("country"),
        )

    customer_details_instance = None
    if invoice_data.get("customer_details"):
        customer_data = invoice_data["customer_details"]
        customer_details_instance = CustomerDetails.objects.create(
            id=customer_data.get("id"),
            name=customer_data.get("name"),
            email=customer_data.get("email"),
            contact=customer_data.get("contact"),
            billing_address=billing_address_instance,
            shipping_address=shipping_address_instance,
        )

    line_items_instances = []
    if "line_items" in invoice_data:
        for line_item_data in invoice_data["line_items"]:
            item_instance = Item.objects.create(
                id=line_item_data.get("id"),
                name=line_item_data.get("name"),
                description=line_item_data.get("description"),
                amount=line_item_data.get("amount"),
                unit_amount=line_item_data.get("unit_amount"),
                currency=line_item_data.get("currency"),
                type=line_item_data.get("type"),
                unit=line_item_data.get("unit"),
                tax_inclusive=line_item_data.get("tax_inclusive", False),
                hsn_code=line_item_data.get("hsn_code"),
                sac_code=line_item_data.get("sac_code"),
                tax_rate=line_item_data.get("tax_rate"),
            )

            line_item_instance = LineItem.objects.create(
                id=line_item_data.get("id"),
                item=item_instance,
                name=line_item_data.get("name"),
                description=line_item_data.get("description"),
                amount=line_item_data.get("amount"),
                quantity=line_item_data.get("quantity", 1),
            )
            line_items_instances.append(line_item_instance)

    invoice = Invoice.objects.create(
        id=invoice_data.get("id"),
        receipt=invoice_data.get("receipt"),
        number=invoice_data.get("invoice_number"),
        customer_id=invoice_data.get("customer_id"),
        customer_details=customer_details_instance,
        order_id=invoice_data.get("order_id"),
        subscription_id=invoice_data.get("subscription_id"),
        payment_id=invoice_data.get("payment_id"),
        status=invoice_data.get("status"),
        expire_by=make_aware_if_naive(datetime.fromtimestamp(invoice_data.get("expire_by")) if invoice_data.get("expire_by") else None),
        issued_at=make_aware_if_naive(datetime.fromtimestamp(invoice_data.get("issued_at")) if invoice_data.get("issued_at") else None),
        paid_at=make_aware_if_naive(datetime.fromtimestamp(invoice_data.get("paid_at")) if invoice_data.get("paid_at") else None),
        cancelled_at=make_aware_if_naive(datetime.fromtimestamp(invoice_data.get("cancelled_at")) if invoice_data.get("cancelled_at") else None),
        expired_at=make_aware_if_naive(datetime.fromtimestamp(invoice_data.get("expired_at")) if invoice_data.get("expired_at") else None),
        sms_status=invoice_data.get("sms_status"),
        email_status=invoice_data.get("email_status"),
        date=make_aware_if_naive(datetime.fromtimestamp(invoice_data.get("date")) if invoice_data.get("date") else None),
        terms=invoice_data.get("terms"),
        partial_payment=invoice_data.get("partial_payment", False),
        gross_amount=invoice_data.get("gross_amount"),
        tax_amount=invoice_data.get("tax_amount"),
        taxable_amount=invoice_data.get("taxable_amount"),
        amount=invoice_data.get("amount"),
        amount_paid=invoice_data.get("amount_paid"),
        amount_due=invoice_data.get("amount_due"),
        currency=invoice_data.get("currency"),
        description=invoice_data.get("description"),
        notes=invoice_data.get("notes"),
    )
    
    invoice.line_items.add(*line_items_instances)
    return invoice

def process_subscription_data(subscription_data):
    subscription = Subscription.objects.create(
        id=subscription_data.get("id"),
        plan_id=subscription_data.get("plan_id"),
        customer_id=subscription_data.get("customer_id"),
        status=subscription_data.get("status"),
        current_start=make_aware_if_naive(datetime.fromtimestamp(subscription_data.get("current_start")) if subscription_data.get("current_start") else None),
        current_end=make_aware_if_naive(datetime.fromtimestamp(subscription_data.get("current_end")) if subscription_data.get("current_end") else None),
        ended_at=make_aware_if_naive(datetime.fromtimestamp(subscription_data.get("ended_at")) if subscription_data.get("ended_at") else None),
        quantity=subscription_data.get("quantity", 1),
        notes=subscription_data.get("notes", {}),
        charge_at=make_aware_if_naive(datetime.fromtimestamp(subscription_data.get("charge_at")) if subscription_data.get("charge_at") else None),
        start_at=make_aware_if_naive(datetime.fromtimestamp(subscription_data.get("start_at")) if subscription_data.get("start_at") else None),
        end_at=make_aware_if_naive(datetime.fromtimestamp(subscription_data.get("end_at")) if subscription_data.get("end_at") else None),
        auth_attempts=subscription_data.get("auth_attempts", 0),
        total_count=subscription_data.get("total_count", 0),
        paid_count=subscription_data.get("paid_count", 0),
        customer_notify=subscription_data.get("customer_notify", True),
        created_at=make_aware_if_naive(datetime.fromtimestamp(subscription_data.get("created_at")) if subscription_data.get("created_at") else None),
        expire_by=make_aware_if_naive(datetime.fromtimestamp(subscription_data.get("expire_by")) if subscription_data.get("expire_by") else None),
        has_scheduled_changes=subscription_data.get("has_scheduled_changes", False),
        change_scheduled_at=make_aware_if_naive(datetime.fromtimestamp(subscription_data.get("change_scheduled_at")) if subscription_data.get("change_scheduled_at") else None),
        source=subscription_data.get("source"),
        payment_method=subscription_data.get("payment_method"),
        offer_id=subscription_data.get("offer_id"),
        remaining_count=subscription_data.get("remaining_count", 0),
    )

    return subscription

def process_order_data(order_data):
    order = Order.objects.create(
        id=order_data.get("id"),
        amount=order_data.get("amount", 0),
        amount_paid=order_data.get("amount_paid", 0),
        amount_due=order_data.get("amount_due", 0),
        currency=order_data.get("currency", "INR"),
        receipt=order_data.get("receipt"),
        offer_id=order_data.get("offer_id"),
        status=order_data.get("status", "created"),
        attempts=order_data.get("attempts", 0),
        created_at=make_aware_if_naive(datetime.fromtimestamp(order_data.get("created_at")) if order_data.get("created_at") else None),
        notes=order_data.get("notes", {})
    )

    return order