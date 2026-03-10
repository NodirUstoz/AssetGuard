"""
Celery configuration for AssetGuard.
"""
import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

app = Celery("assetguard")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

# ---------------------------------------------------------------------------
# Periodic task schedule (Celery Beat)
# ---------------------------------------------------------------------------
app.conf.beat_schedule = {
    "check-license-renewals-daily": {
        "task": "apps.licenses.tasks.check_license_renewals",
        "schedule": crontab(hour=8, minute=0),
        "kwargs": {"days_ahead": 30},
    },
    "check-warranty-expirations-daily": {
        "task": "apps.maintenance.tasks.check_warranty_expirations",
        "schedule": crontab(hour=8, minute=15),
        "kwargs": {"days_ahead": 30},
    },
    "check-scheduled-maintenance-daily": {
        "task": "apps.maintenance.tasks.check_upcoming_maintenance",
        "schedule": crontab(hour=7, minute=0),
        "kwargs": {"days_ahead": 7},
    },
    "generate-monthly-depreciation": {
        "task": "apps.depreciation.services.generate_monthly_depreciation_entries",
        "schedule": crontab(day_of_month=1, hour=1, minute=0),
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to verify Celery is working."""
    print(f"Request: {self.request!r}")
