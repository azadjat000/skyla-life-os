from datetime import date, timedelta

from flask import Blueprint, jsonify, request, render_template

from app.extensions import db
from app.models import (
    Routine,
    RoutineLog,
    Habit,
    HabitLog,
    FocusSession,
)

discipline = Blueprint("discipline", __name__)


def _routine_payload(routine, today):
    completed = RoutineLog.query.filter_by(
        routine_id=routine.id,
        log_date=today,
        completed=True,
    ).first() is not None

    return {
        "id": routine.id,
        "title": routine.title,
        "category": routine.category,
        "time": routine.time,
        "description": routine.description or "",
        "repeat": routine.repeat or "daily",
        "active": bool(routine.active),
        "completed_today": completed,
    }


def _habit_payload(habit, today):
    completed = HabitLog.query.filter_by(
        habit_id=habit.id,
        log_date=today,
        completed=True,
    ).first() is not None

    return {
        "id": habit.id,
        "name": habit.name,
        "category": habit.category or "general",
        "streak": habit.streak or 0,
        "target_days": habit.target_days or 7,
        "active": bool(habit.active),
        "completed_today": completed,
    }


def _calculate_routine_streak(routine_id, today):
    streak = 0
    current = today

    while True:
        completed = RoutineLog.query.filter_by(
            routine_id=routine_id,
            log_date=current,
            completed=True,
        ).first()

        if not completed:
            break

        streak += 1
        current -= timedelta(days=1)

    return streak


def _calculate_habit_streak(habit_id, today):
    streak = 0
    current = today

    while True:
        completed = HabitLog.query.filter_by(
            habit_id=habit_id,
            log_date=current,
            completed=True,
        ).first()

        if not completed:
            break

        streak += 1
        current -= timedelta(days=1)

    return streak


@discipline.get("/discipline")
def discipline_page():
    return render_template("discipline.html")


@discipline.get("/api/discipline")
def get_discipline():
    today = date.today()

    routines = (
        Routine.query
        .filter_by(category="discipline")
        .order_by(Routine.time.asc(), Routine.id.asc())
        .all()
    )

    habits = (
        Habit.query
        .filter_by(active=True)
        .order_by(Habit.id.asc())
        .all()
    )

    routine_items = [
        _routine_payload(routine, today)
        for routine in routines
    ]

    habit_items = [
        _habit_payload(habit, today)
        for habit in habits
    ]

    active_routines = [
        routine for routine in routine_items
        if routine["active"]
    ]

    completed_routines = [
        routine for routine in active_routines
        if routine["completed_today"]
    ]

    active_habits = [
        habit for habit in habit_items
        if habit["active"]
    ]

    completed_habits = [
        habit for habit in active_habits
        if habit["completed_today"]
    ]

    today_focus = (
        db.session.query(db.func.coalesce(db.func.sum(FocusSession.duration), 0))
        .filter(FocusSession.session_date == today)
        .scalar()
        or 0
    )

    routine_progress = (
        round(
            len(completed_routines) / len(active_routines) * 100
        )
        if active_routines else 0
    )

    habit_progress = (
        round(
            len(completed_habits) / len(active_habits) * 100
        )
        if active_habits else 0
    )

    return jsonify({
        "date": today.isoformat(),

        "stats": {
            "total_routines": len(routines),
            "active_routines": len(active_routines),
            "completed_routines": len(completed_routines),
            "routine_progress": routine_progress,

            "total_habits": len(habits),
            "active_habits": len(active_habits),
            "completed_habits": len(completed_habits),
            "habit_progress": habit_progress,

            "focus_minutes_today": int(today_focus),
        },

        "routines": routine_items,
        "habits": habit_items,
    })


@discipline.post("/api/discipline")
def add_discipline():
    data = request.get_json() or {}

    title = str(data.get("title", "")).strip()

    if not title:
        return jsonify({
            "error": "Routine title is required"
        }), 400

    repeat = str(
        data.get("repeat", "daily")
    ).strip() or "daily"

    item = Routine(
        title=title,
        category="discipline",
        time=str(data.get("time", "")).strip(),
        description=str(
            data.get("description", "")
        ).strip(),
        repeat=repeat,
        active=bool(data.get("active", True)),
    )

    db.session.add(item)
    db.session.commit()

    return jsonify({
        "ok": True,
        "id": item.id,
        "routine": _routine_payload(item, date.today()),
    }), 201


@discipline.post("/api/discipline/<int:item_id>/toggle")
def toggle_discipline(item_id):
    item = Routine.query.get_or_404(item_id)

    if item.category != "discipline":
        return jsonify({
            "error": "Not a discipline routine"
        }), 404

    item.active = not bool(item.active)
    db.session.commit()

    return jsonify({
        "ok": True,
        "active": bool(item.active),
    })


@discipline.post("/api/discipline/<int:item_id>/complete")
def complete_discipline(item_id):
    item = Routine.query.get_or_404(item_id)

    if item.category != "discipline":
        return jsonify({
            "error": "Not a discipline routine"
        }), 404

    today = date.today()

    log = RoutineLog.query.filter_by(
        routine_id=item.id,
        log_date=today,
    ).first()

    if log is None:
        log = RoutineLog(
            routine_id=item.id,
            log_date=today,
        )
        db.session.add(log)

    log.completed = True

    db.session.commit()

    return jsonify({
        "ok": True,
        "completed": True,
        "streak": _calculate_routine_streak(
            item.id,
            today,
        ),
    })


@discipline.post("/api/discipline/<int:item_id>/undo")
def undo_discipline(item_id):
    item = Routine.query.get_or_404(item_id)

    if item.category != "discipline":
        return jsonify({
            "error": "Not a discipline routine"
        }), 404

    today = date.today()

    log = RoutineLog.query.filter_by(
        routine_id=item.id,
        log_date=today,
    ).first()

    if log:
        log.completed = False
        db.session.commit()

    return jsonify({
        "ok": True,
        "completed": False,
    })


@discipline.delete("/api/discipline/<int:item_id>")
def delete_discipline(item_id):
    item = Routine.query.get_or_404(item_id)

    if item.category != "discipline":
        return jsonify({
            "error": "Not a discipline routine"
        }), 404

    RoutineLog.query.filter_by(
        routine_id=item.id
    ).delete()

    db.session.delete(item)
    db.session.commit()

    return jsonify({"ok": True})


@discipline.get("/api/discipline/streaks")
def discipline_streaks():
    today = date.today()

    routines = (
        Routine.query
        .filter_by(category="discipline", active=True)
        .order_by(Routine.id.asc())
        .all()
    )

    habits = (
        Habit.query
        .filter_by(active=True)
        .order_by(Habit.id.asc())
        .all()
    )

    routine_streaks = [
        {
            "id": routine.id,
            "title": routine.title,
            "streak": _calculate_routine_streak(
                routine.id,
                today,
            ),
        }
        for routine in routines
    ]

    habit_streaks = [
        {
            "id": habit.id,
            "name": habit.name,
            "streak": _calculate_habit_streak(
                habit.id,
                today,
            ),
        }
        for habit in habits
    ]

    return jsonify({
        "date": today.isoformat(),
        "routines": routine_streaks,
        "habits": habit_streaks,
    })


@discipline.get("/api/discipline/focus")
def discipline_focus():
    today = date.today()

    sessions = (
        FocusSession.query
        .filter_by(session_date=today)
        .order_by(FocusSession.id.desc())
        .all()
    )

    total_minutes = sum(
        int(session.duration or 0)
        for session in sessions
    )

    return jsonify({
        "date": today.isoformat(),
        "total_minutes": total_minutes,
        "sessions": [
            {
                "id": session.id,
                "duration": int(session.duration or 0),
                "notes": session.notes or "",
                "goal_id": session.goal_id,
            }
            for session in sessions
        ],
    })
