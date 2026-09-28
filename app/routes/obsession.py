from datetime import date, datetime, timedelta

from flask import Blueprint, jsonify, request, render_template

from app.extensions import db
from app.models import (
    Goal,
    FocusSession,
    Routine,
    RoutineLog,
)


obsession = Blueprint("obsession", __name__)


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def routine_streak(routine_id, before_date=None):
    current = before_date or date.today()
    streak = 0

    while True:
        log = (
            RoutineLog.query
            .filter_by(
                routine_id=routine_id,
                log_date=current,
                completed=True,
            )
            .first()
        )

        if not log:
            break

        streak += 1
        current -= timedelta(days=1)

    return streak


def goal_payload(goal):
    progress = float(goal.progress or 0)
    target = float(goal.target or 100)

    percent = 0
    if target > 0:
        percent = min(100, max(0, round(progress / target * 100)))

    milestones = {
        "25": percent >= 25,
        "50": percent >= 50,
        "75": percent >= 75,
        "100": percent >= 100,
    }

    return {
        "id": goal.id,
        "title": goal.title,
        "description": goal.description or "",
        "progress": progress,
        "target": target,
        "progress_percent": percent,
        "deadline": (
            goal.deadline.isoformat()
            if goal.deadline
            else None
        ),
        "active": bool(goal.active),
        "completed": percent >= 100,
        "milestones": milestones,
    }


def routine_payload(routine):
    today = date.today()

    completed_today = (
        RoutineLog.query
        .filter_by(
            routine_id=routine.id,
            log_date=today,
            completed=True,
        )
        .first()
        is not None
    )

    return {
        "id": routine.id,
        "title": routine.title,
        "time": routine.time or "",
        "description": routine.description or "",
        "repeat": routine.repeat or "daily",
        "active": bool(routine.active),
        "completed_today": completed_today,
        "streak": routine_streak(routine.id),
    }


# ---------------------------------------------------------
# Page
# ---------------------------------------------------------

@obsession.get("/obsession")
def obsession_page():
    return render_template("obsession.html")


# ---------------------------------------------------------
# Main Obsession Dashboard API
# ---------------------------------------------------------

@obsession.get("/api/obsession")
def get_obsession():

    today = date.today()

    goals = (
        Goal.query
        .filter_by(category="obsession")
        .order_by(Goal.id.desc())
        .all()
    )

    routines = (
        Routine.query
        .filter_by(category="obsession")
        .order_by(Routine.time.asc(), Routine.id.asc())
        .all()
    )

    sessions = (
        FocusSession.query
        .order_by(FocusSession.id.desc())
        .all()
    )

    today_sessions = [
        x for x in sessions
        if x.session_date == today
    ]

    today_focus = sum(
        int(x.duration or 0)
        for x in today_sessions
    )

    active_goals = [
        x for x in goals
        if x.active
    ]

    active_routines = [
        x for x in routines
        if x.active
    ]

    completed_routines = sum(
        1
        for x in active_routines
        if routine_payload(x)["completed_today"]
    )

    routine_progress = (
        round(
            completed_routines /
            len(active_routines) * 100
        )
        if active_routines
        else 0
    )

    goal_progress = [
        goal_payload(x)["progress_percent"]
        for x in active_goals
    ]

    average_progress = (
        round(sum(goal_progress) / len(goal_progress))
        if goal_progress
        else 0
    )

    return jsonify({
        "date": today.isoformat(),

        "stats": {
            "active_targets": len(active_goals),
            "total_targets": len(goals),
            "completed_targets": sum(
                1
                for x in goals
                if goal_payload(x)["completed"]
            ),
            "average_progress": average_progress,

            "active_routines": len(active_routines),
            "completed_routines": completed_routines,
            "routine_progress": routine_progress,

            "focus_minutes_today": today_focus,
            "focus_sessions_today": len(today_sessions),
            "focus_minutes_total": sum(
                int(x.duration or 0)
                for x in sessions
            ),
        },

        "goals": [
            goal_payload(x)
            for x in goals
        ],

        "routines": [
            routine_payload(x)
            for x in routines
        ],

        "sessions": [
            {
                "id": x.id,
                "goal_id": x.goal_id,
                "date": (
                    x.session_date.isoformat()
                    if x.session_date
                    else None
                ),
                "duration": int(x.duration or 0),
                "notes": x.notes or "",
            }
            for x in sessions[:50]
        ],
    })


# ---------------------------------------------------------
# Goals
# ---------------------------------------------------------

@obsession.post("/api/obsession/goals")
def add_goal():

    data = request.get_json() or {}

    title = str(
        data.get("title", "")
    ).strip()

    if not title:
        return jsonify({
            "error": "Target title is required"
        }), 400

    try:
        target = float(
            data.get("target", 100) or 100
        )
    except (TypeError, ValueError):
        return jsonify({
            "error": "Target must be a number"
        }), 400

    if target <= 0:
        return jsonify({
            "error": "Target must be greater than zero"
        }), 400

    deadline_raw = str(
        data.get("deadline", "") or ""
    ).strip()

    deadline = None

    if deadline_raw:
        try:
            deadline = date.fromisoformat(
                deadline_raw
            )
        except ValueError:
            return jsonify({
                "error": "Deadline must be YYYY-MM-DD"
            }), 400

    item = Goal(
        title=title,
        category="obsession",
        description=str(
            data.get("description", "")
        ).strip(),
        progress=0,
        target=target,
        deadline=deadline,
        active=True,
    )

    db.session.add(item)
    db.session.commit()

    return jsonify({
        "ok": True,
        "id": item.id,
        "goal": goal_payload(item),
    }), 201


@obsession.put("/api/obsession/goals/<int:goal_id>")
def update_goal(goal_id):

    item = Goal.query.get_or_404(goal_id)

    if item.category != "obsession":
        return jsonify({
            "error": "Not an obsession target"
        }), 404

    data = request.get_json() or {}

    if "title" in data:
        title = str(data["title"]).strip()

        if not title:
            return jsonify({
                "error": "Target title is required"
            }), 400

        item.title = title

    if "description" in data:
        item.description = str(
            data["description"]
        ).strip()

    if "target" in data:
        try:
            target = float(data["target"])
        except (TypeError, ValueError):
            return jsonify({
                "error": "Target must be a number"
            }), 400

        if target <= 0:
            return jsonify({
                "error": "Target must be greater than zero"
            }), 400

        item.target = target

    if "progress" in data:
        try:
            progress = float(data["progress"])
        except (TypeError, ValueError):
            return jsonify({
                "error": "Progress must be a number"
            }), 400

        item.progress = max(
            0,
            min(
                progress,
                float(item.target or 100)
            )
        )

    if "deadline" in data:

        deadline_raw = str(
            data.get("deadline", "") or ""
        ).strip()

        if deadline_raw:
            try:
                item.deadline = date.fromisoformat(
                    deadline_raw
                )
            except ValueError:
                return jsonify({
                    "error": "Deadline must be YYYY-MM-DD"
                }), 400
        else:
            item.deadline = None

    db.session.commit()

    return jsonify({
        "ok": True,
        "goal": goal_payload(item),
    })


@obsession.post("/api/obsession/goals/<int:goal_id>/toggle")
def toggle_goal(goal_id):

    item = Goal.query.get_or_404(goal_id)

    if item.category != "obsession":
        return jsonify({
            "error": "Not an obsession target"
        }), 404

    item.active = not item.active

    db.session.commit()

    return jsonify({
        "ok": True,
        "active": item.active,
    })


@obsession.delete("/api/obsession/goals/<int:goal_id>")
def delete_goal(goal_id):

    item = Goal.query.get_or_404(goal_id)

    if item.category != "obsession":
        return jsonify({
            "error": "Not an obsession target"
        }), 404

    db.session.delete(item)
    db.session.commit()

    return jsonify({
        "ok": True
    })


# ---------------------------------------------------------
# Obsession Routines
# ---------------------------------------------------------

@obsession.post("/api/obsession/routines")
def add_routine():

    data = request.get_json() or {}

    title = str(
        data.get("title", "")
    ).strip()

    if not title:
        return jsonify({
            "error": "Routine title is required"
        }), 400

    item = Routine(
        title=title,
        category="obsession",
        time=str(
            data.get("time", "")
        ).strip(),
        description=str(
            data.get("description", "")
        ).strip(),
        repeat=str(
            data.get("repeat", "daily")
        ).strip() or "daily",
        active=bool(
            data.get("active", True)
        ),
    )

    db.session.add(item)
    db.session.commit()

    return jsonify({
        "ok": True,
        "id": item.id,
        "routine": routine_payload(item),
    }), 201


@obsession.post(
    "/api/obsession/routines/<int:routine_id>/toggle"
)
def toggle_routine(routine_id):

    item = Routine.query.get_or_404(
        routine_id
    )

    if item.category != "obsession":
        return jsonify({
            "error": "Not an obsession routine"
        }), 404

    item.active = not item.active

    db.session.commit()

    return jsonify({
        "ok": True,
        "active": item.active,
    })


@obsession.post(
    "/api/obsession/routines/<int:routine_id>/complete"
)
def complete_routine(routine_id):

    item = Routine.query.get_or_404(
        routine_id
    )

    if item.category != "obsession":
        return jsonify({
            "error": "Not an obsession routine"
        }), 404

    today = date.today()

    log = (
        RoutineLog.query
        .filter_by(
            routine_id=item.id,
            log_date=today,
        )
        .first()
    )

    if not log:
        log = RoutineLog(
            routine_id=item.id,
            log_date=today,
        )
        db.session.add(log)

    log.completed = True
    log.completed_at = datetime.utcnow()

    db.session.commit()

    return jsonify({
        "ok": True,
        "completed": True,
        "streak": routine_streak(item.id),
    })


@obsession.post(
    "/api/obsession/routines/<int:routine_id>/undo"
)
def undo_routine(routine_id):

    item = Routine.query.get_or_404(
        routine_id
    )

    if item.category != "obsession":
        return jsonify({
            "error": "Not an obsession routine"
        }), 404

    today = date.today()

    log = (
        RoutineLog.query
        .filter_by(
            routine_id=item.id,
            log_date=today,
        )
        .first()
    )

    if log:
        log.completed = False
        log.completed_at = None

    db.session.commit()

    return jsonify({
        "ok": True,
        "completed": False,
    })


@obsession.delete(
    "/api/obsession/routines/<int:routine_id>"
)
def delete_routine(routine_id):

    item = Routine.query.get_or_404(
        routine_id
    )

    if item.category != "obsession":
        return jsonify({
            "error": "Not an obsession routine"
        }), 404

    RoutineLog.query.filter_by(
        routine_id=item.id
    ).delete()

    db.session.delete(item)
    db.session.commit()

    return jsonify({
        "ok": True
    })


# ---------------------------------------------------------
# Focus Sessions
# ---------------------------------------------------------

@obsession.post("/api/obsession/focus")
def add_focus():

    data = request.get_json() or {}

    try:
        duration = int(
            data.get("duration", 0) or 0
        )
    except (TypeError, ValueError):
        return jsonify({
            "error": "Focus duration must be a number"
        }), 400

    if duration <= 0:
        return jsonify({
            "error": "Focus duration must be greater than zero"
        }), 400

    goal_id = data.get("goal_id") or None

    if goal_id:
        goal = Goal.query.get(goal_id)

        if not goal or goal.category != "obsession":
            return jsonify({
                "error": "Invalid obsession target"
            }), 400

    item = FocusSession(
        goal_id=goal_id,
        duration=duration,
        notes=str(
            data.get("notes", "")
        ).strip(),
        session_date=date.today(),
    )

    db.session.add(item)
    db.session.commit()

    return jsonify({
        "ok": True,
        "id": item.id,
    }), 201


@obsession.delete(
    "/api/obsession/focus/<int:session_id>"
)
def delete_focus(session_id):

    item = FocusSession.query.get_or_404(
        session_id
    )

    db.session.delete(item)
    db.session.commit()

    return jsonify({
        "ok": True
    })


# ---------------------------------------------------------
# Streak / Focus helpers
# ---------------------------------------------------------

@obsession.get("/api/obsession/streaks")
def obsession_streaks():

    routines = (
        Routine.query
        .filter_by(
            category="obsession",
            active=True,
        )
        .order_by(Routine.id.asc())
        .all()
    )

    return jsonify({
        "date": date.today().isoformat(),
        "routines": [
            {
                "id": x.id,
                "title": x.title,
                "streak": routine_streak(x.id),
            }
            for x in routines
        ],
    })


@obsession.get("/api/obsession/focus")
def obsession_focus():

    today = date.today()

    sessions = (
        FocusSession.query
        .filter_by(session_date=today)
        .order_by(FocusSession.id.desc())
        .all()
    )

    return jsonify({
        "date": today.isoformat(),
        "sessions": [
            {
                "id": x.id,
                "goal_id": x.goal_id,
                "duration": int(x.duration or 0),
                "notes": x.notes or "",
            }
            for x in sessions
        ],
        "total_minutes": sum(
            int(x.duration or 0)
            for x in sessions
        ),
    })
