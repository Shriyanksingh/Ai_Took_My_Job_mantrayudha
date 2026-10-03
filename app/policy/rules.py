from __future__ import annotations

import calendar
from datetime import date, datetime
from typing import Any, Dict

RESTOCK_CATEGORIES = {'laptops', 'tablets', 'cameras', 'monitors'}


def parse_datetime(value: str) -> datetime:
    """Parse NovaMart timestamps while preserving explicit timezone offsets."""
    text = str(value).strip().replace('Z', '+00:00')
    if 'T' in text or (len(text) >= 10 and text[4] == '-' and text[7] == '-'):
        if len(text) == 10:
            return datetime.strptime(text, '%Y-%m-%d')
        if 'T' in text:
            return datetime.fromisoformat(text)
        return datetime.strptime(text[:19], '%Y-%m-%d %H:%M:%S')
    return datetime.strptime(text[:19], '%Y-%m-%d %H:%M:%S')


def parse_date(value: str) -> date:
    return parse_datetime(value).date()


def hours_between(start: str, end: str) -> float:
    """Exact elapsed hours for SLA/boundary checks."""
    a = parse_datetime(start)
    b = parse_datetime(end)
    # Dataset timestamps without a timezone are interpreted in the same local
    # business timezone as the offset-aware conversation timestamp.
    if a.tzinfo is None and b.tzinfo is not None:
        a = a.replace(tzinfo=b.tzinfo)
    elif b.tzinfo is None and a.tzinfo is not None:
        b = b.replace(tzinfo=a.tzinfo)
    return (b - a).total_seconds() / 3600.0


def day_number(delivery_date: str, request_date: date) -> int:
    return (request_date - parse_date(delivery_date)).days


def effective_change_window(policy: Dict[str, Any], loyalty_tier: str) -> int:
    base = int(policy['change_of_mind_days'])
    tier = (loyalty_tier or '').lower()
    extra = (
        int(policy['gold_extra']) if tier == 'gold'
        else int(policy['platinum_extra']) if tier == 'platinum'
        else 0
    )
    return base + extra


def is_restockable_category(category: str) -> bool:
    return category.strip().lower() in RESTOCK_CATEGORIES


def restocking_fee(policy: Dict[str, Any], category: str, item_refund: float) -> float:
    if float(policy['restocking_percent']) <= 0 or not is_restockable_category(category):
        return 0.0
    return min(
        float(item_refund) * float(policy['restocking_percent']),
        float(policy['restocking_cap']),
    )


def warranty_end_date(delivery_date: str, warranty_months: int) -> date:
    """Add calendar months, preserving the day when possible."""
    start = parse_date(delivery_date)
    months = int(warranty_months)
    year = start.year + (start.month - 1 + months) // 12
    month = (start.month - 1 + months) % 12 + 1
    last = calendar.monthrange(year, month)[1]
    return date(year, month, min(start.day, last))
