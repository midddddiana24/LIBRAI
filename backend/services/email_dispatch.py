"""Bounded delivery while the API is running; the database remains the outbox."""
import logging
from threading import Event

from backend.scripts.email_worker import configured, process

logger = logging.getLogger(__name__)


def deliver_one(delivery_id: int):
    try:
        process(limit=1, delivery_id=delivery_id)
    except Exception as exc:
        logger.warning("Email dispatch stopped (%s); inspect configuration and pending queue.", type(exc).__name__)


def poll(stop: Event):
    while not stop.is_set():
        try:
            if configured():
                process(limit=5)
        except Exception as exc:
            logger.warning("Email polling paused (%s); pending work remains in the database.", type(exc).__name__)
        stop.wait(30)
