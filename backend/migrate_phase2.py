from sqlalchemy import text

from database import Base, engine

import models


def migrate_phase2(target_engine=engine):

    # Create missing tables first; create_all leaves existing tables intact.
    Base.metadata.create_all(bind=target_engine)

    with target_engine.begin() as connection:

        columns = {
            row[1]
            for row in connection.exec_driver_sql(
                "PRAGMA table_info(invoices)"
            ).fetchall()
        }

        if "risk_status" not in columns:

            connection.execute(text(
                "ALTER TABLE invoices "
                "ADD COLUMN risk_status VARCHAR(20) "
                "NOT NULL DEFAULT 'PENDING'"
            ))

        if "risk_score" not in columns:

            connection.execute(text(
                "ALTER TABLE invoices "
                "ADD COLUMN risk_score INTEGER "
                "NOT NULL DEFAULT 0"
            ))


if __name__ == "__main__":
    migrate_phase2()
    print("Phase 2 database migration completed.")