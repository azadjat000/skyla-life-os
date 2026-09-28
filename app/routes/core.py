from datetime import date, datetime
from flask import Blueprint, jsonify, request, render_template
from app.extensions import db
from app.models import Routine, RoutineLog, Habit, HabitLog, Goal

core = Blueprint("core", __name__)


# =========================
# ROUTINE
# =========================

@core.get("/api/routines")
def get_routines():
    rows = Routine.query.order_by(
        Routine.time.asc(),
        Routine.id.asc()
    ).all()

    today = date.today()

    result = []

    for r in rows:
        completed_today = RoutineLog.query.filter_by(
            routine_id=r.id,
            log_date=today,
            completed=True
        ).first() is not None

        result.append({
            "id": r.id,
            "title": r.title,
            "category": r.category,
            "time": r.time,
            "description": r.description,
            "repeat": r.repeat,
            "active": r.active,
            "completed_today": completed_today,
            "today": today.isoformat()
        })

    return jsonify(result)


@core.post("/api/routines")
def create_routine():
    data = request.get_json() or {}

    title = str(data.get("title", "")).strip()
    if not title:
        return jsonify({"error": "Title required"}), 400

    routine = Routine(
        title=title,
        category=data.get("category", "General"),
        time=data.get("time", ""),
        description=data.get("description", ""),
        repeat=data.get("repeat", "Daily"),
        active=True
    )

    db.session.add(routine)
    db.session.commit()

    return jsonify({"ok": True, "id": routine.id}), 201


@core.put("/api/routines/<int:routine_id>")
def update_routine(routine_id):
    routine = db.session.get(Routine, routine_id)

    if not routine:
        return jsonify({"error": "Routine not found"}), 404

    data = request.get_json() or {}

    for field in ["title", "category", "time", "description", "repeat"]:
        if field in data:
            setattr(routine, field, data[field])

    if "active" in data:
        routine.active = bool(data["active"])

    db.session.commit()

    return jsonify({"ok": True})


@core.post("/api/routines/<int:routine_id>/toggle")
def toggle_routine(routine_id):
    routine = db.session.get(Routine, routine_id)

    if not routine:
        return jsonify({"error": "Routine not found"}), 404

    today = date.today()

    log = RoutineLog.query.filter_by(
        routine_id=routine.id,
        log_date=today
    ).first()

    if log:
        log.completed = not log.completed
    else:
        log = RoutineLog(
            routine_id=routine.id,
            log_date=today,
            completed=True,
            completed_at=datetime.utcnow()
        )
        db.session.add(log)

    if log.completed:
        log.completed_at = datetime.utcnow()
    else:
        log.completed_at = None

    db.session.commit()

    return jsonify({
        "ok": True,
        "completed": log.completed,
        "date": today.isoformat()
    })


@core.delete("/api/routines/<int:routine_id>")
def delete_routine(routine_id):
    routine = db.session.get(Routine, routine_id)

    if not routine:
        return jsonify({"error": "Routine not found"}), 404

    RoutineLog.query.filter_by(
        routine_id=routine.id
    ).delete()

    db.session.delete(routine)
    db.session.commit()

    return jsonify({"ok": True})


# =========================
# HABITS
# =========================

def calculate_habit_streak(habit_id, end_date=None):
    """Calculate the real consecutive completed-day streak."""
    if end_date is None:
        end_date = date.today()

    logs = HabitLog.query.filter_by(
        habit_id=habit_id,
        completed=True
    ).order_by(HabitLog.log_date.desc()).all()

    completed_dates = {log.log_date for log in logs}

    streak = 0
    cursor = end_date

    while cursor in completed_dates:
        streak += 1
        cursor = cursor.fromordinal(cursor.toordinal() - 1)

    return streak


def habit_month_calendar(habit_id, year=None, month=None):
    """Return completion status for every day in a calendar month."""
    today = date.today()

    year = year or today.year
    month = month or today.month

    if month < 1 or month > 12:
        raise ValueError("Invalid month")

    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)

    days_in_month = (next_month - date(year, month, 1)).days

    logs = HabitLog.query.filter_by(
        habit_id=habit_id,
        completed=True
    ).all()

    completed_dates = {log.log_date for log in logs}

    return [
        {
            "date": date(year, month, day).isoformat(),
            "day": day,
            "completed": date(year, month, day) in completed_dates,
            "today": date(year, month, day) == today
        }
        for day in range(1, days_in_month + 1)
    ]


def habit_stats(habit_id):
    """Return useful completion statistics for a habit."""
    today = date.today()

    logs = HabitLog.query.filter_by(
        habit_id=habit_id,
        completed=True
    ).all()

    completed_dates = {log.log_date for log in logs}

    streak = calculate_habit_streak(habit_id, today)

    last_7_days = [
        today.fromordinal(today.toordinal() - i)
        for i in range(7)
    ]

    completed_7_days = sum(
        1 for day in last_7_days
        if day in completed_dates
    )

    month_start = today.replace(day=1)

    completed_this_month = sum(
        1 for day in completed_dates
        if day.year == today.year and day.month == today.month
    )

    days_elapsed = today.day
    monthly_completion = round(
        (completed_this_month / days_elapsed) * 100
    ) if days_elapsed else 0

    week = [
        {
            "date": day.isoformat(),
            "completed": day in completed_dates
        }
        for day in reversed(last_7_days)
    ]

    return {
        "streak": streak,
        "completed_7_days": completed_7_days,
        "weekly_completion": round((completed_7_days / 7) * 100),
        "completed_this_month": completed_this_month,
        "monthly_completion": min(100, monthly_completion),
        "total_completed": len(completed_dates),
        "week": week,
    }



@core.get("/api/habits")
def get_habits():
    rows = Habit.query.order_by(Habit.id.desc()).all()

    today = date.today()

    result = []

    for h in rows:
        completed_today = HabitLog.query.filter_by(
            habit_id=h.id,
            log_date=today,
            completed=True
        ).first() is not None

        stats = habit_stats(h.id)

        result.append({
            "id": h.id,
            "name": h.name,
            "category": h.category,
            "target_days": h.target_days,
            "streak": stats["streak"],
            "completed_today": completed_today,
            "active": h.active,
            "today": today.isoformat(),
            "completed_7_days": stats["completed_7_days"],
            "weekly_completion": stats["weekly_completion"],
            "completed_this_month": stats["completed_this_month"],
            "monthly_completion": stats["monthly_completion"],
            "total_completed": stats["total_completed"],
            "week": stats["week"],
            "month": habit_month_calendar(h.id)
        })

    return jsonify(result)


@core.post("/api/habits")
def create_habit():
    data = request.get_json() or {}

    name = str(data.get("name", "")).strip()

    if not name:
        return jsonify({"error": "Habit name required"}), 400

    habit = Habit(
        name=name,
        category=data.get("category", "General"),
        target_days=int(data.get("target_days", 7)),
        streak=0,
        completed_today=False,
        active=True
    )

    db.session.add(habit)
    db.session.commit()

    return jsonify({"ok": True, "id": habit.id}), 201


@core.put("/api/habits/<int:habit_id>")
def update_habit(habit_id):
    habit = db.session.get(Habit, habit_id)

    if not habit:
        return jsonify({"error": "Habit not found"}), 404

    data = request.get_json() or {}

    if "name" in data:
        name = str(data["name"]).strip()
        if not name:
            return jsonify({"error": "Habit name required"}), 400
        habit.name = name

    if "category" in data:
        habit.category = str(data["category"]).strip() or "General"

    if "target_days" in data:
        try:
            target_days = int(data["target_days"])
        except (TypeError, ValueError):
            return jsonify({"error": "Target days must be a number"}), 400

        if target_days < 1 or target_days > 7:
            return jsonify({"error": "Target days must be between 1 and 7"}), 400

        habit.target_days = target_days

    if "active" in data:
        habit.active = bool(data["active"])

    db.session.commit()

    return jsonify({
        "ok": True,
        "id": habit.id
    })


@core.post("/api/habits/<int:habit_id>/toggle")
def toggle_habit(habit_id):
    habit = db.session.get(Habit, habit_id)

    if not habit:
        return jsonify({"error": "Habit not found"}), 404

    today = date.today()

    log = HabitLog.query.filter_by(
        habit_id=habit.id,
        log_date=today
    ).first()

    if log:
        log.completed = not log.completed
    else:
        log = HabitLog(
            habit_id=habit.id,
            log_date=today,
            completed=True
        )
        db.session.add(log)

    habit.completed_today = log.completed

    db.session.flush()

    # Recalculate from actual historical logs instead of +/- 1.
    habit.streak = calculate_habit_streak(habit.id, today)

    db.session.commit()

    stats = habit_stats(habit.id)

    return jsonify({
        "ok": True,
        "completed": log.completed,
        "streak": stats["streak"],
        "completed_7_days": stats["completed_7_days"],
        "weekly_completion": stats["weekly_completion"],
        "completed_this_month": stats["completed_this_month"],
        "monthly_completion": stats["monthly_completion"],
        "total_completed": stats["total_completed"],
        "week": stats["week"]
    })


@core.delete("/api/habits/<int:habit_id>")
def delete_habit(habit_id):
    habit = db.session.get(Habit, habit_id)

    if not habit:
        return jsonify({"error": "Habit not found"}), 404

    HabitLog.query.filter_by(habit_id=habit.id).delete()
    db.session.delete(habit)
    db.session.commit()

    return jsonify({"ok": True})


# =========================
# GOALS
# =========================

@core.get("/api/goals")
def get_goals():
    rows = Goal.query.order_by(Goal.id.desc()).all()

    return jsonify([
        {
            "id": g.id,
            "title": g.title,
            "category": g.category,
            "description": g.description,
            "progress": g.progress,
            "target": g.target,
            "deadline": g.deadline,
            "active": g.active
        }
        for g in rows
    ])


@core.post("/api/goals")
def create_goal():
    data = request.get_json() or {}

    title = str(data.get("title", "")).strip()

    if not title:
        return jsonify({"error": "Goal title required"}), 400

    try:
        progress = float(data.get("progress", 0))
        target = float(data.get("target", 100))
    except (TypeError, ValueError):
        return jsonify({"error": "Progress and target must be numbers"}), 400

    if target <= 0:
        return jsonify({"error": "Target must be greater than 0"}), 400

    if progress < 0:
        return jsonify({"error": "Progress cannot be negative"}), 400

    progress = min(progress, target)

    deadline_raw = str(data.get("deadline", "") or "").strip()
    deadline = None

    if deadline_raw:
        try:
            deadline = date.fromisoformat(deadline_raw)
        except ValueError:
            return jsonify({"error": "Deadline must be YYYY-MM-DD"}), 400

    goal = Goal(
        title=title,
        category=str(data.get("category", "General") or "General").strip(),
        description=str(data.get("description", "") or "").strip(),
        progress=progress,
        target=target,
        deadline=deadline,
        active=True
    )

    db.session.add(goal)
    db.session.commit()

    return jsonify({"ok": True, "id": goal.id}), 201


@core.put("/api/goals/<int:goal_id>")
def update_goal(goal_id):
    goal = db.session.get(Goal, goal_id)

    if not goal:
        return jsonify({"error": "Goal not found"}), 404

    data = request.get_json() or {}

    for field in ["title", "category", "description"]:
        if field in data:
            setattr(goal, field, data[field])

    if "deadline" in data:
        deadline_raw = str(data.get("deadline", "") or "").strip()

        if deadline_raw:
            try:
                goal.deadline = date.fromisoformat(deadline_raw)
            except ValueError:
                return jsonify({"error": "Deadline must be YYYY-MM-DD"}), 400
        else:
            goal.deadline = None

    if "progress" in data:
        goal.progress = float(data["progress"])

    if "target" in data:
        goal.target = float(data["target"])

    if "active" in data:
        goal.active = bool(data["active"])

    db.session.commit()

    return jsonify({"ok": True})


@core.delete("/api/goals/<int:goal_id>")
def delete_goal(goal_id):
    goal = db.session.get(Goal, goal_id)

    if not goal:
        return jsonify({"error": "Goal not found"}), 404

    db.session.delete(goal)
    db.session.commit()

    return jsonify({"ok": True})


# =========================
# FUNCTIONAL PAGES
# =========================

@core.get("/daily-routine")
def routine_page():
    return render_template("core.html", module="routine")


@core.get("/habits")
def habits_page():
    return render_template("core.html", module="habits")


@core.get("/goals")
def goals_page():
    return render_template("core.html", module="goals")
