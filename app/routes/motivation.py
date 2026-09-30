from flask import Blueprint, jsonify, request, render_template
from datetime import datetime, date, timedelta
from app.extensions import db
from app.models import Motivation, Routine, RoutineLog

motivation = Blueprint("motivation", __name__)


def motivation_payload(item):
    return {
        "id": item.id,
        "title": item.title,
        "message": item.message,
        "category": item.category or "daily",
        "reason": item.reason or "",
        "vision": item.vision or "",
        "reward": item.reward or "",
        "morning_reflection": item.morning_reflection or "",
        "evening_reflection": item.evening_reflection or "",
        "active": bool(item.active),
        "created_at": (
            item.created_at.isoformat()
            if item.created_at else None
        ),
    }


@motivation.get("/motivation")
def motivation_page():
    return render_template("motivation.html")


@motivation.get("/api/motivation")
def get_motivation():
    rows = Motivation.query.order_by(Motivation.id.desc()).all()
    return jsonify([motivation_payload(row) for row in rows])


@motivation.post("/api/motivation")
def add_motivation():
    data = request.get_json() or {}

    title = str(data.get("title", "")).strip()
    message = str(data.get("message", "")).strip()

    if not title:
        return jsonify({"error": "Title is required"}), 400

    if not message:
        return jsonify({"error": "Message is required"}), 400

    category = str(data.get("category", "daily")).strip() or "daily"
    reason = str(data.get("reason", "")).strip()
    vision = str(data.get("vision", "")).strip()
    reward = str(data.get("reward", "")).strip()
    morning_reflection = str(
        data.get("morning_reflection", "")
    ).strip()
    evening_reflection = str(
        data.get("evening_reflection", "")
    ).strip()

    item = Motivation(
        title=title,
        message=message,
        category=category,
        reason=reason,
        vision=vision,
        reward=reward,
        morning_reflection=morning_reflection,
        evening_reflection=evening_reflection,
        active=bool(data.get("active", True)),
    )

    db.session.add(item)
    db.session.commit()

    return jsonify({
        "ok": True,
        "item": motivation_payload(item),
    }), 201


@motivation.put("/api/motivation/<int:item_id>")
def update_motivation(item_id):
    item = Motivation.query.get_or_404(item_id)
    data = request.get_json() or {}

    if "title" in data:
        title = str(data.get("title", "")).strip()
        if not title:
            return jsonify({"error": "Title is required"}), 400
        item.title = title

    if "message" in data:
        message = str(data.get("message", "")).strip()
        if not message:
            return jsonify({"error": "Message is required"}), 400
        item.message = message

    text_fields = [
        "category",
        "reason",
        "vision",
        "reward",
        "morning_reflection",
        "evening_reflection",
    ]

    for field in text_fields:
        if field in data:
            value = str(data.get(field, "") or "").strip()

            if field == "category":
                value = value or "daily"

            setattr(item, field, value)

    if "active" in data:
        item.active = bool(data.get("active"))

    db.session.commit()

    return jsonify({
        "ok": True,
        "item": motivation_payload(item),
    })


@motivation.post("/api/motivation/<int:item_id>/toggle")
def toggle_motivation(item_id):
    item = Motivation.query.get_or_404(item_id)
    item.active = not bool(item.active)

    db.session.commit()

    return jsonify({
        "ok": True,
        "active": bool(item.active),
    })


@motivation.delete("/api/motivation/<int:item_id>")
def delete_motivation(item_id):
    item = Motivation.query.get_or_404(item_id)

    db.session.delete(item)
    db.session.commit()

    return jsonify({"ok": True})


# =========================================================
# MOTIVATION ROUTINES
# =========================================================

def motivation_routine_payload(routine):
    today = date.today()

    log = RoutineLog.query.filter_by(
        routine_id=routine.id,
        log_date=today
    ).first()

    return {
        "id": routine.id,
        "title": routine.title,
        "time": routine.time or "",
        "description": routine.description or "",
        "repeat": routine.repeat or "daily",
        "active": bool(routine.active),
        "completed_today": bool(log and log.completed),
        "category": "motivation",
    }


def motivation_routine_streak(routine_id):
    current = date.today()
    streak = 0

    while True:
        log = RoutineLog.query.filter_by(
            routine_id=routine_id,
            log_date=current,
            completed=True
        ).first()

        if not log:
            break

        streak += 1
        current = current - timedelta(days=1)

    return streak


@motivation.get("/api/motivation/routines")
def get_motivation_routines():
    routines = (
        Routine.query
        .filter_by(category="motivation")
        .order_by(Routine.time.asc(), Routine.id.asc())
        .all()
    )

    active = [r for r in routines if r.active]
    completed = sum(
        1 for r in active
        if motivation_routine_payload(r)["completed_today"]
    )

    progress = (
        round(completed / len(active) * 100)
        if active else 0
    )

    return jsonify({
        "routines": [
            {
                **motivation_routine_payload(r),
                "streak": motivation_routine_streak(r.id),
            }
            for r in routines
        ],
        "stats": {
            "total_routines": len(routines),
            "active_routines": len(active),
            "completed_routines": completed,
            "routine_progress": progress,
        }
    })


@motivation.post("/api/motivation/routines")
def add_motivation_routine():
    data = request.get_json() or {}

    title = str(data.get("title", "")).strip()

    if not title:
        return jsonify({"error": "Routine title is required"}), 400

    item = Routine(
        title=title,
        category="motivation",
        time=str(data.get("time", "") or "").strip(),
        description=str(data.get("description", "") or "").strip(),
        repeat=str(data.get("repeat", "daily") or "daily").strip().lower(),
        active=bool(data.get("active", True)),
    )

    db.session.add(item)
    db.session.commit()

    return jsonify({
        "ok": True,
        "routine": {
            **motivation_routine_payload(item),
            "streak": 0,
        }
    }), 201


@motivation.put("/api/motivation/routines/<int:routine_id>")
def update_motivation_routine(routine_id):
    item = Routine.query.get_or_404(routine_id)

    if item.category != "motivation":
        return jsonify({"error": "Not a motivation routine"}), 400

    data = request.get_json() or {}

    if "title" in data:
        title = str(data.get("title", "")).strip()
        if not title:
            return jsonify({"error": "Routine title is required"}), 400
        item.title = title

    if "time" in data:
        item.time = str(data.get("time", "") or "").strip()

    if "description" in data:
        item.description = str(
            data.get("description", "") or ""
        ).strip()

    if "repeat" in data:
        item.repeat = str(
            data.get("repeat", "daily") or "daily"
        ).strip().lower()

    if "active" in data:
        item.active = bool(data.get("active"))

    db.session.commit()

    return jsonify({
        "ok": True,
        "routine": {
            **motivation_routine_payload(item),
            "streak": motivation_routine_streak(item.id),
        }
    })


@motivation.post("/api/motivation/routines/<int:routine_id>/toggle")
def toggle_motivation_routine(routine_id):
    item = Routine.query.get_or_404(routine_id)

    if item.category != "motivation":
        return jsonify({"error": "Not a motivation routine"}), 400

    item.active = not bool(item.active)
    db.session.commit()

    return jsonify({
        "ok": True,
        "active": bool(item.active)
    })


@motivation.post("/api/motivation/routines/<int:routine_id>/complete")
def complete_motivation_routine(routine_id):
    item = Routine.query.get_or_404(routine_id)

    if item.category != "motivation":
        return jsonify({"error": "Not a motivation routine"}), 400

    today = date.today()

    log = RoutineLog.query.filter_by(
        routine_id=item.id,
        log_date=today
    ).first()

    if not log:
        log = RoutineLog(
            routine_id=item.id,
            log_date=today,
            completed=True,
            completed_at=datetime.utcnow()
        )
        db.session.add(log)
    else:
        log.completed = True
        log.completed_at = datetime.utcnow()

    db.session.commit()

    return jsonify({
        "ok": True,
        "completed_today": True,
        "streak": motivation_routine_streak(item.id)
    })


@motivation.post("/api/motivation/routines/<int:routine_id>/undo")
def undo_motivation_routine(routine_id):
    item = Routine.query.get_or_404(routine_id)

    if item.category != "motivation":
        return jsonify({"error": "Not a motivation routine"}), 400

    today = date.today()

    log = RoutineLog.query.filter_by(
        routine_id=item.id,
        log_date=today
    ).first()

    if log:
        db.session.delete(log)
        db.session.commit()

    return jsonify({
        "ok": True,
        "completed_today": False,
        "streak": motivation_routine_streak(item.id)
    })


@motivation.delete("/api/motivation/routines/<int:routine_id>")
def delete_motivation_routine(routine_id):
    item = Routine.query.get_or_404(routine_id)

    if item.category != "motivation":
        return jsonify({"error": "Not a motivation routine"}), 400

    RoutineLog.query.filter_by(
        routine_id=item.id
    ).delete()

    db.session.delete(item)
    db.session.commit()

    return jsonify({"ok": True})


@motivation.get("/api/motivation/routines/streaks")
def motivation_routine_streaks():
    routines = (
        Routine.query
        .filter_by(category="motivation")
        .order_by(Routine.id.asc())
        .all()
    )

    return jsonify({
        "routines": [
            {
                "id": routine.id,
                "title": routine.title,
                "streak": motivation_routine_streak(routine.id),
            }
            for routine in routines
        ]
    })
