"""Depreciation calculation services."""
import logging
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from celery import shared_task
from django.utils import timezone

from .models import DepreciationEntry, DepreciationSchedule

logger = logging.getLogger(__name__)


def calculate_straight_line_monthly(schedule: DepreciationSchedule) -> Decimal:
    """Calculate monthly depreciation using straight-line method."""
    if schedule.useful_life_months <= 0:
        return Decimal("0.00")
    monthly = schedule.depreciable_amount / schedule.useful_life_months
    return monthly.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_declining_balance_monthly(
    schedule: DepreciationSchedule,
    current_book_value: Decimal,
) -> Decimal:
    """Calculate monthly depreciation using declining balance method."""
    if schedule.depreciation_rate <= 0:
        return Decimal("0.00")

    annual_depreciation = current_book_value * schedule.depreciation_rate
    monthly = (annual_depreciation / 12).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Ensure we don't depreciate below salvage value
    if current_book_value - monthly < schedule.salvage_value:
        monthly = current_book_value - schedule.salvage_value

    return max(monthly, Decimal("0.00"))


def calculate_double_declining_monthly(
    schedule: DepreciationSchedule,
    current_book_value: Decimal,
) -> Decimal:
    """Calculate monthly depreciation using double-declining balance method."""
    if schedule.useful_life_months <= 0:
        return Decimal("0.00")

    annual_rate = Decimal(2) / (schedule.useful_life_months / 12)
    annual_depreciation = current_book_value * annual_rate
    monthly = (annual_depreciation / 12).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Ensure we don't depreciate below salvage value
    if current_book_value - monthly < schedule.salvage_value:
        monthly = current_book_value - schedule.salvage_value

    return max(monthly, Decimal("0.00"))


def generate_depreciation_entry(
    schedule: DepreciationSchedule,
    period_date: date,
) -> DepreciationEntry | None:
    """
    Generate a single depreciation entry for the given period.
    Returns None if already exists or asset is fully depreciated.
    """
    # Check if entry already exists
    if DepreciationEntry.objects.filter(
        schedule=schedule,
        period_date=period_date,
    ).exists():
        logger.debug(
            "Depreciation entry already exists for %s on %s",
            schedule.asset.asset_tag,
            period_date,
        )
        return None

    # Check if fully depreciated
    current_book_value = schedule.current_book_value
    if current_book_value <= schedule.salvage_value:
        logger.debug("Asset %s is fully depreciated.", schedule.asset.asset_tag)
        return None

    # Check if period is before start date or past useful life
    if period_date < schedule.start_date:
        return None

    # Calculate depreciation amount based on method
    if schedule.method == DepreciationSchedule.Method.STRAIGHT_LINE:
        amount = calculate_straight_line_monthly(schedule)
    elif schedule.method == DepreciationSchedule.Method.DECLINING_BALANCE:
        amount = calculate_declining_balance_monthly(schedule, current_book_value)
    elif schedule.method == DepreciationSchedule.Method.DOUBLE_DECLINING:
        amount = calculate_double_declining_monthly(schedule, current_book_value)
    else:
        amount = calculate_straight_line_monthly(schedule)

    if amount <= 0:
        return None

    # Ensure book value doesn't go below salvage value
    if current_book_value - amount < schedule.salvage_value:
        amount = current_book_value - schedule.salvage_value

    accumulated = schedule.total_depreciated + amount

    entry = DepreciationEntry.objects.create(
        schedule=schedule,
        period_date=period_date,
        amount=amount,
        book_value_before=current_book_value,
        book_value_after=current_book_value - amount,
        accumulated_depreciation=accumulated,
    )

    logger.info(
        "Created depreciation entry for %s: $%s (period: %s)",
        schedule.asset.asset_tag,
        amount,
        period_date,
    )
    return entry


@shared_task(name="apps.depreciation.services.generate_monthly_depreciation_entries")
def generate_monthly_depreciation_entries():
    """
    Generate depreciation entries for all active schedules for the current month.
    Intended to be run on the 1st of each month via Celery Beat.
    """
    today = timezone.now().date()
    period_date = today.replace(day=1)

    schedules = DepreciationSchedule.objects.filter(
        is_active=True,
        start_date__lte=period_date,
    ).select_related("asset")

    created_count = 0
    skipped_count = 0

    for schedule in schedules:
        entry = generate_depreciation_entry(schedule, period_date)
        if entry:
            created_count += 1
        else:
            skipped_count += 1

    logger.info(
        "Monthly depreciation run complete: %d created, %d skipped.",
        created_count,
        skipped_count,
    )
    return f"Created {created_count} entries, skipped {skipped_count}."


def generate_full_depreciation_schedule(schedule: DepreciationSchedule) -> list:
    """
    Generate a full projected depreciation schedule (all months)
    without saving to the database. Used for preview/reporting.
    """
    entries = []
    current_book_value = schedule.original_cost
    accumulated = Decimal("0.00")
    period = schedule.start_date.replace(day=1)

    for month_num in range(schedule.useful_life_months):
        if current_book_value <= schedule.salvage_value:
            break

        if schedule.method == DepreciationSchedule.Method.STRAIGHT_LINE:
            amount = calculate_straight_line_monthly(schedule)
        elif schedule.method == DepreciationSchedule.Method.DECLINING_BALANCE:
            amount = calculate_declining_balance_monthly(schedule, current_book_value)
        else:
            amount = calculate_double_declining_monthly(schedule, current_book_value)

        if current_book_value - amount < schedule.salvage_value:
            amount = current_book_value - schedule.salvage_value

        if amount <= 0:
            break

        accumulated += amount
        entries.append({
            "month": month_num + 1,
            "period_date": period.isoformat(),
            "amount": str(amount),
            "book_value_before": str(current_book_value),
            "book_value_after": str(current_book_value - amount),
            "accumulated_depreciation": str(accumulated),
        })

        current_book_value -= amount

        # Advance to next month
        if period.month == 12:
            period = period.replace(year=period.year + 1, month=1)
        else:
            period = period.replace(month=period.month + 1)

    return entries
