import shutil
import subprocess
import threading
import time
from pathlib import Path
from datetime import date, datetime

from app.extensions import db
from app.models import Reminder, ReminderLog


CHECK_INTERVAL_SECONDS = 30

_started = False
_thread = None
_lock = threading.Lock()

_last_notified = {}

SOUND_FILES = {
    "bell": "bell.wav",
    "siren": "siren.wav",
    "alarm": "alarm.wav",
    "chime": "chime.wav",
}

PRIORITY_MAP = {
    "low": "low",
    "normal": "normal",
    "high": "critical",
    "urgent": "critical",
}



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


def _sound_path(sound_type):
    filename = SOUND_FILES.get(
        (sound_type or "bell").strip().lower()
    )

    if not filename:
        filename = SOUND_FILES["bell"]

    return (
        Path(__file__).resolve().parent.parent
        / "static"
        / "sounds"
        / filename
    )


def _play_sound(sound_type="bell", volume=80):
    try:
        sound_type = (sound_type or "bell").strip().lower()

        try:
            volume = int(volume)
        except (TypeError, ValueError):
            volume = 80

        volume = max(0, min(100, volume))

        player = shutil.which("pw-play") or shutil.which("paplay")
        sound_path = _sound_path(sound_type)

        if not player:
            print("[Skyla Notifications] No audio player found.")
            return False

        if not sound_path.exists():
            print(
                f"[Skyla Notifications] Sound file missing: {sound_path}"
            )
            return False

        if player.endswith("pw-play"):
            subprocess.Popen(
                [
                    player,
                    "--volume",
                    str(volume / 100.0),
                    str(sound_path),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            pulse_volume = int(65536 * volume / 100)

            subprocess.Popen(
                [
                    player,
                    "--volume",
                    str(pulse_volume),
                    str(sound_path),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        return True

    except Exception as exc:
        print(
            f"[Skyla Notifications] sound playback failed: {exc}"
        )
        return False


def _send_notification(reminder):
    title = f"Skyla Reminder: {reminder.title}"

    priority = (
        getattr(reminder, "priority", "normal")
        or "normal"
    ).strip().lower()

    urgency = PRIORITY_MAP.get(priority, "normal")

    body = (
        f"⏰ {reminder.reminder_time or 'Now'}"
        f"  •  {reminder.repeat or 'daily'}"
        f"  •  {priority.title()}"
    )

    try:
        subprocess.Popen(
            [
                "notify-send",
                "-a",
                "Skyla Life OS",
                "-u",
                urgency,
                title,
                body,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        sound_enabled = getattr(
            reminder,
            "sound_enabled",
            True,
        )

        if sound_enabled:
            _play_sound(
                getattr(reminder, "sound_type", "bell"),
                getattr(reminder, "sound_volume", 80),
            )

        return True

    except Exception as exc:
        print(
            f"[Skyla Notifications] notify-send failed: {exc}"
        )
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

            # Snooze handling
            snooze_until = getattr(reminder, "snooze_until", None)

            if snooze_until:
                if now < snooze_until:
                    continue

                snooze_key = (
                    f"{reminder.id}:snooze:{snooze_until.isoformat()}"
                )

                with _lock:
                    if snooze_key in _last_notified:
                        continue

                if _send_notification(reminder):
                    log = ReminderLog(
                        reminder_id=reminder.id,
                        triggered_at=datetime.utcnow(),
                        status="snoozed",
                    )

                    db.session.add(log)
                    reminder.snooze_until = None
                    db.session.commit()

                    with _lock:
                        _last_notified[snooze_key] = time.time()

                continue

            # Normal scheduled reminder.
            # Treat a reminder as due once its scheduled minute has arrived.
            # _last_notified prevents duplicate notifications for the same day.
            try:
                scheduled_hour, scheduled_minute = map(
                    int,
                    reminder_time.split(":", 1),
                )
                scheduled_total_minutes = (
                    scheduled_hour * 60 + scheduled_minute
                )
                current_total_minutes = (
                    now.hour * 60 + now.minute
                )
            except (TypeError, ValueError):
                continue

            if scheduled_total_minutes > current_total_minutes:
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
                if ":snooze:" not in key
                and not key.endswith(today_prefix)
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
