from datetime import datetime, date, date
from .extensions import db


class Routine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), default="routine")
    time = db.Column(db.String(10))
    description = db.Column(db.Text)
    repeat = db.Column(db.String(50), default="daily")
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class RoutineLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    routine_id = db.Column(
        db.Integer,
        db.ForeignKey("routine.id"),
        nullable=False
    )
    log_date = db.Column(db.Date, default=date.today)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)


class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), default="general")
    target_days = db.Column(db.Integer, default=7)
    streak = db.Column(db.Integer, default=0)
    completed_today = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class HabitLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey("habit.id"), nullable=False)
    log_date = db.Column(db.Date, default=date.today)
    completed = db.Column(db.Boolean, default=True)


class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), default="general")
    description = db.Column(db.Text)
    progress = db.Column(db.Integer, default=0)
    target = db.Column(db.Integer, default=100)
    deadline = db.Column(db.Date)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Sport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    icon = db.Column(db.String(20), default="🏆")
    category = db.Column(db.String(50), default="custom")
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SportSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sport_id = db.Column(
        db.Integer,
        db.ForeignKey("sport.id"),
        nullable=False
    )
    session_date = db.Column(db.Date, default=date.today)
    session_type = db.Column(db.String(100), default="Training")
    duration = db.Column(db.Integer, default=0)
    intensity = db.Column(db.String(30), default="medium")
    drills = db.Column(db.Text, default="")
    notes = db.Column(db.Text, default="")
    rating = db.Column(db.Float, default=0)
    metrics = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SportSkill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sport_id = db.Column(
        db.Integer,
        db.ForeignKey("sport.id"),
        nullable=False
    )
    name = db.Column(db.String(100), nullable=False)
    current = db.Column(db.Float, default=0)
    target = db.Column(db.Float, default=100)
    unit = db.Column(db.String(30), default="%")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SportSkillLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    skill_id = db.Column(
        db.Integer,
        db.ForeignKey("sport_skill.id"),
        nullable=False
    )
    value = db.Column(db.Float, default=0)
    log_date = db.Column(db.Date, default=date.today)
    notes = db.Column(db.Text, default="")


class SportPersonalBest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sport_id = db.Column(
        db.Integer,
        db.ForeignKey("sport.id"),
        nullable=False
    )
    metric = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Float, default=0)
    unit = db.Column(db.String(30), default="")
    record_date = db.Column(db.Date, default=date.today)
    notes = db.Column(db.Text, default="")


class SportTarget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sport_id = db.Column(
        db.Integer,
        db.ForeignKey("sport.id"),
        nullable=False
    )
    title = db.Column(db.String(200), nullable=False)
    target = db.Column(db.Float, default=100)
    actual = db.Column(db.Float, default=0)
    unit = db.Column(db.String(30), default="")
    deadline = db.Column(db.Date)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class FootballSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_date = db.Column(db.Date, default=date.today)
    session_type = db.Column(db.String(100))
    duration = db.Column(db.Integer, default=0)
    drills = db.Column(db.Text)
    notes = db.Column(db.Text)
    rating = db.Column(db.Integer, default=0)


class FitnessWorkout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    workout_date = db.Column(db.Date, default=date.today)
    workout_type = db.Column(db.String(100))
    duration = db.Column(db.Integer, default=0)
    exercises = db.Column(db.Text)
    calories = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)


class Motivation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)

    # Motivation Dashboard sections
    category = db.Column(db.String(50), default="daily")
    reason = db.Column(db.Text, default="")
    vision = db.Column(db.Text, default="")
    reward = db.Column(db.String(200), default="")

    # Daily reflection
    morning_reflection = db.Column(db.Text, default="")
    evening_reflection = db.Column(db.Text, default="")

    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class FocusSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    goal_id = db.Column(db.Integer, db.ForeignKey("goal.id"))
    session_date = db.Column(db.Date, default=date.today)
    duration = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)


class FinanceEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entry_date = db.Column(db.Date, default=date.today)
    entry_type = db.Column(db.String(20), nullable=False)

    # Finance Vault sensitive fields are encrypted at rest.
    encrypted_category = db.Column(db.Text, default=None)
    encrypted_description = db.Column(db.Text, default=None)
    encrypted_amount = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class FinanceSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pin_hash = db.Column(db.String(255))
    enabled = db.Column(db.Boolean, default=True)


class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    reminder_time = db.Column(db.String(10))
    repeat = db.Column(db.String(50), default="daily")
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Reminder notification preferences
    sound_enabled = db.Column(
        db.Boolean,
        default=True,
        nullable=False,
    )
    sound_type = db.Column(
        db.String(30),
        default="bell",
        nullable=False,
    )
    sound_volume = db.Column(
        db.Integer,
        default=80,
        nullable=False,
    )
    priority = db.Column(
        db.String(20),
        default="normal",
        nullable=False,
    )
    snooze_minutes = db.Column(
        db.Integer,
        default=5,
        nullable=False,
    )
    snooze_until = db.Column(
        db.DateTime,
        nullable=True,
    )


class ReminderLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reminder_id = db.Column(
        db.Integer,
        db.ForeignKey("reminder.id"),
        nullable=False
    )
    triggered_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    status = db.Column(
        db.String(30),
        default="triggered",
        nullable=False
    )


class AppSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)


class FootballSkill(db.Model):
    __tablename__ = "football_skills"

    id = db.Column(db.Integer, primary_key=True)
    skill = db.Column(db.String(50), nullable=False, unique=True)
    current = db.Column(db.Float, default=0)
    target = db.Column(db.Float, default=100)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


class FootballSkillLog(db.Model):
    __tablename__ = "football_skill_logs"

    id = db.Column(db.Integer, primary_key=True)
    skill_id = db.Column(
        db.Integer,
        db.ForeignKey("football_skills.id"),
        nullable=False
    )
    value = db.Column(db.Float, nullable=False)
    log_date = db.Column(db.Date, default=date.today)
    notes = db.Column(db.Text, default="")


class FitnessMetric(db.Model):
    __tablename__ = "fitness_metrics"

    id = db.Column(db.Integer, primary_key=True)
    metric_date = db.Column(db.Date, default=date.today, nullable=False)
    weight = db.Column(db.Float, default=0)
    sleep_hours = db.Column(db.Float, default=0)
    running_km = db.Column(db.Float, default=0)
    calories = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class BodyMeasurement(db.Model):
    __tablename__ = "body_measurements"

    id = db.Column(db.Integer, primary_key=True)
    measurement_date = db.Column(db.Date, default=date.today, nullable=False)
    chest = db.Column(db.Float, default=0)
    waist = db.Column(db.Float, default=0)
    arms = db.Column(db.Float, default=0)
    thighs = db.Column(db.Float, default=0)
    body_fat = db.Column(db.Float, default=0)
    notes = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class FitnessGoal(db.Model):
    __tablename__ = "fitness_goals"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    metric = db.Column(db.String(50), nullable=False)
    target = db.Column(db.Float, default=0)
    period = db.Column(db.String(20), default="weekly")
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class FinanceBudget(db.Model):
    __tablename__ = "finance_budgets"

    id = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.String(7), nullable=False, unique=True)

    # Sensitive Finance Vault data is encrypted at rest.
    encrypted_amount = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class FinanceSavingsGoal(db.Model):
    __tablename__ = "finance_savings_goals"

    id = db.Column(db.Integer, primary_key=True)

    # Sensitive Finance Vault data is encrypted at rest.
    encrypted_name = db.Column(db.Text, nullable=False)
    encrypted_target = db.Column(db.Text, nullable=False)
    encrypted_saved = db.Column(db.Text, nullable=False)

    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CalendarEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    event_time = db.Column(db.String(10))
    description = db.Column(db.Text)
    repeat = db.Column(db.String(50), default="none")
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
