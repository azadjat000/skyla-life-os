from flask import Blueprint, jsonify, request, render_template
from app.extensions import db
from app.models import Routine

discipline = Blueprint("discipline", __name__)


@discipline.get("/discipline")
def discipline_page():
    return render_template("discipline.html")


@discipline.get("/api/discipline")
def get_discipline():
    rows = Routine.query.filter_by(category="discipline").order_by(Routine.id.desc()).all()

    return jsonify([
        {
            "id": x.id,
            "title": x.title,
            "time": x.time,
            "description": x.description,
            "repeat": x.repeat,
            "active": x.active
        }
        for x in rows
    ])


@discipline.post("/api/discipline")
def add_discipline():
    data = request.get_json() or {}

    title = str(data.get("title", "")).strip()

    if not title:
        return jsonify({"error": "Routine title is required"}), 400

    item = Routine(
        title=title,
        category="discipline",
        time=str(data.get("time", "")).strip(),
        description=str(data.get("description", "")).strip(),
        repeat=str(data.get("repeat", "daily")).strip(),
        active=bool(data.get("active", True))
    )

    db.session.add(item)
    db.session.commit()

    return jsonify({
        "ok": True,
        "id": item.id
    }), 201


@discipline.post("/api/discipline/<int:item_id>/toggle")
def toggle_discipline(item_id):
    item = Routine.query.get_or_404(item_id)

    if item.category != "discipline":
        return jsonify({"error": "Not a discipline routine"}), 404

    item.active = not item.active
    db.session.commit()

    return jsonify({
        "ok": True,
        "active": item.active
    })


@discipline.delete("/api/discipline/<int:item_id>")
def delete_discipline(item_id):
    item = Routine.query.get_or_404(item_id)

    if item.category != "discipline":
        return jsonify({"error": "Not a discipline routine"}), 404

    db.session.delete(item)
    db.session.commit()

    return jsonify({"ok": True})
