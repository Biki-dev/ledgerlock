from database import Base, engine

import models


INVOICE_COLUMNS = {

    "approval_status":
        "VARCHAR(20) NOT NULL DEFAULT 'PENDING'",

    "review_status":
        "VARCHAR(20) NOT NULL DEFAULT 'NOT_REQUIRED'",

    "reviewed_by_id": "INTEGER",

    "reviewed_at": "DATETIME",

    "review_note": "TEXT",

    "verification_status":
        "VARCHAR(20) NOT NULL DEFAULT 'NOT_REQUIRED'",

    "verified_by_id": "INTEGER",

    "verified_at": "DATETIME",

    "verification_method": "VARCHAR(60)",

    "verification_reference": "VARCHAR(255)",

    "verification_note": "TEXT",

    "approved_by_id": "INTEGER",

    "approved_at": "DATETIME",

    "rejected_by_id": "INTEGER",

    "rejected_at": "DATETIME",

    "rejection_reason": "TEXT"
}


def migrate_phase3(target_engine=engine):

    Base.metadata.create_all(bind=target_engine)

    with target_engine.begin() as connection:

        existing_columns = {
            row[1]
            for row in connection.exec_driver_sql(
                "PRAGMA table_info(invoices)"
            ).fetchall()
        }

        for column, definition in INVOICE_COLUMNS.items():

            if column not in existing_columns:

                connection.exec_driver_sql(
                    f"ALTER TABLE invoices "
                    f"ADD COLUMN {column} {definition}"
                )


if __name__ == "__main__":
    migrate_phase3()
    print("Phase 3 migration completed.")