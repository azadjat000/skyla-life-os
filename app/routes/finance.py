from datetime import date, timedelta, datetime
import secrets
import hmac
from flask import Blueprint, request, jsonify, session
from app.extensions import db
from app.models import FinanceEntry, FinanceSettings, FinanceBudget, FinanceSavingsGoal
from app.services.security import hash_pin, verify_pin
from app.services.finance_crypto import encrypt_text, decrypt_text

finance = Blueprint("finance", __name__, url_prefix="/api/finance")


@finance.get("/csrf")
def csrf_token():
    """Return a per-session CSRF token for Finance API requests."""
    token = session.get("finance_csrf_token")

    if not token:
        token = secrets.token_urlsafe(32)
        session["finance_csrf_token"] = token

    return jsonify({
        "csrf_token": token
    })


@finance.before_request
def protect_finance_mutations():
    """Require CSRF protection for every state-changing Finance request."""
    if request.method not in {"POST", "PUT", "DELETE"}:
        return None

    expected = session.get("finance_csrf_token")
    supplied = request.headers.get("X-CSRF-Token", "")

    if not expected or not supplied:
        return jsonify({
            "ok": False,
            "message": "CSRF validation failed."
        }), 403

    if not hmac.compare_digest(str(expected), str(supplied)):
        return jsonify({
            "ok": False,
            "message": "CSRF validation failed."
        }), 403

    return None
    
def finance_budget_amount(budget):
    """Decrypt a FinanceBudget amount."""
    if not budget:
        return 0.0

    return float(
        decrypt_text(budget.encrypted_amount) or 0
    )


def finance_savings_goal_values(goal):
    """Decrypt sensitive FinanceSavingsGoal values."""
    return {
        "name": decrypt_text(goal.encrypted_name) or "",
        "target": float(
            decrypt_text(goal.encrypted_target) or 0
        ),
        "saved": float(
            decrypt_text(goal.encrypted_saved) or 0
        ),
    }


def finance_entry_values(row):
    """Return decrypted sensitive FinanceEntry values."""
    return {
        "amount": float(decrypt_text(row.encrypted_amount)),
        "category": decrypt_text(row.encrypted_category) or "",
        "description": decrypt_text(row.encrypted_description) or "",
    }





FINANCE_AUTO_LOCK_MINUTES = 15
FINANCE_MAX_PIN_ATTEMPTS = 5
FINANCE_PIN_LOCKOUT_SECONDS = 5 * 60


def finance_is_unlocked():
    if not session.get("finance_unlocked"):
        return False

    last = session.get("finance_last_activity")

    if not last:
        session.pop("finance_unlocked", None)
        return False

    try:
        last_time = datetime.fromisoformat(last)
    except Exception:
        session.pop("finance_unlocked", None)
        session.pop("finance_last_activity", None)
        return False

    elapsed = (
        datetime.utcnow() - last_time
    ).total_seconds()

    if elapsed > FINANCE_AUTO_LOCK_MINUTES * 60:
        session.pop("finance_unlocked", None)
        session.pop("finance_last_activity", None)
        return False

    session["finance_last_activity"] = datetime.utcnow().isoformat()
    return True


def require_finance_unlock():
    if not finance_is_unlocked():
        return jsonify({"error": "Finance locked"}), 403
    return None


@finance.post("/setup")
def setup_pin():
    data = request.get_json(silent=True) or {}
    pin = str(data.get("pin", ""))

    if not pin.isdigit() or len(pin) < 4 or len(pin) > 8:
        return jsonify({
            "ok": False,
            "message": "PIN must contain 4-8 digits."
        }), 400

    settings = FinanceSettings.query.first()

    if settings is None:
        settings = FinanceSettings(enabled=True)
        db.session.add(settings)

    settings.pin_hash = hash_pin(pin)
    settings.enabled = True
    db.session.commit()

    return jsonify({
        "ok": True,
        "message": "Finance Vault PIN created."
    })


@finance.post("/unlock")
def unlock():
    data = request.get_json(silent=True) or {}
    pin = str(data.get("pin", ""))

    settings = FinanceSettings.query.first()

    if not settings or not settings.pin_hash:
        return jsonify({
            "ok": False,
            "message": "Finance PIN has not been configured."
        }), 400

    now = datetime.utcnow()

    lockout_until = session.get("finance_pin_lockout_until")
    if lockout_until:
        try:
            lockout_time = datetime.fromisoformat(lockout_until)
            remaining = (lockout_time - now).total_seconds()

            if remaining > 0:
                return jsonify({
                    "ok": False,
                    "message": "Too many incorrect PIN attempts. Try again later.",
                    "retry_after_seconds": int(remaining) + 1
                }), 429

            session.pop("finance_pin_lockout_until", None)
            session.pop("finance_pin_failed_attempts", None)

        except Exception:
            session.pop("finance_pin_lockout_until", None)
            session.pop("finance_pin_failed_attempts", None)

    if not verify_pin(pin, settings.pin_hash):
        failed = int(session.get("finance_pin_failed_attempts", 0)) + 1
        session["finance_pin_failed_attempts"] = failed

        if failed >= FINANCE_MAX_PIN_ATTEMPTS:
            lockout_until = now + timedelta(
                seconds=FINANCE_PIN_LOCKOUT_SECONDS
            )
            session["finance_pin_lockout_until"] = lockout_until.isoformat()
            session["finance_pin_failed_attempts"] = 0

            return jsonify({
                "ok": False,
                "message": "Too many incorrect PIN attempts. Try again later.",
                "retry_after_seconds": FINANCE_PIN_LOCKOUT_SECONDS
            }), 429

        return jsonify({
            "ok": False,
            "message": "Incorrect PIN.",
            "attempts_remaining": FINANCE_MAX_PIN_ATTEMPTS - failed
        }), 401

    session.pop("finance_pin_failed_attempts", None)
    session.pop("finance_pin_lockout_until", None)

    session["finance_unlocked"] = True
    session["finance_last_activity"] = now.isoformat()

    return jsonify({
        "ok": True,
        "message": "Finance Vault unlocked."
    })


@finance.post("/lock")
def lock():
    session.pop("finance_unlocked", None)

    return jsonify({
        "ok": True,
        "message": "Finance Vault locked."
    })



@finance.post("/change-pin")
def change_pin():

    if not finance_is_unlocked():
        return jsonify({"error": "Finance locked"}), 403

    data = request.get_json(silent=True) or {}

    old_pin = str(data.get("old_pin", ""))
    new_pin = str(data.get("new_pin", ""))

    settings = FinanceSettings.query.first()

    if not settings or not settings.pin_hash:
        return jsonify({"error": "Finance PIN is not configured"}), 400

    if not verify_pin(old_pin, settings.pin_hash):
        return jsonify({"error": "Current PIN is incorrect"}), 401

    if not new_pin.isdigit() or len(new_pin) < 4 or len(new_pin) > 8:
        return jsonify({
            "error": "New PIN must contain 4-8 digits"
        }), 400

    settings.pin_hash = hash_pin(new_pin)

    db.session.commit()

    return jsonify({
        "ok": True,
        "message": "Finance PIN changed"
    })


@finance.get("/status")
def status():
    settings = FinanceSettings.query.first()

    unlocked = finance_is_unlocked() if session.get("finance_unlocked") else False

    return jsonify({
        "configured": bool(settings and settings.pin_hash),
        "unlocked": unlocked
    })


@finance.get("/entries")
def entries():
    if not finance_is_unlocked():
        return jsonify({
            "ok": False,
            "message": "Finance Vault is locked."
        }), 403

    rows = FinanceEntry.query.order_by(
        FinanceEntry.entry_date.desc(),
        FinanceEntry.id.desc()
    ).all()

    output = []

    for row in rows:
        values = finance_entry_values(row)

        output.append({
            "id": row.id,
            "date": row.entry_date.isoformat(),
            "type": row.entry_type,
            "category": values["category"],
            "description": values["description"],
            "amount": values["amount"]
        })

    return jsonify({
        "ok": True,
        "entries": output
    })


@finance.post("/entries")
def add_entry():
    if not finance_is_unlocked():
        return jsonify({
            "ok": False,
            "message": "Finance Vault is locked."
        }), 403

    data = request.get_json(silent=True) or {}

    entry_type = data.get("type")

    if entry_type not in ("income", "expense"):
        return jsonify({
            "ok": False,
            "message": "Type must be income or expense."
        }), 400

    try:
        amount = float(data.get("amount", 0))
    except (TypeError, ValueError):
        return jsonify({
            "ok": False,
            "message": "Invalid amount."
        }), 400

    if amount <= 0:
        return jsonify({
            "ok": False,
            "message": "Amount must be greater than zero."
        }), 400

    category = str(data.get("category", "General"))
    description = str(data.get("description", ""))

    entry = FinanceEntry(
        entry_type=entry_type,

        # Sensitive values are encrypted before storage.
        encrypted_category=encrypt_text(category),
        encrypted_description=encrypt_text(description),
        encrypted_amount=encrypt_text(str(amount))
    )

    db.session.add(entry)
    db.session.commit()

    return jsonify({
        "ok": True,
        "id": entry.id
    })


@finance.get("/analytics")
def finance_analytics():

    if not finance_is_unlocked():
        return jsonify({"error": "Finance locked"}), 403

    today = date.today()
    current_month = today.strftime("%Y-%m")

    entries = FinanceEntry.query.order_by(
        FinanceEntry.entry_date.asc(),
        FinanceEntry.id.asc()
    ).all()

    month_entries = [
        x for x in entries
        if x.entry_date.strftime("%Y-%m") == current_month
    ]

    decrypted_entries = {
        x.id: finance_entry_values(x)
        for x in month_entries
    }

    income = sum(
        decrypted_entries[x.id]["amount"]
        for x in month_entries
        if x.entry_type == "income"
    )

    expenses = sum(
        decrypted_entries[x.id]["amount"]
        for x in month_entries
        if x.entry_type == "expense"
    )

    balance = income - expenses

    budget = FinanceBudget.query.filter_by(
        month=current_month
    ).first()

    budget_amount = finance_budget_amount(budget)

    savings_goals = FinanceSavingsGoal.query.filter_by(
        active=True
    ).order_by(FinanceSavingsGoal.id.asc()).all()

    categories = {}

    for entry in month_entries:

        if entry.entry_type != "expense":
            continue

        values = decrypted_entries[entry.id]
        category = values["category"] or "Other"

        categories[category] = (
            categories.get(category, 0)
            + values["amount"]
        )

    return jsonify({
        "month": current_month,
        "income": round(income, 2),
        "expenses": round(expenses, 2),
        "balance": round(balance, 2),
        "budget": round(budget_amount, 2),
        "budget_used": round(
            (expenses / budget_amount * 100)
            if budget_amount > 0 else 0,
            1
        ),
        "categories": [
            {
                "category": key,
                "amount": round(value, 2)
            }
            for key, value in sorted(
                categories.items(),
                key=lambda item: item[1],
                reverse=True
            )
        ],
        "savings_goals": [
            {
                "id": goal.id,
                "name": finance_savings_goal_values(goal)["name"],
                "target": round(
                    finance_savings_goal_values(goal)["target"],
                    2
                ),
                "saved": round(
                    finance_savings_goal_values(goal)["saved"],
                    2
                ),
                "progress": round(
                    min(
                        100,
                        (
                            finance_savings_goal_values(goal)["saved"]
                            /
                            max(
                                finance_savings_goal_values(goal)["target"],
                                1
                            )
                        ) * 100
                    ),
                    1
                )
            }
            for goal in savings_goals
        ]
    })


@finance.get("/graph-data")
def finance_graph_data():

    if not finance_is_unlocked():
        return jsonify({"error": "Finance locked"}), 403

    today = date.today()

    monthly = []

    for offset in range(11, -1, -1):

        year = today.year
        month = today.month - offset

        while month <= 0:
            year -= 1
            month += 12

        month_key = f"{year:04d}-{month:02d}"

        entries = FinanceEntry.query.all()

        month_entries = [
            x for x in entries
            if x.entry_date.strftime("%Y-%m") == month_key
        ]

        decrypted_entries = {
            x.id: finance_entry_values(x)
            for x in month_entries
        }

        income = sum(
            decrypted_entries[x.id]["amount"]
            for x in month_entries
            if x.entry_type == "income"
        )

        expenses = sum(
            decrypted_entries[x.id]["amount"]
            for x in month_entries
            if x.entry_type == "expense"
        )

        monthly.append({
            "month": month_key,
            "income": round(income, 2),
            "expenses": round(expenses, 2),
            "balance": round(income - expenses, 2)
        })

    return jsonify({
        "monthly": monthly
    })


@finance.post("/budget")
def set_finance_budget():

    if not finance_is_unlocked():
        return jsonify({"error": "Finance locked"}), 403

    data = request.get_json(silent=True) or {}

    month = str(
        data.get("month", date.today().strftime("%Y-%m"))
    ).strip()

    amount = float(data.get("amount", 0) or 0)

    if len(month) != 7 or amount <= 0:
        return jsonify({
            "error": "Valid month and positive budget required"
        }), 400

    budget = FinanceBudget.query.filter_by(
        month=month
    ).first()

    if not budget:
        budget = FinanceBudget(month=month)
        db.session.add(budget)

    budget.encrypted_amount = encrypt_text(str(amount))

    db.session.commit()

    return jsonify({
        "success": True,
        "month": month,
        "amount": amount
    })


@finance.get("/budget")
def get_finance_budget():

    if not finance_is_unlocked():
        return jsonify({"error": "Finance locked"}), 403

    month = request.args.get(
        "month",
        date.today().strftime("%Y-%m")
    )

    budget = FinanceBudget.query.filter_by(
        month=month
    ).first()

    return jsonify({
        "month": month,
        "amount": finance_budget_amount(budget)
    })


@finance.post("/savings-goals")
def add_finance_savings_goal():

    if not finance_is_unlocked():
        return jsonify({"error": "Finance locked"}), 403

    data = request.get_json(silent=True) or {}

    name = str(data.get("name", "")).strip()
    target = float(data.get("target", 0) or 0)
    saved = float(data.get("saved", 0) or 0)

    if not name:
        return jsonify({"error": "Goal name required"}), 400

    if target <= 0:
        return jsonify({"error": "Target must be greater than 0"}), 400

    if saved < 0:
        return jsonify({"error": "Saved amount cannot be negative"}), 400

    goal = FinanceSavingsGoal(
        encrypted_name=encrypt_text(name),
        encrypted_target=encrypt_text(str(target)),
        encrypted_saved=encrypt_text(str(saved)),
        active=True
    )

    db.session.add(goal)
    db.session.commit()

    return jsonify({
        "success": True,
        "id": goal.id
    }), 201


@finance.put("/savings-goals/<int:goal_id>")
def update_finance_savings_goal(goal_id):

    if not finance_is_unlocked():
        return jsonify({"error": "Finance locked"}), 403

    goal = db.session.get(
        FinanceSavingsGoal,
        goal_id
    )

    if not goal:
        return jsonify({"error": "Savings goal not found"}), 404

    data = request.get_json(silent=True) or {}

    if "name" in data:
        goal.encrypted_name = encrypt_text(
            str(data["name"]).strip()
        )

    if "target" in data:
        target = float(data["target"] or 0)

        if target <= 0:
            return jsonify({
                "error": "Target must be greater than 0"
            }), 400

        goal.encrypted_target = encrypt_text(str(target))

    if "saved" in data:
        saved = float(data["saved"] or 0)

        if saved < 0:
            return jsonify({
                "error": "Saved amount cannot be negative"
            }), 400

        goal.encrypted_saved = encrypt_text(str(saved))

    if "active" in data:
        goal.active = bool(data["active"])

    db.session.commit()

    return jsonify({"success": True})


@finance.delete("/savings-goals/<int:goal_id>")
def delete_finance_savings_goal(goal_id):

    if not finance_is_unlocked():
        return jsonify({"error": "Finance locked"}), 403

    goal = db.session.get(
        FinanceSavingsGoal,
        goal_id
    )

    if not goal:
        return jsonify({"error": "Savings goal not found"}), 404

    db.session.delete(goal)
    db.session.commit()

    return jsonify({"success": True})
