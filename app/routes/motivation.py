from flask import Blueprint, jsonify, request, render_template
from app.extensions import db
from app.models import Motivation

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
