from django.db import migrations, models
from django.db.models import Count


def remove_duplicate_event_ids(apps, schema_editor):
    webhook_model = apps.get_model(
        "razorpay_ipn_django_handler",
        "RazorpayWebhook",
    )
    duplicate_ids = (
        webhook_model.objects.values("event_id")
        .annotate(total=Count("event_id"))
        .filter(total__gt=1)
    )
    for duplicate in duplicate_ids.iterator():
        webhooks = webhook_model.objects.filter(
            event_id=duplicate["event_id"]
        ).order_by("created_at", "uuid")
        webhooks.exclude(uuid=webhooks.first().uuid).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("razorpay_ipn_django_handler", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            remove_duplicate_event_ids,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="razorpaywebhook",
            name="event_id",
            field=models.CharField(
                help_text="Unique identifier for the Razorpay event",
                max_length=255,
                unique=True,
            ),
        ),
    ]