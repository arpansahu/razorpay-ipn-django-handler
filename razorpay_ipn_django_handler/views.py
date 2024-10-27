from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import logging
from django.db import transaction

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

@csrf_exempt
@transaction.atomic
def razorpay_ipn_receiver_view(request):
    if request.method == "POST":
        try:
            payload = json.loads(request.body)
            body = request.body.decode('utf-8')
            signature = request.headers.get("X-Razorpay-Signature")

            # Extract core event details from headers and payload
            event_id = request.META.get("HTTP_X_RAZORPAY_EVENT_ID")
            event_type = payload.get("event")
            account_id = payload.get("account_id")
            payload_data = payload.get("payload", {})

            # Check if this IPN event already exists
            if RazorpayIPN.objects.filter(event_id=event_id).exists():
                logger.info(f"Duplicate event received: {event_id}")
                return JsonResponse({"status": "Duplicate event"}, status=200)

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
                # Save the incomplete IPN record with signature_verified=False
                ipn_event.signature_verified = False
                ipn_event.save()
                # Send invalid signal
                invalid_razorpay_ipn_received.send(
                    sender=RazorpayIPN,
                    instance=ipn_event
                )
                return JsonResponse({"status": "Invalid signature"}, status=400)

            # If signature is verified, proceed with event processing
            ipn_event.signature_verified = True

            # Process Payment
            if "payment" in payload_data:
                payment_data = payload_data["payment"]["entity"]                    
                payment_instance = process_payment_data(payment_data)
                ipn_event.payment = payment_instance


            # Process Refund
            if "refund" in payload_data:
                refund_data = payload_data["refund"]["entity"]                    
                refund_instance = process_refund_data(refund_data)
                ipn_event.refund = refund_instance  


            # Process Invoice
            if "invoice" in payload_data:
                invoice_data = payload_data["invoice"]["entity"]                
                invoice_instance = process_invoice_data(invoice_data)
                ipn_event.invoice = invoice_instance

            # Process Subscription
            if "subscription" in payload_data:
                subscription_data = payload_data["subscription"]["entity"]                
                subscription_instance = process_subscription_data(subscription_data)
                ipn_event.subscription = subscription_instance

            # Process Order
            if "order" in payload_data:
                order_data = payload_data["order"]["entity"]
                order_instance = process_order_data(order_data)
                ipn_event.order = order_instance

            # Save the IPN event after processing
            ipn_event.save()

            # Send valid signal after successful processing
            valid_razorpay_ipn_received.send(sender=RazorpayIPN, instance=ipn_event)
            logger.info(f"Processed event {event_id} of type {event_type}")
            return JsonResponse({"status": "Success"}, status=200)

        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            logger.info(f"Payload which caused error is: {payload}")
            # Send minimal invalid signal information if `ipn_event` isn't created
            invalid_razorpay_ipn_received.send(
                sender=RazorpayIPN,
                instance={
                    "event_id": event_id,
                    "event_type": event_type,
                    "error": str(e)
                }
            )
            return JsonResponse({"status": "Error", "error": str(e)}, status=500)

    return JsonResponse({"status": "Method not allowed"}, status=405)
