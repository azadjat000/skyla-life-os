from flask import Blueprint, render_template

main = Blueprint("main", __name__)

@main.get("/")
def home():
    return render_template("index.html")


@main.get("/api/dashboard")
def dashboard_data():
    from app.models import Motivation, Routine, Goal, FocusSession

    motivation_count = Motivation.query.filter_by(active=True).count()

    discipline_count = Routine.query.filter_by(
        category="discipline",
        active=True
    ).count()

    obsession_goals = Goal.query.filter_by(
        category="obsession",
        active=True
    ).all()

    focus_sessions = FocusSession.query.all()

    focus_minutes = sum(
        int(x.duration or 0)
        for x in focus_sessions
    )

    obsession_progress = 0

    if obsession_goals:
        values = []

        for goal in obsession_goals:
            target = float(goal.target or 100)
            progress = float(goal.progress or 0)

            values.append(
                min(100, (progress / target) * 100)
            )

        obsession_progress = round(
            sum(values) / len(values)
        )

    return {
        "motivation": {
            "active": motivation_count
        },
        "discipline": {
            "active": discipline_count
        },
        "obsession": {
            "active": len(obsession_goals),
            "progress": obsession_progress,
            "focus_minutes": focus_minutes
        }
    }
