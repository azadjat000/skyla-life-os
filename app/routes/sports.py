import json
from datetime import date, timedelta

from flask import Blueprint, jsonify, request, render_template

from app.extensions import db
from app.models import (
    Sport,
    SportSession,
    SportSkill,
    SportSkillLog,
    SportPersonalBest,
    SportTarget,
)


sports = Blueprint("sports", __name__)


DEFAULT_SPORTS = [
    ("Football", "⚽", "team"),
    ("Cricket", "🏏", "team"),
    ("Basketball", "🏀", "team"),
    ("Badminton", "🏸", "racket"),
    ("Tennis", "🎾", "racket"),
    ("Volleyball", "🏐", "team"),
    ("Swimming", "🏊", "individual"),
    ("Running", "🏃", "athletics"),
    ("Boxing", "🥊", "combat"),
    ("MMA", "🥋", "combat"),
    ("Cycling", "🚴", "endurance"),
    ("Weightlifting", "🏋️", "strength"),
    ("Table Tennis", "🏓", "racket"),
    ("Hockey", "🏑", "team"),
    ("Golf", "⛳", "precision"),
    ("Custom Sport", "🏆", "custom"),
]


def ensure_default_sports():
    changed = False

    for name, icon, category in DEFAULT_SPORTS:
        sport = Sport.query.filter_by(name=name).first()

        if not sport:
            db.session.add(
                Sport(
                    name=name,
                    icon=icon,
                    category=category,
                    active=True,
                )
            )
            changed = True

    if changed:
        db.session.commit()


def sport_payload(sport):
    return {
        "id": sport.id,
        "name": sport.name,
        "icon": sport.icon,
        "category": sport.category,
        "active": bool(sport.active),
    }


@sports.get("/sports")
def sports_page():
    return render_template("sports.html")


@sports.get("/api/sports")
def get_sports():
    ensure_default_sports()

    rows = Sport.query.order_by(Sport.id.asc()).all()

    return jsonify([sport_payload(x) for x in rows])


@sports.post("/api/sports")
def create_sport():
    data = request.get_json() or {}

    name = str(data.get("name", "")).strip()

    if not name:
        return jsonify({"error": "Sport name is required"}), 400

    existing = Sport.query.filter_by(name=name).first()

    if existing:
        return jsonify({
            "error": "Sport already exists",
            "id": existing.id,
        }), 409

    sport = Sport(
        name=name,
        icon=str(data.get("icon", "🏆")).strip() or "🏆",
        category=str(data.get("category", "custom")).strip() or "custom",
        active=True,
    )

    db.session.add(sport)
    db.session.commit()

    return jsonify(sport_payload(sport)), 201


@sports.post("/api/sports/<int:sport_id>/toggle")
def toggle_sport(sport_id):
    sport = Sport.query.get_or_404(sport_id)

    sport.active = not bool(sport.active)

    db.session.commit()

    return jsonify({
        "ok": True,
        "id": sport.id,
        "active": sport.active,
    })


@sports.get("/api/sports/<int:sport_id>/dashboard")
def sport_dashboard(sport_id):
    sport = Sport.query.get_or_404(sport_id)

    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    sessions = (
        SportSession.query
        .filter_by(sport_id=sport.id)
        .order_by(SportSession.session_date.desc())
        .all()
    )

    skills = SportSkill.query.filter_by(
        sport_id=sport.id
    ).order_by(SportSkill.id.asc()).all()

    targets = SportTarget.query.filter_by(
        sport_id=sport.id
    ).order_by(SportTarget.id.asc()).all()

    personal_bests = SportPersonalBest.query.filter_by(
        sport_id=sport.id
    ).order_by(SportPersonalBest.record_date.desc()).all()

    week_sessions = [
        x for x in sessions
        if x.session_date and x.session_date >= week_start
    ]

    month_sessions = [
        x for x in sessions
        if x.session_date and x.session_date >= month_start
    ]

    today_sessions = [
        x for x in sessions
        if x.session_date == today
    ]

    weekly_minutes = sum(
        int(x.duration or 0)
        for x in week_sessions
    )

    monthly_minutes = sum(
        int(x.duration or 0)
        for x in month_sessions
    )

    today_minutes = sum(
        int(x.duration or 0)
        for x in today_sessions
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

    skill_payload = []

    for skill in skills:
        current = float(skill.current or 0)
        target = float(skill.target or 100)

        progress = (
            min(100, round((current / target) * 100))
            if target > 0 else 0
        )

        skill_payload.append({
            "id": skill.id,
            "name": skill.name,
            "current": current,
            "target": target,
            "unit": skill.unit,
            "progress": progress,
        })

    target_payload = []

    for target in targets:
        target_value = float(target.target or 0)
        actual_value = float(target.actual or 0)

        progress = (
            min(100, round((actual_value / target_value) * 100))
            if target_value > 0 else 0
        )

        target_payload.append({
            "id": target.id,
            "title": target.title,
            "target": target_value,
            "actual": actual_value,
            "unit": target.unit,
            "deadline": (
                target.deadline.isoformat()
                if target.deadline else None
            ),
            "active": bool(target.active),
            "progress": progress,
        })

    return jsonify({
        "sport": sport_payload(sport),
        "stats": {
            "sessions_today": len(today_sessions),
            "today_minutes": today_minutes,
            "week_sessions": len(week_sessions),
            "week_minutes": weekly_minutes,
            "month_sessions": len(month_sessions),
            "month_minutes": monthly_minutes,
            "average_rating": average_rating,
            "active_targets": sum(
                1 for x in targets if x.active
            ),
        },
        "sessions": [
            {
                "id": x.id,
                "date": (
                    x.session_date.isoformat()
                    if x.session_date else None
                ),
                "type": x.session_type,
                "duration": x.duration,
                "intensity": x.intensity,
                "drills": x.drills,
                "notes": x.notes,
                "rating": x.rating,
                "metrics": (
                    json.loads(x.metrics)
                    if x.metrics
                    else {}
                ),
            }
            for x in sessions
        ],
        "skills": skill_payload,
        "targets": target_payload,
        "personal_bests": [
            {
                "id": x.id,
                "metric": x.metric,
                "value": x.value,
                "unit": x.unit,
                "date": (
                    x.record_date.isoformat()
                    if x.record_date else None
                ),
                "notes": x.notes,
            }
            for x in personal_bests
        ],
    })


@sports.post("/api/sports/<int:sport_id>/sessions")
def create_session(sport_id):
    Sport.query.get_or_404(sport_id)

    data = request.get_json() or {}

    try:
        duration = max(
            0,
            int(data.get("duration", 0) or 0)
        )
    except (TypeError, ValueError):
        return jsonify({
            "error": "Duration must be a number"
        }), 400

    try:
        rating = max(
            0,
            min(5, float(data.get("rating", 0) or 0))
        )
    except (TypeError, ValueError):
        return jsonify({
            "error": "Rating must be a number"
        }), 400

    session_date_raw = str(
        data.get("session_date", "")
        or ""
    ).strip()

    session_date = date.today()

    if session_date_raw:
        try:
            session_date = date.fromisoformat(
                session_date_raw
            )
        except ValueError:
            return jsonify({
                "error": "Training date must be YYYY-MM-DD"
            }), 400

    metrics = data.get("metrics", {})

    if not isinstance(metrics, dict):
        return jsonify({
            "error": "Training metrics must be an object"
        }), 400

    clean_metrics = {}

    for key, value in metrics.items():
        key = str(key).strip()

        if not key:
            continue

        if isinstance(value, (str, int, float, bool)):
            clean_metrics[key] = value

    session = SportSession(
        sport_id=sport_id,
        session_date=session_date,
        session_type=str(
            data.get("type", "Training")
        ).strip() or "Training",
        duration=duration,
        intensity=str(
            data.get("intensity", "medium")
        ).strip().lower() or "medium",
        drills=str(data.get("drills", "")).strip(),
        notes=str(data.get("notes", "")).strip(),
        rating=rating,
        metrics=json.dumps(
            clean_metrics,
            ensure_ascii=False
        ),
    )

    db.session.add(session)
    db.session.commit()

    return jsonify({
        "ok": True,
        "id": session.id,
        "session_date": session.session_date.isoformat(),
    }), 201


@sports.delete("/api/sports/sessions/<int:session_id>")
def delete_session(session_id):
    session = SportSession.query.get_or_404(session_id)

    db.session.delete(session)
    db.session.commit()

    return jsonify({"ok": True})


@sports.post("/api/sports/<int:sport_id>/skills")
def create_skill(sport_id):
    Sport.query.get_or_404(sport_id)

    data = request.get_json() or {}

    name = str(data.get("name", "")).strip()

    if not name:
        return jsonify({"error": "Skill name is required"}), 400

    skill = SportSkill(
        sport_id=sport_id,
        name=name,
        current=max(0, float(data.get("current", 0) or 0)),
        target=max(1, float(data.get("target", 100) or 100)),
        unit=str(data.get("unit", "%")).strip() or "%",
    )

    db.session.add(skill)
    db.session.commit()

    return jsonify({
        "ok": True,
        "id": skill.id,
    }), 201


@sports.put("/api/sports/skills/<int:skill_id>")
def update_skill(skill_id):
    skill = SportSkill.query.get_or_404(skill_id)

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

    if "unit" in data:
        skill.unit = (
            str(data.get("unit") or "%").strip()
            or "%"
        )

    db.session.commit()

    return jsonify({"ok": True})


@sports.post("/api/sports/skills/<int:skill_id>/log")
def log_skill(skill_id):
    skill = SportSkill.query.get_or_404(skill_id)

    data = request.get_json() or {}

    try:
        value = max(
            0,
            float(data.get("value") or 0)
        )
    except (TypeError, ValueError):
        return jsonify({
            "error": "Skill value must be a number"
        }), 400

    skill.current = value

    log = SportSkillLog(
        skill_id=skill.id,
        value=value,
        notes=str(data.get("notes", "")).strip(),
    )

    db.session.add(log)
    db.session.commit()

    return jsonify({
        "ok": True,
        "id": log.id,
    }), 201


@sports.post("/api/sports/<int:sport_id>/targets")
def create_target(sport_id):
    Sport.query.get_or_404(sport_id)

    data = request.get_json() or {}

    title = str(data.get("title", "")).strip()

    if not title:
        return jsonify({
            "error": "Target title is required"
        }), 400

    try:
        target = max(
            0.01,
            float(data.get("target", 100) or 100)
        )
        actual = max(
            0,
            float(data.get("actual", 0) or 0)
        )
    except (TypeError, ValueError):
        return jsonify({
            "error": "Target values must be numbers"
        }), 400

    item = SportTarget(
        sport_id=sport_id,
        title=title,
        target=target,
        actual=min(actual, target),
        unit=str(data.get("unit", "")).strip(),
        active=True,
    )

    db.session.add(item)
    db.session.commit()

    return jsonify({
        "ok": True,
        "id": item.id,
    }), 201


@sports.put("/api/sports/targets/<int:target_id>")
def update_target(target_id):
    target = SportTarget.query.get_or_404(target_id)

    data = request.get_json() or {}

    if "actual" in data:
        try:
            target.actual = max(
                0,
                min(
                    float(data.get("actual") or 0),
                    float(target.target or 0),
                )
            )
        except (TypeError, ValueError):
            return jsonify({
                "error": "Actual value must be a number"
            }), 400

    if "target" in data:
        try:
            target.target = max(
                0.01,
                float(data.get("target") or 100),
            )
            target.actual = min(
                float(target.actual or 0),
                target.target,
            )
        except (TypeError, ValueError):
            return jsonify({
                "error": "Target must be a number"
            }), 400

    if "active" in data:
        target.active = bool(data.get("active"))

    db.session.commit()

    return jsonify({"ok": True})


@sports.delete("/api/sports/targets/<int:target_id>")
def delete_target(target_id):
    target = SportTarget.query.get_or_404(target_id)

    db.session.delete(target)
    db.session.commit()

    return jsonify({"ok": True})


@sports.post("/api/sports/<int:sport_id>/personal-bests")
def create_personal_best(sport_id):
    Sport.query.get_or_404(sport_id)

    data = request.get_json() or {}

    metric = str(data.get("metric", "")).strip()

    if not metric:
        return jsonify({
            "error": "Metric is required"
        }), 400

    try:
        value = float(data.get("value") or 0)
    except (TypeError, ValueError):
        return jsonify({
            "error": "Value must be a number"
        }), 400

    item = SportPersonalBest(
        sport_id=sport_id,
        metric=metric,
        value=value,
        unit=str(data.get("unit", "")).strip(),
        notes=str(data.get("notes", "")).strip(),
    )

    db.session.add(item)
    db.session.commit()

    return jsonify({
        "ok": True,
        "id": item.id,
    }), 201

# ============================================================
# SPORTS PERFORMANCE ENGINE
# ============================================================

from datetime import timedelta


SPORT_SKILL_PRESETS = {
    "Football": [
        ("Speed", "%"),
        ("Dribbling", "%"),
        ("Passing", "%"),
        ("Shooting", "%"),
        ("Stamina", "%"),
        ("Strength", "%"),
    ],
    "Cricket": [
        ("Batting", "%"),
        ("Bowling", "%"),
        ("Fielding", "%"),
        ("Stamina", "%"),
        ("Reaction", "%"),
        ("Strength", "%"),
    ],
    "Basketball": [
        ("Shooting", "%"),
        ("Dribbling", "%"),
        ("Passing", "%"),
        ("Speed", "%"),
        ("Stamina", "%"),
        ("Defense", "%"),
    ],
    "Badminton": [
        ("Footwork", "%"),
        ("Smash", "%"),
        ("Serve", "%"),
        ("Defense", "%"),
        ("Speed", "%"),
        ("Stamina", "%"),
    ],
    "Tennis": [
        ("Serve", "%"),
        ("Forehand", "%"),
        ("Backhand", "%"),
        ("Footwork", "%"),
        ("Speed", "%"),
        ("Stamina", "%"),
    ],
    "Volleyball": [
        ("Serving", "%"),
        ("Spiking", "%"),
        ("Blocking", "%"),
        ("Passing", "%"),
        ("Jump", "%"),
        ("Stamina", "%"),
    ],
    "Swimming": [
        ("Technique", "%"),
        ("Speed", "%"),
        ("Endurance", "%"),
        ("Breathing", "%"),
        ("Turns", "%"),
        ("Strength", "%"),
    ],
    "Running": [
        ("Pace", "%"),
        ("Endurance", "%"),
        ("Speed", "%"),
        ("Stamina", "%"),
        ("Form", "%"),
        ("Recovery", "%"),
    ],
    "Boxing": [
        ("Footwork", "%"),
        ("Punching", "%"),
        ("Defense", "%"),
        ("Speed", "%"),
        ("Power", "%"),
        ("Stamina", "%"),
    ],
    "MMA": [
        ("Striking", "%"),
        ("Grappling", "%"),
        ("Defense", "%"),
        ("Speed", "%"),
        ("Power", "%"),
        ("Stamina", "%"),
    ],
    "Cycling": [
        ("Power", "%"),
        ("Cadence", "%"),
        ("Endurance", "%"),
        ("Climbing", "%"),
        ("Speed", "%"),
        ("Recovery", "%"),
    ],
    "Weightlifting": [
        ("Strength", "%"),
        ("Power", "%"),
        ("Technique", "%"),
        ("Mobility", "%"),
        ("Recovery", "%"),
        ("Consistency", "%"),
    ],
    "Table Tennis": [
        ("Serve", "%"),
        ("Forehand", "%"),
        ("Backhand", "%"),
        ("Footwork", "%"),
        ("Reaction", "%"),
        ("Control", "%"),
    ],
    "Hockey": [
        ("Speed", "%"),
        ("Dribbling", "%"),
        ("Passing", "%"),
        ("Shooting", "%"),
        ("Defense", "%"),
        ("Stamina", "%"),
    ],
    "Golf": [
        ("Driving", "%"),
        ("Putting", "%"),
        ("Chipping", "%"),
        ("Accuracy", "%"),
        ("Consistency", "%"),
        ("Mental Game", "%"),
    ],
    "Custom Sport": [
        ("Skill 1", "%"),
        ("Skill 2", "%"),
        ("Skill 3", "%"),
    ],
}


@sports.get("/api/sports/<int:sport_id>/streak")
def sport_streak(sport_id):

    sport = Sport.query.get_or_404(sport_id)

    sessions = (
        SportSession.query
        .filter_by(sport_id=sport.id)
        .order_by(SportSession.session_date.desc())
        .all()
    )

    dates = {
        session.session_date
        for session in sessions
        if session.session_date
    }

    today = date.today()

    streak = 0
    cursor = today

    if cursor not in dates:
        cursor = today - timedelta(days=1)

    while cursor in dates:
        streak += 1
        cursor -= timedelta(days=1)

    return jsonify({
        "sport_id": sport.id,
        "sport": sport.name,
        "streak": streak,
        "date": today.isoformat(),
    })



@sports.post("/api/sports/<int:sport_id>/initialize-skills")
def initialize_sport_skills(sport_id):
    sport = db.session.get(Sport, sport_id)

    if not sport:
        return jsonify({"error": "Sport not found"}), 404

    sport_name = sport.name.strip()

    presets = SPORT_SKILL_PRESETS.get(
        sport_name,
        []
    )

    created = []
    existing = []

    for preset in presets:

        if isinstance(preset, (tuple, list)):
            skill_name = str(preset[0]).strip()
            skill_unit = (
                str(preset[1]).strip()
                if len(preset) > 1 and preset[1]
                else "%"
            )
        else:
            skill_name = str(preset).strip()
            skill_unit = "%"

        if not skill_name:
            continue

        found = SportSkill.query.filter_by(
            sport_id=sport.id,
            name=skill_name
        ).first()

        if found:
            existing.append(skill_name)
            continue

        skill = SportSkill(
            sport_id=sport.id,
            name=skill_name,
            current=0,
            target=100,
            unit=skill_unit
        )

        db.session.add(skill)
        created.append(skill_name)

    db.session.commit()

    return jsonify({
        "success": True,
        "sport": sport.name,
        "created": created,
        "existing": existing,
        "count": len(created)
    })

@sports.get("/api/sports/<int:sport_id>/analytics")
def sport_analytics(sport_id):

    sport = Sport.query.get_or_404(sport_id)

    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    sessions = SportSession.query.filter_by(
        sport_id=sport.id
    ).all()

    week_sessions = [
        s for s in sessions
        if s.session_date and s.session_date >= week_start
    ]

    month_sessions = [
        s for s in sessions
        if s.session_date and s.session_date >= month_start
    ]

    def minutes(rows):
        return sum(int(x.duration or 0) for x in rows)

    def avg_rating(rows):
        ratings = [
            float(x.rating or 0)
            for x in rows
            if float(x.rating or 0) > 0
        ]
        return round(sum(ratings) / len(ratings), 2) if ratings else 0

    def metric_totals(rows):
        totals = {}

        for session in rows:
            try:
                session_metrics = json.loads(
                    session.metrics or "{}"
                )
            except (TypeError, ValueError):
                session_metrics = {}

            if not isinstance(session_metrics, dict):
                continue

            for key, value in session_metrics.items():

                if isinstance(value, bool):
                    continue

                if isinstance(value, (int, float)):
                    totals[key] = totals.get(key, 0) + value

        return totals

    daily = {}

    for offset in range(7):
        day = week_start + timedelta(days=offset)

        rows = [
            s for s in sessions
            if s.session_date == day
        ]

        daily[day.isoformat()] = {
            "sessions": len(rows),
            "minutes": minutes(rows),
            "metrics": metric_totals(rows),
        }

    return jsonify({
        "sport": {
            "id": sport.id,
            "name": sport.name,
            "icon": sport.icon,
        },
        "week": {
            "sessions": len(week_sessions),
            "minutes": minutes(week_sessions),
            "average_rating": avg_rating(week_sessions),
            "metrics": metric_totals(week_sessions),
        },
        "month": {
            "sessions": len(month_sessions),
            "minutes": minutes(month_sessions),
            "average_rating": avg_rating(month_sessions),
            "metrics": metric_totals(month_sessions),
        },
        "daily": daily,
    })


@sports.post("/api/sports/<int:sport_id>/skills/presets")
def create_skill_presets(sport_id):

    sport = Sport.query.get_or_404(sport_id)

    presets = SPORT_SKILL_PRESETS.get(
        sport.name,
        SPORT_SKILL_PRESETS["Custom Sport"]
    )

    created = []

    existing = {
        skill.name.lower()
        for skill in SportSkill.query.filter_by(
            sport_id=sport.id
        ).all()
    }

    for name, unit in presets:

        if name.lower() in existing:
            continue

        skill = SportSkill(
            sport_id=sport.id,
            name=name,
            current=0,
            target=100,
            unit=unit,
        )

        db.session.add(skill)
        created.append(name)

    db.session.commit()

    return jsonify({
        "sport": sport.name,
        "created": created,
        "count": len(created),
    }), 201


@sports.get("/api/sports/<int:sport_id>/skill-history/<int:skill_id>")
def skill_history(sport_id, skill_id):

    sport = Sport.query.get_or_404(sport_id)

    skill = SportSkill.query.filter_by(
        id=skill_id,
        sport_id=sport.id
    ).first_or_404()

    logs = (
        SportSkillLog.query
        .filter_by(skill_id=skill.id)
        .order_by(SportSkillLog.log_date.asc())
        .all()
    )

    return jsonify({
        "sport": sport.name,
        "skill": {
            "id": skill.id,
            "name": skill.name,
            "current": skill.current,
            "target": skill.target,
            "unit": skill.unit,
        },
        "history": [
            {
                "id": row.id,
                "date": row.log_date.isoformat(),
                "value": row.value,
                "notes": row.notes,
            }
            for row in logs
        ],
    })


@sports.post("/api/sports/<int:sport_id>/legacy-football-sync")
def legacy_football_sync(sport_id):
    """
    Safely copy legacy Football data into Sports Hub.
    Legacy Football records are never modified or deleted.
    """

    sport = db.session.get(Sport, sport_id)

    if not sport:
        return jsonify({"error": "Sport not found"}), 404

    if sport.name.lower() != "football":
        return jsonify({
            "error": "This endpoint is only for Football"
        }), 400

    from ..models import (
        FootballSession,
        FootballSkill,
        FootballSkillLog,
    )

    imported_sessions = 0
    imported_skills = 0
    imported_logs = 0

    # ---------------------------------------------------------
    # Legacy Football sessions -> Sports Hub sessions
    # ---------------------------------------------------------

    existing_sessions = SportSession.query.filter_by(
        sport_id=sport.id
    ).all()

    existing_session_keys = {
        (
            x.session_date,
            x.session_type or "Training",
            x.duration or 0,
            x.drills or "",
            x.notes or "",
        )
        for x in existing_sessions
    }

    legacy_sessions = FootballSession.query.order_by(
        FootballSession.id.asc()
    ).all()

    for old in legacy_sessions:

        key = (
            old.session_date,
            old.session_type or "Training",
            old.duration or 0,
            old.drills or "",
            old.notes or "",
        )

        if key in existing_session_keys:
            continue

        db.session.add(
            SportSession(
                sport_id=sport.id,
                session_date=old.session_date,
                session_type=old.session_type or "Training",
                duration=old.duration or 0,
                intensity="medium",
                drills=old.drills or "",
                notes=old.notes or "",
                rating=old.rating or 0,
            )
        )

        existing_session_keys.add(key)
        imported_sessions += 1

    # ---------------------------------------------------------
    # Legacy Football skills -> Sports Hub skills
    # FootballSkill.skill is the actual legacy field.
    # ---------------------------------------------------------

    skill_map = {}

    old_skills = FootballSkill.query.order_by(
        FootballSkill.id.asc()
    ).all()

    for old_skill in old_skills:

        skill_name = (
            getattr(old_skill, "skill", None)
            or f"Football Skill {old_skill.id}"
        ).strip()

        existing = SportSkill.query.filter_by(
            sport_id=sport.id,
            name=skill_name
        ).first()

        if existing:
            skill_map[old_skill.id] = existing
            continue

        new_skill = SportSkill(
            sport_id=sport.id,
            name=skill_name,
            current=getattr(old_skill, "current", 0) or 0,
            target=getattr(old_skill, "target", 100) or 100,
            unit="%",
        )

        db.session.add(new_skill)
        db.session.flush()

        skill_map[old_skill.id] = new_skill
        imported_skills += 1

    # ---------------------------------------------------------
    # Legacy skill logs -> Sports Hub skill logs
    # ---------------------------------------------------------

    old_logs = FootballSkillLog.query.order_by(
        FootballSkillLog.id.asc()
    ).all()

    for old_log in old_logs:

        new_skill = skill_map.get(old_log.skill_id)

        if not new_skill:
            continue

        duplicate = SportSkillLog.query.filter_by(
            skill_id=new_skill.id,
            value=old_log.value or 0,
            log_date=old_log.log_date,
            notes=old_log.notes or "",
        ).first()

        if duplicate:
            continue

        db.session.add(
            SportSkillLog(
                skill_id=new_skill.id,
                value=old_log.value or 0,
                log_date=old_log.log_date,
                notes=old_log.notes or "",
            )
        )

        imported_logs += 1

    db.session.commit()

    return jsonify({
        "success": True,
        "sport": sport.name,
        "legacy_data_preserved": True,
        "imported": {
            "sessions": imported_sessions,
            "skills": imported_skills,
            "skill_logs": imported_logs,
        },
    })

