"""Celery tasks for license management."""
import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(name="apps.licenses.tasks.check_license_renewals")
def check_license_renewals(days_ahead=30):
    """
    Check for licenses expiring within the given number of days
    and send notification emails to administrators.
    """
    from apps.accounts.models import User
    from .models import SoftwareLicense

    cutoff_date = timezone.now().date() + timedelta(days=days_ahead)
    expiring_licenses = SoftwareLicense.objects.filter(
        expiration_date__lte=cutoff_date,
        expiration_date__gte=timezone.now().date(),
        status=SoftwareLicense.Status.ACTIVE,
    ).order_by("expiration_date")

    if not expiring_licenses.exists():
        logger.info("No licenses expiring within %d days.", days_ahead)
        return "No expiring licenses found."

    # Get admin/manager users who receive notifications
    recipients = User.objects.filter(
        role__in=[User.Role.ADMIN, User.Role.MANAGER],
        receive_notifications=True,
        is_active=True,
    ).values_list("email", flat=True)

    if not recipients:
        logger.warning("No notification recipients found.")
        return "No recipients configured."

    license_list = []
    for lic in expiring_licenses:
        license_list.append({
            "name": lic.software_name,
            "version": lic.version,
            "expiration_date": lic.expiration_date.strftime("%Y-%m-%d"),
            "days_remaining": lic.days_until_expiration,
            "total_seats": lic.total_seats,
            "used_seats": lic.used_seats,
            "annual_cost": str(lic.annual_cost),
        })

        # Mark as pending renewal if expiring within 14 days
        if lic.days_until_expiration is not None and lic.days_until_expiration <= 14:
            lic.status = SoftwareLicense.Status.PENDING_RENEWAL
            lic.save(update_fields=["status", "updated_at"])

    subject = f"[AssetGuard] {len(license_list)} License(s) Expiring Soon"
    message_lines = [
        f"The following {len(license_list)} license(s) are expiring within {days_ahead} days:\n",
    ]
    for item in license_list:
        message_lines.append(
            f"  - {item['name']} {item['version']}: expires {item['expiration_date']} "
            f"({item['days_remaining']} days remaining, "
            f"{item['used_seats']}/{item['total_seats']} seats used)"
        )
    message_lines.append("\nPlease review and initiate renewals as needed.")
    message = "\n".join(message_lines)

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=list(recipients),
            fail_silently=False,
        )
        logger.info(
            "License renewal notification sent for %d licenses to %d recipients.",
            len(license_list),
            len(recipients),
        )
    except Exception as e:
        logger.error("Failed to send license renewal notification: %s", str(e))
        raise

    return f"Notified about {len(license_list)} expiring license(s)."


@shared_task(name="apps.licenses.tasks.update_expired_licenses")
def update_expired_licenses():
    """Mark licenses that have passed their expiration date as expired."""
    from .models import SoftwareLicense

    expired_count = SoftwareLicense.objects.filter(
        expiration_date__lt=timezone.now().date(),
        status__in=[
            SoftwareLicense.Status.ACTIVE,
            SoftwareLicense.Status.PENDING_RENEWAL,
        ],
    ).update(status=SoftwareLicense.Status.EXPIRED)

    logger.info("Marked %d licenses as expired.", expired_count)
    return f"Marked {expired_count} license(s) as expired."
