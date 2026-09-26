from flask import Blueprint, jsonify, request, render_template
from app.extensions import db
from app.models import Motivation

motivation = Blueprint("motivation", __name__)

@motivation.get("/motivation")
def motivation_page():
    return render_template("motivation.html")

@motivation.get("/api/motivation")
def get_motivation():
    rows = Motivation.query.order_by(Motivation.id.desc()).all()
    return jsonify([
        {
            "id": x.id,
            "title": x.title,
            "message": x.message,
            "active": x.active
        }
        for x in rows
    ])

@motivation.post("/api/motivation")
def add_motivation():
    data = request.get_json() or {}

    title = str(data.get("title", "")).strip()
    message = str(data.get("message", "")).strip()

    if not title or not message:
        return jsonify({"error": "Title and message are required"}), 400

    item = Motivation(
        title=title,
        message=message,
        active=bool(data.get("active", True))
    )

    db.session.add(item)
    db.session.commit()

    return jsonify({
        "ok": True,
        "id": item.id
    }), 201

@motivation.post("/api/motivation/<int:item_id>/toggle")
def toggle_motivation(item_id):
    item = Motivation.query.get_or_404(item_id)
    item.active = not item.active
    db.session.commit()

    return jsonify({
        "ok": True,
        "active": item.active
    })

@motivation.delete("/api/motivation/<int:item_id>")
def delete_motivation(item_id):
    item = Motivation.query.get_or_404(item_id)

    db.session.delete(item)
    db.session.commit()

    return jsonify({"ok": True})
