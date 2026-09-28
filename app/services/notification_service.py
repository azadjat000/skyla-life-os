import subprocess
import threading
import time
from datetime import date, datetime

from app.extensions import db
from app.models import Reminder, ReminderLog


CHECK_INTERVAL_SECONDS = 30

_started = False
_thread = None
_lock = threading.Lock()

_last_notified = {}


def _is_due_today(reminder, now):
    repeat = (reminder.repeat or "daily").strip().lower()

    if repeat == "daily":
        return True

    if repeat == "weekdays":
        return now.weekday() < 5

    if repeat == "weekly":
        # Weekly reminders use Monday as the recurring weekday.
        return now.weekday() == 0

    if repeat == "monthly":
        # Monthly reminders repeat on the first day of each month.
        return now.day == 1

    return False


def _send_notification(reminder):
    title = f"Skyla Reminder: {reminder.title}"
    body = (
        f"⏰ {reminder.reminder_time or 'Now'}"
        f"  •  {reminder.repeat or 'daily'}"
    )

    try:
        subprocess.Popen(
            [
                "notify-send",
                "-a",
                "Skyla Life OS",
                "-u",
                "normal",
                title,
                body,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception as exc:
        print(f"[Skyla Notifications] notify-send failed: {exc}")
        return False


def _reminder_key(reminder, now):
    return f"{reminder.id}:{now.date().isoformat()}"


def check_reminders():
    now = datetime.now()
    current_time = now.strftime("%H:%M")

    try:
        reminders = Reminder.query.filter_by(enabled=True).all()

        for reminder in reminders:
            reminder_time = (reminder.reminder_time or "").strip()

            if not reminder_time:
                continue

            if reminder_time != current_time:
                continue

            if not _is_due_today(reminder, now):
                continue

            key = _reminder_key(reminder, now)

            with _lock:
                if key in _last_notified:
                    continue

            if _send_notification(reminder):
                log = ReminderLog(
                    reminder_id=reminder.id,
                    triggered_at=datetime.utcnow(),
                    status="triggered",
                )

                db.session.add(log)
                db.session.commit()

                with _lock:
                    _last_notified[key] = time.time()

        # Keep memory bounded.
        today_prefix = f":{date.today().isoformat()}"
        with _lock:
            stale = [
                key
                for key in _last_notified
                if not key.endswith(today_prefix)
            ]

            for key in stale:
                del _last_notified[key]

    except Exception as exc:
        db.session.rollback()
        print(f"[Skyla Notifications] check failed: {exc}")


def _notification_loop(app):
    with app.app_context():
        print("[Skyla Notifications] Background service started.")

        while True:
            try:
                check_reminders()
            except Exception as exc:
                print(
                    f"[Skyla Notifications] loop error: {exc}"
                )

            time.sleep(CHECK_INTERVAL_SECONDS)


def start_notification_service(app):
    global _started, _thread

    with _lock:
        if _started:
            return

        _started = True

    _thread = threading.Thread(
        target=_notification_loop,
        args=(app,),
        name="skyla-notifications",
        daemon=True,
    )

    _thread.start()
