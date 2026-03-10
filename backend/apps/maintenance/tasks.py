"""Celery tasks for maintenance management."""
import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(name="apps.maintenance.tasks.check_warranty_expirations")
def check_warranty_expirations(days_ahead=30):
    """
    Check for warranties expiring within the given number of days
    and send notification emails.
    """
    from apps.accounts.models import User
    from .models import Warranty

    cutoff_date = timezone.now().date() + timedelta(days=days_ahead)
    expiring_warranties = Warranty.objects.filter(
        end_date__lte=cutoff_date,
        end_date__gte=timezone.now().date(),
        status=Warranty.Status.ACTIVE,
    ).select_related("asset").order_by("end_date")

    if not expiring_warranties.exists():
        logger.info("No warranties expiring within %d days.", days_ahead)
        return "No expiring warranties found."

    recipients = User.objects.filter(
        role__in=[User.Role.ADMIN, User.Role.MANAGER],
        receive_notifications=True,
        is_active=True,
    ).values_list("email", flat=True)

    if not recipients:
        logger.warning("No notification recipients found.")
        return "No recipients configured."

    warranty_list = []
    for warranty in expiring_warranties:
        warranty_list.append({
            "asset": str(warranty.asset),
            "provider": warranty.provider,
            "end_date": warranty.end_date.strftime("%Y-%m-%d"),
            "days_remaining": warranty.days_remaining,
        })

    subject = f"[AssetGuard] {len(warranty_list)} Warranty(ies) Expiring Soon"
    message_lines = [
        f"The following {len(warranty_list)} warranty(ies) are expiring within {days_ahead} days:\n",
    ]
    for item in warranty_list:
        message_lines.append(
            f"  - {item['asset']} ({item['provider']}): "
            f"expires {item['end_date']} ({item['days_remaining']} days remaining)"
        )
    message_lines.append("\nPlease review and take action as needed.")
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
            "Warranty expiration notification sent for %d warranties.",
            len(warranty_list),
        )
    except Exception as e:
        logger.error("Failed to send warranty notification: %s", str(e))
        raise

    return f"Notified about {len(warranty_list)} expiring warranty(ies)."


@shared_task(name="apps.maintenance.tasks.check_upcoming_maintenance")
def check_upcoming_maintenance(days_ahead=7):
    """
    Check for upcoming scheduled maintenance and send reminders.
    Also mark overdue maintenance.
    """
    from apps.accounts.models import User
    from .models import MaintenanceSchedule

    today = timezone.now().date()
    cutoff_date = today + timedelta(days=days_ahead)

    # Mark overdue schedules
    overdue_count = MaintenanceSchedule.objects.filter(
        scheduled_date__lt=today,
        status__in=[
            MaintenanceSchedule.Status.SCHEDULED,
            MaintenanceSchedule.Status.IN_PROGRESS,
        ],
    ).update(status=MaintenanceSchedule.Status.OVERDUE)

    if overdue_count > 0:
        logger.info("Marked %d maintenance schedule(s) as overdue.", overdue_count)

    # Find upcoming maintenance
    upcoming = MaintenanceSchedule.objects.filter(
        scheduled_date__gte=today,
        scheduled_date__lte=cutoff_date,
        status=MaintenanceSchedule.Status.SCHEDULED,
    ).select_related("asset").order_by("scheduled_date")

    if not upcoming.exists():
        return f"Marked {overdue_count} as overdue. No upcoming maintenance."

    recipients = User.objects.filter(
        role__in=[User.Role.ADMIN, User.Role.MANAGER, User.Role.TECHNICIAN],
        receive_notifications=True,
        is_active=True,
    ).values_list("email", flat=True)

    if not recipients:
        return f"Marked {overdue_count} as overdue. No recipients for upcoming alerts."

    subject = f"[AssetGuard] {upcoming.count()} Upcoming Maintenance Event(s)"
    message_lines = [
        f"The following maintenance events are scheduled within the next {days_ahead} days:\n",
    ]
    for item in upcoming:
        days_until = (item.scheduled_date - today).days
        message_lines.append(
            f"  - [{item.priority.upper()}] {item.asset.asset_tag}: {item.title} "
            f"on {item.scheduled_date.strftime('%Y-%m-%d')} "
            f"({days_until} day(s) from now)"
        )
    if overdue_count > 0:
        message_lines.append(f"\nAdditionally, {overdue_count} maintenance event(s) are OVERDUE.")
    message = "\n".join(message_lines)

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=list(recipients),
            fail_silently=False,
        )
    except Exception as e:
        logger.error("Failed to send maintenance reminder: %s", str(e))
        raise

    return f"Overdue: {overdue_count}, Upcoming reminders sent: {upcoming.count()}"
