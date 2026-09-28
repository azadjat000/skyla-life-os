from flask import Blueprint, render_template

main = Blueprint("main", __name__)

@main.get("/")
def home():
    return render_template("index.html")


@main.get("/api/dashboard")
def dashboard_data():
    from datetime import date
    from app.models import (
        Motivation,
        Routine,
        Habit,
        Goal,
        FootballSession,
        FitnessWorkout,
        FocusSession,
    )

    today = date.today()

    # Motivation
    motivation_count = Motivation.query.filter_by(
        active=True
    ).count()

    # Discipline routines
    discipline_count = Routine.query.filter_by(
        category="discipline",
        active=True
    ).count()

    # Today's habits
    active_habits = Habit.query.filter_by(
        active=True
    ).all()

    habits_completed = sum(
        1 for habit in active_habits
        if habit.completed_today
    )

    habit_completion = 0

    if active_habits:
        habit_completion = round(
            (habits_completed / len(active_habits)) * 100
        )

    # Active obsession goals
    obsession_goals = Goal.query.filter_by(
        category="obsession",
        active=True
    ).all()

    obsession_progress = 0

    if obsession_goals:
        values = []

        for goal in obsession_goals:
            target = float(goal.target or 100)
            progress = float(goal.progress or 0)

            if target > 0:
                values.append(
                    min(100, (progress / target) * 100)
                )

        if values:
            obsession_progress = round(
                sum(values) / len(values)
            )

    # Focus sessions
    focus_sessions = FocusSession.query.all()

    focus_minutes = sum(
        int(x.duration or 0)
        for x in focus_sessions
    )

    today_focus_minutes = sum(
        int(x.duration or 0)
        for x in focus_sessions
        if x.session_date == today
    )

    # Football today
    football_today = FootballSession.query.filter_by(
        session_date=today
    ).all()

    football_minutes = sum(
        int(x.duration or 0)
        for x in football_today
    )

    # Fitness today
    fitness_today = FitnessWorkout.query.filter_by(
        workout_date=today
    ).all()

    fitness_minutes = sum(
        int(x.duration or 0)
        for x in fitness_today
    )

    # Today's routines
    today_routines = Routine.query.filter_by(
        active=True
    ).count()

    return {
        "motivation": {
            "active": motivation_count
        },

        "discipline": {
            "active": discipline_count,
            "today_routines": today_routines
        },

        "habits": {
            "active": len(active_habits),
            "completed_today": habits_completed,
            "completion": habit_completion
        },

        "obsession": {
            "active": len(obsession_goals),
            "progress": obsession_progress,
            "focus_minutes": focus_minutes,
            "today_focus_minutes": today_focus_minutes
        },

        "football": {
            "sessions_today": len(football_today),
            "minutes_today": football_minutes
        },

        "fitness": {
            "workouts_today": len(fitness_today),
            "minutes_today": fitness_minutes
        }
    }
