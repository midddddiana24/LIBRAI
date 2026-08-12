from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.core.config import settings
from backend.models.entities import SystemSetting


DEFAULTS = {"BORROWING_LIMIT": str(settings.default_borrowing_limit), "BORROWING_PERIOD_DAYS": str(settings.default_borrowing_period_days), "MAX_RENEWALS": "1", "ALLOW_BORROW_WITH_OVERDUE": str(settings.default_allow_borrow_with_overdue).lower(), "RESERVATION_HOLD_DAYS": "2", "OVERDUE_FINE_PER_DAY_CENTS": "500", "BLOCK_BORROW_WITH_UNPAID_FINES": "true"}


def get_setting(db: Session, key: str) -> str:
    row = db.scalar(select(SystemSetting).where(SystemSetting.key == key))
    return row.value if row else DEFAULTS[key]


def borrowing_limit(db: Session) -> int: return int(get_setting(db, "BORROWING_LIMIT"))
def borrowing_period_days(db: Session) -> int: return int(get_setting(db, "BORROWING_PERIOD_DAYS"))
def max_renewals(db: Session) -> int: return int(get_setting(db, "MAX_RENEWALS"))
def allow_overdue(db: Session) -> bool: return get_setting(db, "ALLOW_BORROW_WITH_OVERDUE").lower() == "true"
def reservation_hold_days(db: Session) -> int: return int(get_setting(db, "RESERVATION_HOLD_DAYS"))
def overdue_fine_per_day_cents(db: Session) -> int: return int(get_setting(db, "OVERDUE_FINE_PER_DAY_CENTS"))
def block_borrow_with_unpaid_fines(db: Session) -> bool: return get_setting(db, "BLOCK_BORROW_WITH_UNPAID_FINES").lower() == "true"
