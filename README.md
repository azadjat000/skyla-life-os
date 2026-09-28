# Skyla Life OS

Personal Life Management OS for routines, habits, goals, motivation, discipline, obsession, sports, fitness, finance, reminders, calendar and analytics.

## Features

- 🧠 Motivation Dashboard
- 🎯 Discipline Dashboard
- 🔥 Obsession Dashboard
- 📅 Daily Routine
- ✅ Habits
- 🎯 Goals
- ⚽ Sports Hub
- 🏋️ Fitness
- 💰 Finance Vault
- 🔔 Reminders
- 📆 Calendar
- 📊 Analytics
- ⚙️ Customization
- 🔐 Settings

## Requirements

- Linux
- Python 3.12+ recommended
- Git
- Internet connection for initial dependency installation

## Installation

Clone the development branch:

    git clone -b v1.1-development https://github.com/azadjat000/skyla-life-os.git
    cd skyla-life-os
    ./install.sh

The installer automatically creates the local environment, Python virtual environment, SQLite database directory, launcher and desktop application entry.

## Start Skyla

From the project directory:

    ./launch.sh

Or open Applications → Skyla Life OS from the Linux desktop menu.

Skyla runs locally at:

    http://127.0.0.1:5000

## Uninstall

    ./uninstall.sh

The uninstaller removes the desktop launcher and runtime log. Your .env and database are preserved.

## Data & Privacy

Skyla Life OS is designed to run locally.

The application database is stored in:

    data/skyla_life_os.db

The local secret key is stored in:

    .env

These runtime files are excluded from Git by .gitignore.

Do not commit personal databases, secrets, passwords, PINs or other private information to a public repository.

## Development

Run Skyla locally:

    ./launch.sh

Check Python syntax:

    python -m compileall -q app

## Status

Skyla Life OS is under active development.

The v1.1-development branch contains the current development build.
