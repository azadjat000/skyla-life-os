from app import create_app
from app.extensions import db
from app.models import FinanceEntry
from app.services.finance_crypto import encrypt_text, decrypt_text
from sqlalchemy import inspect, text

app = create_app()

with app.app_context():

    inspector = inspect(db.engine)
    tables = inspector.get_table_names()

    if "finance_entry" not in tables:
        raise SystemExit("ERROR: finance_entry table not found")

    columns = {
        col["name"]
        for col in inspector.get_columns("finance_entry")
    }

    required = {
        "encrypted_category": "TEXT",
        "encrypted_description": "TEXT",
        "encrypted_amount": "TEXT",
    }

    for name, dtype in required.items():
        if name not in columns:
            db.session.execute(
                text(
                    f"ALTER TABLE finance_entry "
                    f"ADD COLUMN {name} {dtype}"
                )
            )
            print(f"ADDED COLUMN: {name}")
        else:
            print(f"COLUMN EXISTS: {name}")

    db.session.commit()

    entries = FinanceEntry.query.order_by(
        FinanceEntry.id
    ).all()

    print(f"FINANCE RECORDS FOUND: {len(entries)}")

    migrated = 0
    already = 0

    for entry in entries:

        if (
            entry.encrypted_amount
            and entry.encrypted_category is not None
            and entry.encrypted_description is not None
        ):
            already += 1
            continue

        entry.encrypted_amount = encrypt_text(
            str(entry.amount)
        )

        entry.encrypted_category = encrypt_text(
            entry.category or ""
        )

        entry.encrypted_description = encrypt_text(
            entry.description or ""
        )

        migrated += 1

    db.session.commit()

    print(f"NEWLY ENCRYPTED: {migrated}")
    print(f"ALREADY ENCRYPTED: {already}")


    # --------------------------------------------------------
    # Verify every encrypted record.
    # --------------------------------------------------------

    failures = []

    for entry in entries:

        try:
            amount = decrypt_text(entry.encrypted_amount)
            category = decrypt_text(entry.encrypted_category)
            description = decrypt_text(entry.encrypted_description)

            if amount is None:
                failures.append(entry.id)

            if category is None:
                failures.append(entry.id)

            if description is None:
                failures.append(entry.id)

        except Exception as exc:
            print(
                f"DECRYPTION FAILED FOR ENTRY {entry.id}: {exc}"
            )
            failures.append(entry.id)

    if failures:
        print(
            "FAILED ENTRY IDS:",
            sorted(set(failures))
        )
        raise SystemExit(
            "FINANCE ENCRYPTION VERIFY: FAILED"
        )

    print(f"RECORDS VERIFIED: {len(entries)}")
    print("FINANCE ENCRYPTION MIGRATION: OK")
