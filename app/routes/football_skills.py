from flask import Blueprint, jsonify, request
from datetime import date

from app.extensions import db
from app.models import (
    FootballSkill,
    FootballSkillLog,
    FootballSession
)


football_skills = Blueprint("football_skills", __name__)

DEFAULT_SKILLS = [
    "Speed",
    "Dribbling",
    "Passing",
    "Shooting",
    "Stamina",
    "Strength",
]


def ensure_default_skills():
    changed = False

    for name in DEFAULT_SKILLS:
        skill = FootballSkill.query.filter_by(skill=name).first()

        if not skill:
            skill = FootballSkill(
                skill=name,
                current=0,
                target=100
            )
            db.session.add(skill)
            changed = True

    if changed:
        db.session.commit()


@football_skills.get("/api/football/skills")
def get_skills():
    ensure_default_skills()

    skills = FootballSkill.query.order_by(FootballSkill.id.asc()).all()

    result = []

    for skill in skills:
        target = float(skill.target or 100)
        current = float(skill.current or 0)

        progress = 0
        if target > 0:
            progress = min(100, round((current / target) * 100))

        result.append({
            "id": skill.id,
            "skill": skill.skill,
            "current": current,
            "target": target,
            "progress": progress
        })

    return jsonify(result)


@football_skills.put("/api/football/skills/<int:skill_id>")
def update_skill(skill_id):
    skill = FootballSkill.query.get_or_404(skill_id)
    data = request.get_json() or {}

    if "current" in data:
        skill.current = max(
            0,
            float(data.get("current") or 0)
        )

    if "target" in data:
        skill.target = max(
            1,
            float(data.get("target") or 100)
        )

    db.session.commit()

    return jsonify({
        "ok": True,
        "id": skill.id,
        "current": skill.current,
        "target": skill.target
    })


@football_skills.post("/api/football/skills/<int:skill_id>/log")
def log_skill(skill_id):
    skill = FootballSkill.query.get_or_404(skill_id)
    data = request.get_json() or {}

    value = float(data.get("value") or 0)

    if value < 0:
        return jsonify({
            "error": "Skill value cannot be negative"
        }), 400

    skill.current = value

    log = FootballSkillLog(
        skill_id=skill.id,
        value=value,
        log_date=date.today(),
        notes=str(data.get("notes", "")).strip()
    )

    db.session.add(log)
    db.session.commit()

    return jsonify({
        "ok": True,
        "log_id": log.id,
        "skill_id": skill.id,
        "value": value
    }), 201


@football_skills.get("/api/football/skills/<int:skill_id>/history")
def skill_history(skill_id):
    skill = FootballSkill.query.get_or_404(skill_id)

    logs = (
        FootballSkillLog.query
        .filter_by(skill_id=skill.id)
        .order_by(
            FootballSkillLog.log_date.asc(),
            FootballSkillLog.id.asc()
        )
        .all()
    )

    return jsonify([
        {
            "id": log.id,
            "date": log.log_date.isoformat() if log.log_date else None,
            "value": log.value,
            "notes": log.notes
        }
        for log in logs
    ])


@football_skills.delete("/api/football/skills/log/<int:log_id>")
def delete_skill_log(log_id):
    log = FootballSkillLog.query.get_or_404(log_id)

    db.session.delete(log)
    db.session.commit()

    return jsonify({"ok": True})


@football_skills.get("/api/football/analytics")
def football_analytics():
    from datetime import date, timedelta

    ensure_default_skills()

    skills = FootballSkill.query.order_by(FootballSkill.id.asc()).all()

    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    sessions = FootballSession.query.order_by(
        FootballSession.session_date.asc()
    ).all()

    weekly_sessions = [
        x for x in sessions
        if x.session_date and x.session_date >= week_start
    ]

    monthly_sessions = [
        x for x in sessions
        if x.session_date and x.session_date >= month_start
    ]

    weekly_minutes = sum(
        int(x.duration or 0)
        for x in weekly_sessions
    )

    monthly_minutes = sum(
        int(x.duration or 0)
        for x in monthly_sessions
    )

    ratings = [
        float(x.rating)
        for x in sessions
        if x.rating is not None and float(x.rating) > 0
    ]

    average_rating = (
        round(sum(ratings) / len(ratings), 2)
        if ratings else 0
    )

    skill_data = []

    for skill in skills:
        current = float(skill.current or 0)
        target = float(skill.target or 100)

        progress = (
            min(100, round((current / target) * 100))
            if target > 0 else 0
        )

        logs = (
            FootballSkillLog.query
            .filter_by(skill_id=skill.id)
            .order_by(FootballSkillLog.value.desc())
            .all()
        )

        personal_best = max(
            [float(x.value) for x in logs],
            default=current
        )

        skill_data.append({
            "skill": skill.skill,
            "current": current,
            "target": target,
            "progress": progress,
            "personal_best": personal_best
        })

    overall = (
        round(
            sum(x["progress"] for x in skill_data)
            / len(skill_data)
        )
        if skill_data else 0
    )

    training_dates = sorted({
        x.session_date
        for x in sessions
        if x.session_date
    })

    streak = 0
    check_date = today

    training_date_set = set(training_dates)

    while check_date in training_date_set:
        streak += 1
        check_date -= timedelta(days=1)

    return jsonify({
        "overall_skill": overall,
        "weekly": {
            "sessions": len(weekly_sessions),
            "minutes": weekly_minutes
        },
        "monthly": {
            "sessions": len(monthly_sessions),
            "minutes": monthly_minutes
        },
        "average_rating": average_rating,
        "training_streak": streak,
        "skills": skill_data
    })

@football_skills.get("/api/football/graph-data")
def football_graph_data():
    from datetime import date, timedelta

    ensure_default_skills()

    today = date.today()
    start_date = today - timedelta(days=29)

    sessions = (
        FootballSession.query
        .order_by(FootballSession.session_date.asc())
        .all()
    )

    skills = FootballSkill.query.order_by(FootballSkill.id.asc()).all()

    # Last 30 days
    daily = []

    for i in range(30):
        current_date = start_date + timedelta(days=i)

        day_sessions = [
            x for x in sessions
            if x.session_date == current_date
        ]

        daily.append({
            "date": current_date.isoformat(),
            "sessions": len(day_sessions),
            "minutes": sum(int(x.duration or 0) for x in day_sessions),
            "rating": round(
                sum(float(x.rating or 0) for x in day_sessions) /
                len(day_sessions), 2
            ) if day_sessions else 0
        })

    # Skill history
    skill_history = []

    for skill in skills:
        logs = (
            FootballSkillLog.query
            .filter(
                FootballSkillLog.skill_id == skill.id,
                FootballSkillLog.log_date >= start_date
            )
            .order_by(FootballSkillLog.log_date.asc())
            .all()
        )

        skill_history.append({
            "skill": skill.skill,
            "target": float(skill.target or 0),
            "current": float(skill.current or 0),
            "history": [
                {
                    "date": x.log_date.isoformat(),
                    "value": float(x.value)
                }
                for x in logs
            ]
        })

    return jsonify({
        "period": {
            "start": start_date.isoformat(),
            "end": today.isoformat()
        },
        "daily": daily,
        "skills": skill_history
    })
