import hashlib
import hmac
import json
from datetime import datetime, timezone

from django.test import TestCase, override_settings

from .models import RazorpayIPN
from .signals import valid_razorpay_ipn_received
from .utilities import datetime_from_timestamp


@override_settings(RAZORPAY_WEBHOOK_SECRET="test-secret")
class RazorpayIPNReceiverTests(TestCase):
	url = "/webhook/"

	def _post_event(self, event, signature=None, event_id="evt_test"):
		body = json.dumps(event, separators=(",", ":")).encode()
		if signature is None:
			signature = hmac.new(b"test-secret", body, hashlib.sha256).hexdigest()
		return self.client.post(
			self.url,
			data=body,
			content_type="application/json",
			HTTP_X_RAZORPAY_EVENT_ID=event_id,
			HTTP_X_RAZORPAY_SIGNATURE=signature,
		)

	def test_rejects_malformed_json(self):
		response = self.client.post(
			self.url,
			data=b"{invalid",
			content_type="application/json",
		)

		self.assertEqual(response.status_code, 400)
		self.assertEqual(response.json(), {"status": "Invalid JSON"})

	def test_rejects_missing_webhook_metadata(self):
		response = self.client.post(
			self.url,
			data=b"{}",
			content_type="application/json",
		)

		self.assertEqual(response.status_code, 400)
		self.assertEqual(response.json(), {"status": "Missing webhook metadata"})

	def test_invalid_signature_does_not_reserve_event_id(self):
		event = {
			"event": "payment.authorized",
			"account_id": "acc_test",
			"payload": {},
		}

		invalid_response = self._post_event(event, signature="invalid")
		valid_response = self._post_event(event)

		self.assertEqual(invalid_response.status_code, 400)
		self.assertEqual(valid_response.status_code, 200)
		self.assertEqual(RazorpayIPN.objects.count(), 1)

	def test_valid_event_is_processed_and_duplicate_is_ignored(self):
		event = {
			"event": "payment.authorized",
			"account_id": "acc_test",
			"payload": {},
		}

		response = self._post_event(event)
		duplicate_response = self._post_event(event)

		ipn = RazorpayIPN.objects.get(event_id="evt_test")
		self.assertEqual(response.json(), {"status": "Success"})
		self.assertTrue(ipn.signature_verified)
		self.assertTrue(ipn.processed)
		self.assertEqual(duplicate_response.json(), {"status": "Duplicate event"})
		self.assertEqual(RazorpayIPN.objects.count(), 1)

	def test_order_payload_preserves_partial_payment(self):
		event = {
			"event": "order.paid",
			"account_id": "acc_test",
			"payload": {
				"order": {
					"entity": {
						"id": "order_test",
						"amount": 10000,
						"amount_paid": 2500,
						"amount_due": 7500,
						"currency": "INR",
						"partial_payment": True,
						"created_at": 1735689600,
					}
				}
			},
		}

		response = self._post_event(event, event_id="evt_order")

		self.assertEqual(response.status_code, 200)
		order = RazorpayIPN.objects.get(event_id="evt_order").order
		self.assertTrue(order.partial_payment)
		self.assertEqual(
			order.created_at,
			datetime(2025, 1, 1, tzinfo=timezone.utc),
		)

	def test_payment_payload_persists_nested_upi_details(self):
		event = {
			"event": "payment.captured",
			"account_id": "acc_test",
			"payload": {
				"payment": {
					"entity": {
						"id": "pay_test",
						"amount": 49900,
						"currency": "INR",
						"status": "captured",
						"method": "upi",
						"captured": True,
						"upi": {
							"vpa": "customer@bank",
							"flow": "in_app",
							"payer_account_type": "bank_account",
						},
					}
				}
			},
		}

		response = self._post_event(event, event_id="evt_payment")

		self.assertEqual(response.status_code, 200)
		payment = RazorpayIPN.objects.get(event_id="evt_payment").payment
		self.assertEqual(payment.id, "pay_test")
		self.assertTrue(payment.captured)
		self.assertEqual(payment.upi_details.vpa, "customer@bank")

	def test_refund_payload_persists_required_fields(self):
		event = {
			"event": "refund.processed",
			"account_id": "acc_test",
			"payload": {
				"refund": {
					"entity": {
						"id": "rfnd_test",
						"amount": 1000,
						"currency": "INR",
						"payment_id": "pay_test",
						"speed": "normal",
						"status": "processed",
						"created_at": 1735689600,
					}
				}
			},
		}

		response = self._post_event(event, event_id="evt_refund")

		self.assertEqual(response.status_code, 200)
		refund = RazorpayIPN.objects.get(event_id="evt_refund").refund
		self.assertEqual(refund.payment_id, "pay_test")
		self.assertEqual(refund.status, "processed")

	def test_invoice_payload_links_line_items(self):
		event = {
			"event": "invoice.paid",
			"account_id": "acc_test",
			"payload": {
				"invoice": {
					"entity": {
						"id": "inv_test",
						"status": "paid",
						"currency": "INR",
						"line_items": [
							{
								"id": "li_test",
								"name": "Annual plan",
								"amount": 120000,
								"quantity": 1,
							}
						],
					}
				}
			},
		}

		response = self._post_event(event, event_id="evt_invoice")

		self.assertEqual(response.status_code, 200)
		invoice = RazorpayIPN.objects.get(event_id="evt_invoice").invoice
		self.assertEqual(invoice.line_items.count(), 1)
		self.assertEqual(invoice.line_items.get().name, "Annual plan")

	def test_subscription_payload_persists_cycle_counts(self):
		event = {
			"event": "subscription.activated",
			"account_id": "acc_test",
			"payload": {
				"subscription": {
					"entity": {
						"id": "sub_test",
						"plan_id": "plan_test",
						"status": "active",
						"total_count": 12,
						"paid_count": 1,
						"remaining_count": 11,
						"current_start": 1735689600,
					}
				}
			},
		}

		response = self._post_event(event, event_id="evt_subscription")

		self.assertEqual(response.status_code, 200)
		subscription = RazorpayIPN.objects.get(
			event_id="evt_subscription"
		).subscription
		self.assertEqual(subscription.status, "active")
		self.assertEqual(subscription.remaining_count, 11)

	def test_signal_failure_rolls_back_event_for_retry(self):
		event = {
			"event": "payment.authorized",
			"account_id": "acc_test",
			"payload": {},
		}

		def failing_receiver(sender, **kwargs):
			raise RuntimeError("downstream processing failed")

		valid_razorpay_ipn_received.connect(
			failing_receiver,
			dispatch_uid="failing-test-receiver",
		)
		try:
			response = self._post_event(event, event_id="evt_retry")
		finally:
			valid_razorpay_ipn_received.disconnect(
				dispatch_uid="failing-test-receiver"
			)

		self.assertEqual(response.status_code, 500)
		self.assertFalse(RazorpayIPN.objects.filter(event_id="evt_retry").exists())

		retry_response = self._post_event(event, event_id="evt_retry")
		self.assertEqual(retry_response.status_code, 200)


class TimestampConversionTests(TestCase):
	def test_timestamp_is_interpreted_as_utc(self):
		self.assertEqual(
			datetime_from_timestamp(0),
			datetime(1970, 1, 1, tzinfo=timezone.utc),
		)

	def test_missing_timestamp_remains_none(self):
		self.assertIsNone(datetime_from_timestamp(None))
