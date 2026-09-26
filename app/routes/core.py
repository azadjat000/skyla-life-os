from datetime import date
from flask import Blueprint, jsonify, request, render_template
from app.extensions import db
from app.models import Routine, Habit, HabitLog, Goal

core = Blueprint("core", __name__)


# =========================
# ROUTINE
# =========================

@core.get("/api/routines")
def get_routines():
    rows = Routine.query.order_by(Routine.time.asc(), Routine.id.asc()).all()

    return jsonify([
        {
            "id": r.id,
            "title": r.title,
            "category": r.category,
            "time": r.time,
            "description": r.description,
            "repeat": r.repeat,
            "active": r.active
        }
        for r in rows
    ])


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


@core.delete("/api/routines/<int:routine_id>")
def delete_routine(routine_id):
    routine = db.session.get(Routine, routine_id)

    if not routine:
        return jsonify({"error": "Routine not found"}), 404

    db.session.delete(routine)
    db.session.commit()

    return jsonify({"ok": True})


# =========================
# HABITS
# =========================

@core.get("/api/habits")
def get_habits():
    rows = Habit.query.order_by(Habit.id.desc()).all()

    today = date.today().isoformat()

    result = []

    for h in rows:
        completed = HabitLog.query.filter_by(
            habit_id=h.id,
            log_date=date.today(),
            completed=True
        ).first() is not None

        result.append({
            "id": h.id,
            "name": h.name,
            "category": h.category,
            "target_days": h.target_days,
            "streak": h.streak,
            "completed_today": completed,
            "active": h.active,
            "today": today
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

    if log.completed:
        habit.streak += 1
    elif habit.streak > 0:
        habit.streak -= 1

    habit.completed_today = log.completed

    db.session.commit()

    return jsonify({
        "ok": True,
        "completed": log.completed,
        "streak": habit.streak
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

    goal = Goal(
        title=title,
        category=data.get("category", "General"),
        description=data.get("description", ""),
        progress=float(data.get("progress", 0)),
        target=float(data.get("target", 100)),
        deadline=data.get("deadline", ""),
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

    for field in ["title", "category", "description", "deadline"]:
        if field in data:
            setattr(goal, field, data[field])

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
