from django.contrib import admin
from .models import (
    BillingAddress,
    ShippingAddress,
    CustomerDetails,
    Item,
    LineItem,
    Invoice,
    UPIDetails,
    CardDetails,
    Payment,
    Subscription,
    Order,
    RazorpayWebhook,
    RazorpayIPN,  # Add RazorpayIPN here
)


class BillingAddressAdmin(admin.ModelAdmin):
    list_display = ('id', 'primary', 'line1', 'city', 'state', 'country', 'zipcode')
    search_fields = ('id', 'line1', 'city', 'state', 'country', 'zipcode')


class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ('id', 'primary', 'line1', 'city', 'state', 'country', 'zipcode')
    search_fields = ('id', 'line1', 'city', 'state', 'country', 'zipcode')


class CustomerDetailsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'contact')
    search_fields = ('id', 'name', 'email', 'contact')
    list_filter = ('billing_address__state', 'shipping_address__state')


class ItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'amount', 'currency', 'tax_rate')
    search_fields = ('id', 'name', 'hsn_code', 'sac_code')
    list_filter = ('currency', 'tax_inclusive')


class LineItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'amount', 'quantity')
    search_fields = ('id', 'name', 'description')
    list_filter = ('amount',)


class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'customer_id', 'amount', 'currency', 'amount_due', 'issued_at', 'paid_at')
    search_fields = ('id', 'customer_id', 'order_id', 'subscription_id')
    list_filter = ('status', 'currency', 'sms_status', 'email_status')
    date_hierarchy = 'issued_at'
    filter_horizontal = ('line_items',)


class UPIDetailsAdmin(admin.ModelAdmin):
    list_display = ('vpa', 'payer_account_type')
    search_fields = ('vpa',)
    list_filter = ('payer_account_type',)


class CardDetailsAdmin(admin.ModelAdmin):
    list_display = ('card_id', 'name', 'last4', 'network', 'card_type', 'issuer')
    search_fields = ('card_id', 'name', 'last4', 'issuer')
    list_filter = ('network', 'card_type', 'sub_type')

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'amount', 'currency', 'status', 'method', 'captured', 'refund_status')
    search_fields = ('id', 'order_id', 'invoice_id', 'error_code')
    list_filter = ('status', 'method', 'currency', 'captured')
    date_hierarchy = 'created_at'


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_id', 'status', 'plan_id', 'quantity', 'current_start', 'current_end')
    search_fields = ('id', 'customer_id', 'plan_id')
    list_filter = ('status', 'customer_notify', 'has_scheduled_changes', 'schedule_change_at')
    date_hierarchy = 'current_start'


class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'amount', 'currency', 'status', 'partial_payment', 'created_at')
    search_fields = ('id', 'receipt')
    list_filter = ('status', 'currency', 'partial_payment')
    date_hierarchy = 'created_at'


class RazorpayWebhookAdmin(admin.ModelAdmin):
    list_display = ('event_id', 'event_type', 'account_id', 'processed', 'created_at')
    search_fields = ('event_id', 'event_type', 'account_id')
    list_filter = ('processed',)
    date_hierarchy = 'created_at'


class RazorpayIPNAdmin(admin.ModelAdmin):
    list_display = ('event_id', 'event_type', 'account_id', 'signature_verified', 'created_at')
    search_fields = ('event_id', 'event_type', 'account_id')
    list_filter = ('signature_verified',)
    date_hierarchy = 'created_at'


# Register all models with customized admin classes
admin.site.register(BillingAddress, BillingAddressAdmin)
admin.site.register(ShippingAddress, ShippingAddressAdmin)
admin.site.register(CustomerDetails, CustomerDetailsAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(LineItem, LineItemAdmin)
admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(UPIDetails, UPIDetailsAdmin)
admin.site.register(CardDetails, CardDetailsAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(RazorpayWebhook, RazorpayWebhookAdmin)
admin.site.register(RazorpayIPN, RazorpayIPNAdmin)  # Register RazorpayIPN
