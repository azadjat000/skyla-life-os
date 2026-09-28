from datetime import date, timedelta

from flask import Blueprint, jsonify, request, render_template

from app.extensions import db
from app.models import FitnessWorkout, FitnessMetric, BodyMeasurement, FitnessGoal


fitness = Blueprint("fitness", __name__)


@fitness.get("/fitness")
def fitness_page():
    return render_template("fitness.html")


# ---------------------------------------------------------
# WORKOUTS
# ---------------------------------------------------------

@fitness.get("/api/fitness/workouts")
def get_workouts():
    rows = FitnessWorkout.query.order_by(
        FitnessWorkout.workout_date.desc(),
        FitnessWorkout.id.desc()
    ).all()

    return jsonify([
        {
            "id": x.id,
            "date": x.workout_date.isoformat() if x.workout_date else None,
            "type": x.workout_type or "",
            "duration": int(x.duration or 0),
            "exercises": x.exercises or "",
            "calories": int(x.calories or 0),
            "notes": x.notes or "",
        }
        for x in rows
    ])


@fitness.post("/api/fitness/workouts")
def add_workout():
    data = request.get_json() or {}

    workout_type = str(data.get("type", "")).strip()

    if not workout_type:
        return jsonify({"error": "Workout type is required"}), 400

    workout_date = data.get("date")

    item = FitnessWorkout(
        workout_date=date.fromisoformat(workout_date)
        if workout_date else date.today(),

        workout_type=workout_type,

        duration=int(data.get("duration", 0) or 0),

        exercises=str(
            data.get("exercises", "")
        ).strip(),

        calories=int(
            data.get("calories", 0) or 0
        ),

        notes=str(
            data.get("notes", "")
        ).strip()
    )

    db.session.add(item)
    db.session.commit()

    return jsonify({
        "ok": True,
        "id": item.id
    }), 201


@fitness.delete("/api/fitness/workouts/<int:workout_id>")
def delete_workout(workout_id):
    item = FitnessWorkout.query.get_or_404(workout_id)

    db.session.delete(item)
    db.session.commit()

    return jsonify({"ok": True})


# ---------------------------------------------------------
# FITNESS METRICS
# ---------------------------------------------------------

@fitness.get("/api/fitness/metrics")
def get_metrics():
    rows = FitnessMetric.query.order_by(
        FitnessMetric.metric_date.desc(),
        FitnessMetric.id.desc()
    ).all()

    return jsonify([
        {
            "id": x.id,
            "date": x.metric_date.isoformat(),
            "weight": float(x.weight or 0),
            "sleep": float(x.sleep_hours or 0),
            "running": float(x.running_km or 0),
            "calories": int(x.calories or 0),
            "notes": x.notes or "",
        }
        for x in rows
    ])


@fitness.post("/api/fitness/metrics")
def add_metric():
    data = request.get_json() or {}

    metric_date = data.get("date")

    item = FitnessMetric(
        metric_date=date.fromisoformat(metric_date)
        if metric_date else date.today(),

        weight=float(data.get("weight", 0) or 0),

        sleep_hours=float(
            data.get("sleep", 0) or 0
        ),

        running_km=float(
            data.get("running", 0) or 0
        ),

        calories=int(
            data.get("calories", 0) or 0
        ),

        notes=str(
            data.get("notes", "")
        ).strip()
    )

    db.session.add(item)
    db.session.commit()

    return jsonify({
        "ok": True,
        "id": item.id
    }), 201


@fitness.delete("/api/fitness/metrics/<int:metric_id>")
def delete_metric(metric_id):
    item = FitnessMetric.query.get_or_404(metric_id)

    db.session.delete(item)
    db.session.commit()

    return jsonify({"ok": True})


# ---------------------------------------------------------
# BODY MEASUREMENTS
# ---------------------------------------------------------

@fitness.get("/api/fitness/measurements")
def get_measurements():
    rows = BodyMeasurement.query.order_by(
        BodyMeasurement.measurement_date.desc(),
        BodyMeasurement.id.desc()
    ).all()

    return jsonify([
        {
            "id": x.id,
            "date": x.measurement_date.isoformat(),
            "chest": float(x.chest or 0),
            "waist": float(x.waist or 0),
            "arms": float(x.arms or 0),
            "thighs": float(x.thighs or 0),
            "body_fat": float(x.body_fat or 0),
            "notes": x.notes or "",
        }
        for x in rows
    ])


@fitness.post("/api/fitness/measurements")
def add_measurement():
    data = request.get_json() or {}

    measurement_date = data.get("date")

    item = BodyMeasurement(
        measurement_date=date.fromisoformat(measurement_date)
        if measurement_date else date.today(),

        chest=float(data.get("chest", 0) or 0),
        waist=float(data.get("waist", 0) or 0),
        arms=float(data.get("arms", 0) or 0),
        thighs=float(data.get("thighs", 0) or 0),
        body_fat=float(data.get("body_fat", 0) or 0),

        notes=str(
            data.get("notes", "")
        ).strip()
    )

    db.session.add(item)
    db.session.commit()

    return jsonify({
        "ok": True,
        "id": item.id
    }), 201


@fitness.delete("/api/fitness/measurements/<int:measurement_id>")
def delete_measurement(measurement_id):
    item = BodyMeasurement.query.get_or_404(measurement_id)

    db.session.delete(item)
    db.session.commit()

    return jsonify({"ok": True})


# ---------------------------------------------------------
# ANALYTICS
# ---------------------------------------------------------

@fitness.get("/api/fitness/analytics")
def fitness_analytics():

    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    workouts = FitnessWorkout.query.all()
    metrics = FitnessMetric.query.order_by(
        FitnessMetric.metric_date.asc()
    ).all()

    weekly_workouts = [
        x for x in workouts
        if x.workout_date and x.workout_date >= week_start
    ]

    monthly_workouts = [
        x for x in workouts
        if x.workout_date and x.workout_date >= month_start
    ]

    latest_weight = 0
    previous_weight = 0

    weight_rows = [
        x for x in metrics
        if float(x.weight or 0) > 0
    ]

    if weight_rows:
        latest_weight = float(weight_rows[-1].weight)

        if len(weight_rows) >= 2:
            previous_weight = float(
                weight_rows[-2].weight
            )

    weight_change = round(
        latest_weight - previous_weight, 2
    ) if previous_weight else 0

    weekly_minutes = sum(
        int(x.duration or 0)
        for x in weekly_workouts
    )

    monthly_minutes = sum(
        int(x.duration or 0)
        for x in monthly_workouts
    )

    weekly_calories = sum(
        int(x.calories or 0)
        for x in weekly_workouts
    )

    monthly_calories = sum(
        int(x.calories or 0)
        for x in monthly_workouts
    )

    running_total = sum(
        float(x.running_km or 0)
        for x in metrics
        if x.metric_date and x.metric_date >= month_start
    )

    sleep_rows = [
        float(x.sleep_hours or 0)
        for x in metrics
        if x.metric_date and
        x.metric_date >= month_start and
        float(x.sleep_hours or 0) > 0
    ]

    average_sleep = round(
        sum(sleep_rows) / len(sleep_rows), 2
    ) if sleep_rows else 0

    return jsonify({
        "latest_weight": latest_weight,
        "previous_weight": previous_weight,
        "weight_change": weight_change,

        "weekly": {
            "workouts": len(weekly_workouts),
            "minutes": weekly_minutes,
            "calories": weekly_calories,
        },

        "monthly": {
            "workouts": len(monthly_workouts),
            "minutes": monthly_minutes,
            "calories": monthly_calories,
            "running_km": round(running_total, 2),
            "average_sleep": average_sleep,
        }
    })


# ---------------------------------------------------------
# GRAPH DATA
# ---------------------------------------------------------

@fitness.get("/api/fitness/graph-data")
def fitness_graph_data():

    today = date.today()
    start_date = today - timedelta(days=89)

    workouts = FitnessWorkout.query.all()
    metrics = FitnessMetric.query.all()

    daily = []

    for i in range(90):

        current_date = start_date + timedelta(days=i)

        day_workouts = [
            x for x in workouts
            if x.workout_date == current_date
        ]

        day_metrics = [
            x for x in metrics
            if x.metric_date == current_date
        ]

        weight = 0
        sleep = 0
        running = 0
        metric_calories = 0

        if day_metrics:

            latest = sorted(
                day_metrics,
                key=lambda x: x.id
            )[-1]

            weight = float(latest.weight or 0)
            sleep = float(latest.sleep_hours or 0)
            running = float(latest.running_km or 0)
            metric_calories = int(latest.calories or 0)

        workout_minutes = sum(
            int(x.duration or 0)
            for x in day_workouts
        )

        workout_calories = sum(
            int(x.calories or 0)
            for x in day_workouts
        )

        daily.append({
            "date": current_date.isoformat(),
            "workouts": len(day_workouts),
            "minutes": workout_minutes,
            "calories": workout_calories,
            "metric_calories": metric_calories,
            "weight": weight,
            "sleep": sleep,
            "running": running,
        })

    return jsonify({
        "period": {
            "start": start_date.isoformat(),
            "end": today.isoformat()
        },
        "daily": daily
    })

@fitness.get("/api/fitness/goals")
def get_fitness_goals():

    goals = FitnessGoal.query.order_by(
        FitnessGoal.id.asc()
    ).all()

    return jsonify([
        {
            "id": g.id,
            "name": g.name,
            "metric": g.metric,
            "target": float(g.target or 0),
            "period": g.period,
            "active": bool(g.active),
        }
        for g in goals
    ])


@fitness.post("/api/fitness/goals")
def add_fitness_goal():

    data = request.get_json(silent=True) or {}

    name = str(data.get("name", "")).strip()
    metric = str(data.get("metric", "")).strip()
    target = float(data.get("target", 0) or 0)
    period = str(data.get("period", "weekly")).strip()

    if not name:
        return jsonify({"error": "Goal name is required"}), 400

    if metric not in {
        "weight",
        "running",
        "sleep",
        "workouts",
        "minutes",
        "calories"
    }:
        return jsonify({"error": "Invalid fitness metric"}), 400

    if target <= 0:
        return jsonify({"error": "Target must be greater than 0"}), 400

    if period not in {"weekly", "monthly"}:
        return jsonify({"error": "Invalid period"}), 400

    goal = FitnessGoal(
        name=name,
        metric=metric,
        target=target,
        period=period,
        active=True
    )

    db.session.add(goal)
    db.session.commit()

    return jsonify({
        "success": True,
        "id": goal.id
    }), 201


@fitness.put("/api/fitness/goals/<int:goal_id>")
def update_fitness_goal(goal_id):

    goal = db.session.get(FitnessGoal, goal_id)

    if not goal:
        return jsonify({"error": "Goal not found"}), 404

    data = request.get_json(silent=True) or {}

    if "name" in data:
        goal.name = str(data["name"]).strip()

    if "target" in data:
        target = float(data["target"] or 0)

        if target <= 0:
            return jsonify({"error": "Target must be greater than 0"}), 400

        goal.target = target

    if "period" in data:
        period = str(data["period"]).strip()

        if period not in {"weekly", "monthly"}:
            return jsonify({"error": "Invalid period"}), 400

        goal.period = period

    if "active" in data:
        goal.active = bool(data["active"])

    db.session.commit()

    return jsonify({"success": True})


@fitness.delete("/api/fitness/goals/<int:goal_id>")
def delete_fitness_goal(goal_id):

    goal = db.session.get(FitnessGoal, goal_id)

    if not goal:
        return jsonify({"error": "Goal not found"}), 404

    db.session.delete(goal)
    db.session.commit()

    return jsonify({"success": True})


@fitness.get("/api/fitness/goals/analytics")
def fitness_goals_analytics():

    today = date.today()

    workouts = FitnessWorkout.query.all()
    metrics = FitnessMetric.query.all()
    goals = FitnessGoal.query.filter_by(active=True).all()

    start_week = today - timedelta(days=today.weekday())
    start_month = today.replace(day=1)

    weekly_workouts = [
        x for x in workouts
        if x.workout_date >= start_week
        and x.workout_date <= today
    ]

    monthly_workouts = [
        x for x in workouts
        if x.workout_date >= start_month
        and x.workout_date <= today
    ]

    weekly_minutes = sum(
        int(x.duration or 0)
        for x in weekly_workouts
    )

    monthly_minutes = sum(
        int(x.duration or 0)
        for x in monthly_workouts
    )

    weekly_calories = sum(
        int(x.calories or 0)
        for x in weekly_workouts
    )

    monthly_running = sum(
        float(x.running_km or 0)
        for x in metrics
        if x.metric_date >= start_month
        and x.metric_date <= today
    )

    weekly_running = sum(
        float(x.running_km or 0)
        for x in metrics
        if x.metric_date >= start_week
        and x.metric_date <= today
    )

    weekly_sleep_values = [
        float(x.sleep_hours or 0)
        for x in metrics
        if x.metric_date >= start_week
        and x.metric_date <= today
        and float(x.sleep_hours or 0) > 0
    ]

    monthly_sleep_values = [
        float(x.sleep_hours or 0)
        for x in metrics
        if x.metric_date >= start_month
        and x.metric_date <= today
        and float(x.sleep_hours or 0) > 0
    ]

    weekly_average_sleep = (
        sum(weekly_sleep_values) / len(weekly_sleep_values)
        if weekly_sleep_values else 0
    )

    monthly_average_sleep = (
        sum(monthly_sleep_values) / len(monthly_sleep_values)
        if monthly_sleep_values else 0
    )

    results = []

    for goal in goals:

        actual = 0

        if goal.metric == "workouts":
            actual = (
                len(weekly_workouts)
                if goal.period == "weekly"
                else len(monthly_workouts)
            )

        elif goal.metric == "minutes":
            actual = (
                weekly_minutes
                if goal.period == "weekly"
                else monthly_minutes
            )

        elif goal.metric == "calories":
            actual = (
                weekly_calories
                if goal.period == "weekly"
                else sum(
                    int(x.calories or 0)
                    for x in monthly_workouts
                )
            )

        elif goal.metric == "running":
            actual = (
                weekly_running
                if goal.period == "weekly"
                else monthly_running
            )

        elif goal.metric == "sleep":
            actual = (
                weekly_average_sleep
                if goal.period == "weekly"
                else monthly_average_sleep
            )

        elif goal.metric == "weight":

            weight_rows = sorted(
                [
                    x for x in metrics
                    if float(x.weight or 0) > 0
                ],
                key=lambda x: (x.metric_date, x.id)
            )

            if weight_rows:
                actual = float(weight_rows[-1].weight or 0)

        target = float(goal.target or 0)

        if goal.metric == "weight" and target > 0:

            weight_rows = sorted(
                [
                    x for x in metrics
                    if float(x.weight or 0) > 0
                ],
                key=lambda x: (x.metric_date, x.id)
            )

            if weight_rows:
                starting_weight = float(weight_rows[0].weight or 0)

                if abs(starting_weight - target) < 0.001:
                    progress = 100
                else:
                    distance = abs(starting_weight - target)
                    achieved = abs(starting_weight - actual)

                    progress = min(
                        100,
                        max(0, (achieved / distance) * 100)
                    )

                    # Do not count movement beyond the target
                    # as extra progress in the wrong direction.
                    if starting_weight > target and actual > starting_weight:
                        progress = 0
                    elif starting_weight < target and actual < starting_weight:
                        progress = 0
        elif target > 0:
            progress = min(
                100,
                max(0, (actual / target) * 100)
            )
        else:
            progress = 0

        if progress >= 100:
            status = "Completed"
        elif progress > 0:
            status = "In progress"
        else:
            status = "Not started"

        results.append({
            "id": goal.id,
            "name": goal.name,
            "metric": goal.metric,
            "period": goal.period,
            "target": target,
            "actual": round(actual, 2),
            "progress": round(progress, 1),
            "status": status,
        })

    return jsonify({
        "goals": results,
        "summary": {
            "weekly_workouts": len(weekly_workouts),
            "weekly_minutes": weekly_minutes,
            "weekly_calories": weekly_calories,
            "weekly_running": round(weekly_running, 2),
            "monthly_running": round(monthly_running, 2),
            "weekly_average_sleep": round(weekly_average_sleep, 2),
            "monthly_average_sleep": round(monthly_average_sleep, 2),
        }
    })
