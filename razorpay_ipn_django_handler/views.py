from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import logging
from django.db import IntegrityError, transaction

from .models import RazorpayIPN
from .utilities import ( 
    process_payment_data, 
    process_refund_data,
    process_invoice_data, 
    process_subscription_data,
    process_order_data
)

from .signals import (
    valid_razorpay_ipn_received,
    invalid_razorpay_ipn_received, 
)

logger = logging.getLogger(__name__)


def _process_payload(ipn_event, payload_data):
    if "payment" in payload_data:
        ipn_event.payment = process_payment_data(payload_data["payment"]["entity"])

    if "refund" in payload_data:
        ipn_event.refund = process_refund_data(payload_data["refund"]["entity"])

    if "invoice" in payload_data:
        ipn_event.invoice = process_invoice_data(payload_data["invoice"]["entity"])

    if "subscription" in payload_data:
        ipn_event.subscription = process_subscription_data(payload_data["subscription"]["entity"])

    if "order" in payload_data:
        ipn_event.order = process_order_data(payload_data["order"]["entity"])


@csrf_exempt
def razorpay_ipn_receiver_view(request):
    if request.method == "POST":
        event_id = None
        event_type = None
        try:
            try:
                payload = json.loads(request.body)
            except (json.JSONDecodeError, UnicodeDecodeError):
                return JsonResponse({"status": "Invalid JSON"}, status=400)

            if not isinstance(payload, dict):
                return JsonResponse({"status": "Invalid payload"}, status=400)

            body = request.body
            signature = request.headers.get("X-Razorpay-Signature")

            # Extract core event details from headers and payload
            event_id = request.META.get("HTTP_X_RAZORPAY_EVENT_ID")
            event_type = payload.get("event")
            account_id = payload.get("account_id")
            payload_data = payload.get("payload", {})

            if not event_id or not event_type or not account_id or not signature:
                return JsonResponse({"status": "Missing webhook metadata"}, status=400)

            if not isinstance(payload_data, dict):
                return JsonResponse({"status": "Invalid payload"}, status=400)

            # Initialize the IPN event instance
            ipn_event = RazorpayIPN(
                event_id=event_id,
                event_type=event_type,
                account_id=account_id,
                payload=payload
            )

            # ipn_event.save() # Temp

            # Verify the signature
            if not ipn_event.verify_signature(body, signature):
                logger.warning(f"Signature verification failed for event {event_id}")
                invalid_razorpay_ipn_received.send(
                    sender=RazorpayIPN,
                    instance=ipn_event
                )
                return JsonResponse({"status": "Invalid signature"}, status=400)

            # If signature is verified, proceed with event processing
            ipn_event.signature_verified = True

            try:
                with transaction.atomic():
                    if RazorpayIPN.objects.filter(event_id=event_id).exists():
                        logger.info("Duplicate event received: %s", event_id)
                        return JsonResponse({"status": "Duplicate event"}, status=200)

                    _process_payload(ipn_event, payload_data)
                    ipn_event.processed = True
                    ipn_event.save()
                    valid_razorpay_ipn_received.send(
                        sender=RazorpayIPN,
                        instance=ipn_event,
                    )
            except IntegrityError:
                if RazorpayIPN.objects.filter(event_id=event_id).exists():
                    logger.info("Concurrent duplicate event received: %s", event_id)
                    return JsonResponse({"status": "Duplicate event"}, status=200)
                raise

            logger.info(f"Processed event {event_id} of type {event_type}")
            return JsonResponse({"status": "Success"}, status=200)

        except Exception as e:
            logger.exception("Error processing webhook event %s", event_id)
            # Send minimal invalid signal information if `ipn_event` isn't created
            invalid_razorpay_ipn_received.send(
                sender=RazorpayIPN,
                instance={
                    "event_id": event_id,
                    "event_type": event_type,
                    "error": str(e)
                }
            )
            return JsonResponse({"status": "Error"}, status=500)

    return JsonResponse({"status": "Method not allowed"}, status=405)
