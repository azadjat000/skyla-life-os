from flask import Blueprint, render_template

pages = Blueprint("pages", __name__)

@pages.get("/motivation")
def motivation():
    return render_template("module.html", title="🔥 Motivation", subtitle="Build your reason, vision and daily drive.", module="motivation")

@pages.get("/discipline")
def discipline():
    return render_template("module.html", title="🧱 Discipline", subtitle="Turn your routines into consistent action.", module="discipline")

@pages.get("/obsession")
def obsession():
    return render_template("module.html", title="⚡ Obsession", subtitle="Focused commitment toward your biggest target.", module="obsession")

@pages.get("/calendar")
def calendar():
    return render_template("module.html", title="📅 Calendar", subtitle="Plan your days, weeks and months.", module="calendar")

@pages.get("/routine")
def routine():
    return render_template("module.html", title="🕒 Daily Routine", subtitle="Manage your hourly schedule and recurring tasks.", module="routine")
@pages.get("/reminders")
def reminders():
    return render_template("module.html", title="🔔 Reminders", subtitle="Create recurring reminders and alerts.", module="reminders")

@pages.get("/analytics")
def analytics():
    return render_template("module.html", title="📊 Analytics", subtitle="Understand your progress with data and graphs.", module="analytics")

@pages.get("/customization")
def customization():
    return render_template("module.html", title="🎨 Customization", subtitle="Customize Skyla Life OS your way.", module="customization")

@pages.get("/settings")
def settings():
    return render_template("module.html", title="⚙️ Settings", subtitle="Configure your Skyla Life OS.", module="settings")
