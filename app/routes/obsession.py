from flask import Blueprint, jsonify, request, render_template
from app.extensions import db
from app.models import Goal, FocusSession

obsession = Blueprint("obsession", __name__)


@obsession.get("/obsession")
def obsession_page():
    return render_template("obsession.html")


@obsession.get("/api/obsession")
def get_obsession():

    goals = Goal.query.filter_by(category="obsession").order_by(Goal.id.desc()).all()
    sessions = FocusSession.query.order_by(FocusSession.id.desc()).all()

    return jsonify({
        "goals": [
            {
                "id": x.id,
                "title": x.title,
                "description": x.description,
                "progress": x.progress,
                "target": x.target,
                "deadline": x.deadline,
                "active": x.active
            }
            for x in goals
        ],
        "sessions": [
            {
                "id": x.id,
                "goal_id": x.goal_id,
                "date": x.session_date.isoformat() if x.session_date else None,
                "duration": x.duration,
                "notes": x.notes
            }
            for x in sessions
        ]
    })


@obsession.post("/api/obsession/goals")
def add_goal():

    data = request.get_json() or {}

    title = str(data.get("title", "")).strip()

    if not title:
        return jsonify({"error": "Target title is required"}), 400

    target = float(data.get("target", 100) or 100)

    item = Goal(
        title=title,
        category="obsession",
        description=str(data.get("description", "")).strip(),
        progress=0,
        target=target,
        deadline=str(data.get("deadline", "")).strip(),
        active=True
    )

    db.session.add(item)
    db.session.commit()

    return jsonify({
        "ok": True,
        "id": item.id
    }), 201


@obsession.put("/api/obsession/goals/<int:goal_id>")
def update_goal(goal_id):

    item = Goal.query.get_or_404(goal_id)

    if item.category != "obsession":
        return jsonify({"error": "Not an obsession target"}), 404

    data = request.get_json() or {}

    if "progress" in data:
        item.progress = max(0, min(
            float(data["progress"]),
            float(item.target or 100)
        ))

    if "title" in data:
        item.title = str(data["title"]).strip()

    if "description" in data:
        item.description = str(data["description"]).strip()

    if "deadline" in data:
        item.deadline = str(data["deadline"]).strip()

    db.session.commit()

    return jsonify({"ok": True})


@obsession.post("/api/obsession/goals/<int:goal_id>/toggle")
def toggle_goal(goal_id):

    item = Goal.query.get_or_404(goal_id)

    if item.category != "obsession":
        return jsonify({"error": "Not an obsession target"}), 404

    item.active = not item.active
    db.session.commit()

    return jsonify({
        "ok": True,
        "active": item.active
    })


@obsession.delete("/api/obsession/goals/<int:goal_id>")
def delete_goal(goal_id):

    item = Goal.query.get_or_404(goal_id)

    if item.category != "obsession":
        return jsonify({"error": "Not an obsession target"}), 404

    db.session.delete(item)
    db.session.commit()

    return jsonify({"ok": True})


@obsession.post("/api/obsession/focus")
def add_focus():

    data = request.get_json() or {}

    duration = int(data.get("duration", 0) or 0)

    if duration <= 0:
        return jsonify({"error": "Focus duration must be greater than zero"}), 400

    item = FocusSession(
        goal_id=data.get("goal_id") or None,
        duration=duration,
        notes=str(data.get("notes", "")).strip()
    )

    db.session.add(item)
    db.session.commit()

    return jsonify({
        "ok": True,
        "id": item.id
    }), 201


@obsession.delete("/api/obsession/focus/<int:session_id>")
def delete_focus(session_id):

    item = FocusSession.query.get_or_404(session_id)

    db.session.delete(item)
    db.session.commit()

    return jsonify({"ok": True})
