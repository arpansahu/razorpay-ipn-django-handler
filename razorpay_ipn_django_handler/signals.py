# signals.py
from django.dispatch import Signal

# Sent when a validated, non-duplicated webhook is received
valid_razorpay_ipn_received = Signal()

# Sent when a flagged webhook (e.g., duplicate, invalid) is received
invalid_razorpay_ipn_received = Signal()