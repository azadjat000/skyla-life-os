from datetime import date, datetime, timedelta

from flask import Blueprint, jsonify, render_template, request

from app.extensions import db
from app.models import (
    AppSettings,
    Reminder,
    Routine,
    RoutineLog,
    Habit,
    HabitLog,
    Goal,
    FocusSession,
    FootballSession,
    FitnessWorkout,
    CalendarEvent,
)

pages = Blueprint("pages", __name__)


# =========================================================
# PAGE ROUTES
# =========================================================

@pages.get("/calendar")
def calendar():
    return render_template(
        "module.html",
        title="📅 Calendar",
        subtitle="Plan your days, weeks and months.",
        module="calendar",
    )


@pages.get("/routine")
def routine():
    return render_template(
        "module.html",
        title="🕒 Daily Routine",
        subtitle="Manage your hourly schedule and recurring tasks.",
        module="routine",
    )


@pages.get("/reminders")
def reminders():
    return render_template(
        "module.html",
        title="🔔 Reminders",
        subtitle="Create recurring reminders and alerts.",
        module="reminders",
    )


@pages.get("/analytics")
def analytics():
    return render_template(
        "module.html",
        title="📊 Analytics",
        subtitle="Understand your progress with real data.",
        module="analytics",
    )


@pages.get("/customization")
def customization():
    return render_template(
        "module.html",
        title="🎨 Customization",
        subtitle="Customize the look and feel of Skyla.",
        module="customization",
    )


@pages.get("/settings")
def settings():
    return render_template(
        "module.html",
        title="⚙️ Settings",
        subtitle="Configure your Skyla Life OS.",
        module="settings",
    )


# =========================================================
# REMINDERS API
# =========================================================

REMINDER_REPEAT_OPTIONS = {
    "daily",
    "weekdays",
    "weekly",
    "monthly",
}

REMINDER_SOUND_TYPES = {
    "bell",
    "siren",
    "alarm",
    "chime",
}

REMINDER_PRIORITY_OPTIONS = {
    "low",
    "normal",
    "high",
    "urgent",
}

REMINDER_SNOOZE_OPTIONS = {
    5,
    10,
    15,
    30,
}


def reminder_payload(reminder):
    return {
        "id": reminder.id,
        "title": reminder.title,
        "reminder_time": reminder.reminder_time or "",
        "repeat": reminder.repeat or "daily",
        "enabled": bool(reminder.enabled),
        "sound_enabled": bool(
            reminder.sound_enabled
        ),
        "sound_type": (
            reminder.sound_type or "bell"
        ),
        "sound_volume": int(
            reminder.sound_volume
            if reminder.sound_volume is not None
            else 80
        ),
        "priority": (
            reminder.priority or "normal"
        ),
        "snooze_minutes": int(
            reminder.snooze_minutes
            if reminder.snooze_minutes is not None
            else 5
        ),
        "created_at": (
            reminder.created_at.isoformat()
            if reminder.created_at else None
        ),
    }


def validate_reminder_time(value):
    value = str(value or "").strip()

    if not value:
        return ""

    try:
        hour, minute = value.split(":")
        hour = int(hour)
        minute = int(minute)
    except (ValueError, AttributeError):
        return None

    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None

    return f"{hour:02d}:{minute:02d}"


def validate_reminder_sound_type(value):
    value = str(value or "bell").strip().lower()

    if value not in REMINDER_SOUND_TYPES:
        return None

    return value


def validate_reminder_volume(value):
    try:
        volume = int(value)
    except (TypeError, ValueError):
        return None

    if not 0 <= volume <= 100:
        return None

    return volume


def validate_reminder_priority(value):
    value = str(value or "normal").strip().lower()

    if value not in REMINDER_PRIORITY_OPTIONS:
        return None

    return value


def validate_reminder_snooze(value):
    try:
        minutes = int(value)
    except (TypeError, ValueError):
        return None

    if minutes <= 0 or minutes > 180:
        return None

    return minutes


@pages.get("/api/reminders")
def get_reminders():
    rows = Reminder.query.order_by(
        Reminder.reminder_time.asc(),
        Reminder.id.asc(),
    ).all()

    return jsonify([
        reminder_payload(row)
        for row in rows
    ])


@pages.post("/api/reminders")
def create_reminder():
    data = request.get_json() or {}

    title = str(data.get("title", "")).strip()

    if not title:
        return jsonify({
            "error": "Reminder title is required"
        }), 400

    reminder_time = validate_reminder_time(
        data.get("reminder_time", "")
    )

    if reminder_time is None:
        return jsonify({
            "error": "Time must be in HH:MM format"
        }), 400

    repeat = str(
        data.get("repeat", "daily")
    ).strip().lower()

    if repeat not in REMINDER_REPEAT_OPTIONS:
        return jsonify({
            "error": "Invalid repeat option"
        }), 400

    sound_type = validate_reminder_sound_type(
        data.get("sound_type", "bell")
    )

    if sound_type is None:
        return jsonify({
            "error": (
                "Invalid sound type. "
                "Use bell, siren, alarm or chime."
            )
        }), 400

    sound_volume = validate_reminder_volume(
        data.get("sound_volume", 80)
    )

    if sound_volume is None:
        return jsonify({
            "error": "Sound volume must be between 0 and 100"
        }), 400

    priority = validate_reminder_priority(
        data.get("priority", "normal")
    )

    if priority is None:
        return jsonify({
            "error": (
                "Invalid priority. "
                "Use low, normal, high or urgent."
            )
        }), 400

    snooze_minutes = validate_reminder_snooze(
        data.get("snooze_minutes", 5)
    )

    if snooze_minutes is None:
        return jsonify({
            "error": (
                "Snooze must be between "
                "1 and 180 minutes."
            )
        }), 400

    reminder = Reminder(
        title=title,
        reminder_time=reminder_time,
        repeat=repeat,
        enabled=bool(data.get("enabled", True)),
        sound_enabled=bool(
            data.get("sound_enabled", True)
        ),
        sound_type=sound_type,
        sound_volume=sound_volume,
        priority=priority,
        snooze_minutes=snooze_minutes,
    )

    db.session.add(reminder)
    db.session.commit()

    return jsonify(
        reminder_payload(reminder)
    ), 201


@pages.put("/api/reminders/<int:reminder_id>")
def update_reminder(reminder_id):
    reminder = db.session.get(
        Reminder,
        reminder_id,
    )

    if not reminder:
        return jsonify({
            "error": "Reminder not found"
        }), 404

    data = request.get_json() or {}

    if "title" in data:
        title = str(
            data.get("title", "")
        ).strip()

        if not title:
            return jsonify({
                "error": "Reminder title is required"
            }), 400

        reminder.title = title

    if "reminder_time" in data:
        reminder_time = validate_reminder_time(
            data.get("reminder_time", "")
        )

        if reminder_time is None:
            return jsonify({
                "error": "Time must be in HH:MM format"
            }), 400

        reminder.reminder_time = reminder_time

    if "repeat" in data:
        repeat = str(
            data.get("repeat", "daily")
        ).strip().lower()

        if repeat not in REMINDER_REPEAT_OPTIONS:
            return jsonify({
                "error": "Invalid repeat option"
            }), 400

        reminder.repeat = repeat

    if "enabled" in data:
        reminder.enabled = bool(
            data.get("enabled")
        )

    if "sound_enabled" in data:
        reminder.sound_enabled = bool(
            data.get("sound_enabled")
        )

    if "sound_type" in data:
        sound_type = validate_reminder_sound_type(
            data.get("sound_type")
        )

        if sound_type is None:
            return jsonify({
                "error": (
                    "Invalid sound type. "
                    "Use bell, siren, alarm or chime."
                )
            }), 400

        reminder.sound_type = sound_type

    if "sound_volume" in data:
        sound_volume = validate_reminder_volume(
            data.get("sound_volume")
        )

        if sound_volume is None:
            return jsonify({
                "error": (
                    "Sound volume must be between 0 and 100"
                )
            }), 400

        reminder.sound_volume = sound_volume

    if "priority" in data:
        priority = validate_reminder_priority(
            data.get("priority")
        )

        if priority is None:
            return jsonify({
                "error": (
                    "Invalid priority. "
                    "Use low, normal, high or urgent."
                )
            }), 400

        reminder.priority = priority

    if "snooze_minutes" in data:
        snooze_minutes = validate_reminder_snooze(
            data.get("snooze_minutes")
        )

        if snooze_minutes is None:
            return jsonify({
                "error": (
                    "Snooze must be between "
                    "1 and 180 minutes."
                )
            }), 400

        reminder.snooze_minutes = snooze_minutes

    db.session.commit()

    return jsonify(
        reminder_payload(reminder)
    )


@pages.post("/api/reminders/<int:reminder_id>/toggle")
def toggle_reminder(reminder_id):
    reminder = db.session.get(
        Reminder,
        reminder_id,
    )

    if not reminder:
        return jsonify({
            "error": "Reminder not found"
        }), 404

    reminder.enabled = not reminder.enabled

    db.session.commit()

    return jsonify(
        reminder_payload(reminder)
    )


@pages.post("/api/reminders/<int:reminder_id>/snooze")
def snooze_reminder(reminder_id):
    reminder = db.session.get(
        Reminder,
        reminder_id,
    )

    if not reminder:
        return jsonify({
            "error": "Reminder not found"
        }), 404

    data = request.get_json(silent=True) or {}

    raw_minutes = data.get(
        "minutes",
        getattr(reminder, "snooze_minutes", 5),
    )

    try:
        minutes = int(raw_minutes)
    except (TypeError, ValueError):
        return jsonify({
            "error": "Invalid snooze minutes"
        }), 400

    if minutes < 1 or minutes > 180:
        return jsonify({
            "error": "Snooze must be between 1 and 180 minutes"
        }), 400

    reminder.snooze_minutes = minutes
    reminder.snooze_until = datetime.now() + timedelta(
        minutes=minutes
    )

    db.session.commit()

    return jsonify({
        "ok": True,
        "id": reminder.id,
        "snooze_minutes": minutes,
        "snooze_until": (
            reminder.snooze_until.isoformat()
            if reminder.snooze_until
            else None
        ),
    })


@pages.delete("/api/reminders/<int:reminder_id>")
def delete_reminder(reminder_id):
    reminder = db.session.get(
        Reminder,
        reminder_id,
    )

    if not reminder:
        return jsonify({
            "error": "Reminder not found"
        }), 404

    db.session.delete(reminder)
    db.session.commit()

    return jsonify({
        "ok": True
    })


# =========================================================
# ANALYTICS API
# =========================================================


@pages.get("/api/reminder-history")
def get_reminder_history():
    from ..models import ReminderLog, Reminder

    rows = (
        db.session.query(ReminderLog, Reminder)
        .join(
            Reminder,
            Reminder.id == ReminderLog.reminder_id
        )
        .order_by(ReminderLog.triggered_at.desc())
        .limit(100)
        .all()
    )

    result = []

    for log, reminder in rows:
        result.append({
            "id": log.id,
            "reminder_id": reminder.id,
            "title": reminder.title,
            "triggered_at": (
                log.triggered_at.isoformat()
                if log.triggered_at else None
            ),
            "status": log.status,
        })

    return jsonify(result)


@pages.get("/api/analytics")
def analytics_data():
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    routines = Routine.query.filter_by(active=True).all()
    habits = Habit.query.filter_by(active=True).all()
    goals = Goal.query.filter_by(active=True).all()

    routine_total = len(routines)
    routine_completed_today = RoutineLog.query.filter_by(
        log_date=today,
        completed=True,
    ).count()

    routine_week_logs = RoutineLog.query.filter(
        RoutineLog.log_date >= week_start,
        RoutineLog.log_date <= today,
        RoutineLog.completed.is_(True),
    ).count()

    habit_total = len(habits)
    habit_completed_today = HabitLog.query.filter_by(
        log_date=today,
        completed=True,
    ).count()

    habit_week_logs = HabitLog.query.filter(
        HabitLog.log_date >= week_start,
        HabitLog.log_date <= today,
        HabitLog.completed.is_(True),
    ).count()

    goal_progress = 0

    if goals:
        values = []

        for goal in goals:
            target = float(goal.target or 0)

            if target > 0:
                values.append(
                    min(
                        100,
                        max(
                            0,
                            (float(goal.progress or 0) / target) * 100,
                        ),
                    )
                )

        if values:
            goal_progress = round(sum(values) / len(values))

    focus_today = db.session.query(
        db.func.coalesce(
            db.func.sum(FocusSession.duration),
            0,
        )
    ).filter(
        FocusSession.session_date == today
    ).scalar() or 0

    focus_week = db.session.query(
        db.func.coalesce(
            db.func.sum(FocusSession.duration),
            0,
        )
    ).filter(
        FocusSession.session_date >= week_start,
        FocusSession.session_date <= today,
    ).scalar() or 0

    football_today = FootballSession.query.filter(
        FootballSession.session_date == today
    ).count()

    fitness_today = FitnessWorkout.query.filter(
        FitnessWorkout.workout_date == today
    ).count()

    return jsonify({
        "date": today.isoformat(),
        "routines": {
            "total": routine_total,
            "completed_today": routine_completed_today,
            "today_percent": (
                round(
                    routine_completed_today / routine_total * 100
                )
                if routine_total else 0
            ),
            "week_completed": routine_week_logs,
        },
        "habits": {
            "total": habit_total,
            "completed_today": habit_completed_today,
            "today_percent": (
                round(
                    habit_completed_today / habit_total * 100
                )
                if habit_total else 0
            ),
            "week_completed": habit_week_logs,
        },
        "goals": {
            "total": len(goals),
            "average_progress": goal_progress,
        },
        "focus": {
            "today_minutes": int(focus_today),
            "week_minutes": int(focus_week),
        },
        "football": {
            "sessions_today": football_today,
        },
        "fitness": {
            "workouts_today": fitness_today,
        },
    })


# =========================================================
# APP SETTINGS / CUSTOMIZATION API
# =========================================================

DEFAULT_SETTINGS = {
    "theme": "dark",
    "accent": "green",
    "font_size": "medium",
    "card_density": "comfortable",
    "notifications": "on",
    "focus_mode": "off",
}


def get_app_settings():
    rows = AppSettings.query.all()

    result = dict(DEFAULT_SETTINGS)

    for row in rows:
        result[row.key] = row.value

    return result


@pages.get("/api/calendar")
def calendar_data():
    """Return calendar events for a requested month."""
    raw_year = request.args.get("year", type=int)
    raw_month = request.args.get("month", type=int)

    today = date.today()
    year = raw_year or today.year
    month = raw_month or today.month

    if month < 1 or month > 12:
        return jsonify({"error": "Month must be between 1 and 12"}), 400

    import calendar as pycalendar

    days_in_month = pycalendar.monthrange(year, month)[1]
    start_date = date(year, month, 1)
    end_date = date(year, month, days_in_month)

    events = []

    # Routine completion events
    routine_logs = (
        RoutineLog.query
        .filter(
            RoutineLog.log_date >= start_date,
            RoutineLog.log_date <= end_date,
            RoutineLog.completed == True,
        )
        .all()
    )

    routine_map = {
        r.id: r.title
        for r in Routine.query.all()
    }

    for log in routine_logs:
        events.append({
            "date": log.log_date.isoformat(),
            "type": "routine",
            "title": routine_map.get(log.routine_id, "Routine"),
            "icon": "🕒",
        })

    # Habit completion events
    habit_logs = (
        HabitLog.query
        .filter(
            HabitLog.log_date >= start_date,
            HabitLog.log_date <= end_date,
            HabitLog.completed == True,
        )
        .all()
    )

    habit_map = {
        h.id: h.name
        for h in Habit.query.all()
    }

    for log in habit_logs:
        events.append({
            "date": log.log_date.isoformat(),
            "type": "habit",
            "title": habit_map.get(log.habit_id, "Habit"),
            "icon": "🔥",
        })

    # Goal deadline events
    goals = (
        Goal.query
        .filter(
            Goal.deadline >= start_date,
            Goal.deadline <= end_date,
        )
        .all()
    )

    for goal in goals:
        events.append({
            "date": goal.deadline.isoformat(),
            "type": "goal",
            "title": goal.title,
            "icon": "🎯",
            "progress": goal.progress,
            "target": goal.target,
        })

    # Reminder events
    # Expand recurring reminders across the requested month.
    reminders = Reminder.query.filter_by(enabled=True).all()

    for reminder in reminders:
        repeat = (reminder.repeat or "daily").strip().lower()

        for day_number in range(1, days_in_month + 1):
            event_date = date(year, month, day_number)

            should_show = False

            if repeat == "daily":
                should_show = True

            elif repeat == "weekdays":
                should_show = event_date.weekday() < 5

            elif repeat == "weekly":
                # Current weekly reminder semantics:
                # Monday is the recurring weekday.
                should_show = event_date.weekday() == 0

            elif repeat == "monthly":
                # Current monthly reminder semantics:
                # first day of each month.
                should_show = event_date.day == 1

            if should_show:
                events.append({
                    "date": event_date.isoformat(),
                    "type": "reminder",
                    "title": reminder.title,
                    "icon": "🔔",
                    "time": reminder.reminder_time,
                    "repeat": reminder.repeat,
                })

    # Personal calendar events
    # Expand enabled personal events across the requested month.
    personal_events = CalendarEvent.query.filter_by(enabled=True).all()

    for personal_event in personal_events:
        repeat = (personal_event.repeat or "none").strip().lower()
        source_date = personal_event.event_date

        for day_number in range(1, days_in_month + 1):
            event_date = date(year, month, day_number)
            should_show = False

            if repeat == "none":
                should_show = event_date == source_date

            elif repeat == "daily":
                should_show = event_date >= source_date

            elif repeat == "weekly":
                should_show = (
                    event_date >= source_date
                    and event_date.weekday() == source_date.weekday()
                )

            elif repeat == "monthly":
                should_show = (
                    event_date >= source_date
                    and event_date.day == source_date.day
                )

            if should_show:
                events.append({
                    "date": event_date.isoformat(),
                    "type": "event",
                    "title": personal_event.title,
                    "icon": "📌",
                    "time": personal_event.event_time or "",
                    "repeat": personal_event.repeat or "none",
                    "description": personal_event.description or "",
                    "event_id": personal_event.id,
                })

    return jsonify({
        "year": year,
        "month": month,
        "today": today.isoformat(),
        "days_in_month": days_in_month,
        "events": events,
    })


@pages.get("/api/settings")
def get_settings():
    return jsonify(get_app_settings())


@pages.put("/api/settings")
def update_settings():
    data = request.get_json() or {}

    allowed = {
        "theme": {"dark", "light"},
        "accent": {"green", "blue", "purple", "orange"},
        "font_size": {"small", "medium", "large"},
        "card_density": {"compact", "comfortable", "large"},
        "notifications": {"on", "off"},
        "focus_mode": {"on", "off"},
    }

    for key, value in data.items():
        if key not in allowed:
            continue

        value = str(value).lower()

        if value not in allowed[key]:
            return jsonify({
                "error": f"Invalid value for {key}"
            }), 400

        row = AppSettings.query.filter_by(key=key).first()

        if not row:
            row = AppSettings(key=key, value=value)
            db.session.add(row)
        else:
            row.value = value

    db.session.commit()

    return jsonify(get_app_settings())

# =========================================================
# PERSONAL CALENDAR EVENTS
# =========================================================

def calendar_event_payload(event):
    return {
        "id": event.id,
        "title": event.title,
        "date": event.event_date.isoformat(),
        "time": event.event_time or "",
        "description": event.description or "",
        "repeat": event.repeat or "none",
        "enabled": bool(event.enabled),
    }


@pages.get("/api/calendar/events")
def calendar_events():
    events = (
        CalendarEvent.query
        .order_by(CalendarEvent.event_date.asc(), CalendarEvent.event_time.asc())
        .all()
    )

    return jsonify({
        "events": [calendar_event_payload(event) for event in events]
    })


@pages.post("/api/calendar/events")
def create_calendar_event():
    data = request.get_json(silent=True) or {}

    title = str(data.get("title", "")).strip()
    event_date = str(data.get("date", "")).strip()
    event_time = str(data.get("time", "")).strip()
    description = str(data.get("description", "")).strip()
    repeat = str(data.get("repeat", "none")).strip().lower()
    enabled = bool(data.get("enabled", True))

    if not title:
        return jsonify({"error": "Title is required"}), 400

    if not event_date:
        return jsonify({"error": "Date is required"}), 400

    try:
        parsed_date = date.fromisoformat(event_date)
    except ValueError:
        return jsonify({"error": "Invalid date"}), 400

    allowed_repeat = {"none", "daily", "weekly", "monthly"}
    if repeat not in allowed_repeat:
        return jsonify({"error": "Invalid repeat value"}), 400

    event = CalendarEvent(
        title=title,
        event_date=parsed_date,
        event_time=event_time or None,
        description=description or None,
        repeat=repeat,
        enabled=enabled,
    )

    db.session.add(event)
    db.session.commit()

    return jsonify({
        "ok": True,
        "event": calendar_event_payload(event),
    }), 201


@pages.put("/api/calendar/events/<int:event_id>")
def update_calendar_event(event_id):
    event = db.session.get(CalendarEvent, event_id)

    if event is None:
        return jsonify({"error": "Calendar event not found"}), 404

    data = request.get_json(silent=True) or {}

    if "title" in data:
        title = str(data.get("title", "")).strip()
        if not title:
            return jsonify({"error": "Title is required"}), 400
        event.title = title

    if "date" in data:
        try:
            event.event_date = date.fromisoformat(
                str(data.get("date", "")).strip()
            )
        except ValueError:
            return jsonify({"error": "Invalid date"}), 400

    if "time" in data:
        event.event_time = str(data.get("time", "")).strip() or None

    if "description" in data:
        event.description = str(data.get("description", "")).strip() or None

    if "repeat" in data:
        repeat = str(data.get("repeat", "none")).strip().lower()
        if repeat not in {"none", "daily", "weekly", "monthly"}:
            return jsonify({"error": "Invalid repeat value"}), 400
        event.repeat = repeat

    if "enabled" in data:
        event.enabled = bool(data.get("enabled"))

    db.session.commit()

    return jsonify({
        "ok": True,
        "event": calendar_event_payload(event),
    })


@pages.delete("/api/calendar/events/<int:event_id>")
def delete_calendar_event(event_id):
    event = db.session.get(CalendarEvent, event_id)

    if event is None:
        return jsonify({"error": "Calendar event not found"}), 404

    db.session.delete(event)
    db.session.commit()

    return jsonify({
        "ok": True,
        "message": "Calendar event deleted",
    })

