from flask import Blueprint, jsonify, request, render_template
from app.extensions import db
from app.models import FootballSession

football = Blueprint("football", __name__)


@football.get("/football")
def football_page():
    return render_template("football.html")


@football.get("/api/football")
def get_football():
    rows = FootballSession.query.order_by(
        FootballSession.id.desc()
    ).all()

    return jsonify([
        {
            "id": x.id,
            "date": x.session_date.isoformat()
                if x.session_date else None,
            "type": x.session_type,
            "duration": x.duration,
            "drills": x.drills,
            "notes": x.notes,
            "rating": x.rating
        }
        for x in rows
    ])


@football.post("/api/football")
def add_football():
    data = request.get_json() or {}

    session_type = str(
        data.get("type", "")
    ).strip()

    if not session_type:
        return jsonify({
            "error": "Training type is required"
        }), 400

    item = FootballSession(
        session_type=session_type,
        duration=int(data.get("duration", 0) or 0),
        drills=str(data.get("drills", "")).strip(),
        notes=str(data.get("notes", "")).strip(),
        rating=float(data.get("rating", 0) or 0)
    )

    db.session.add(item)
    db.session.commit()

    return jsonify({
        "ok": True,
        "id": item.id
    }), 201


@football.delete("/api/football/<int:session_id>")
def delete_football(session_id):
    item = FootballSession.query.get_or_404(session_id)

    db.session.delete(item)
    db.session.commit()

    return jsonify({
        "ok": True
    })
