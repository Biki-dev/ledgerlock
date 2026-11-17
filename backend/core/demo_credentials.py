import os

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.security import verify_password
from models.user import User


DEMO_PASSWORD_ENV = {
    "reviewer@ledgerlock.demo": "DEMO_REVIEWER_PASSWORD",
    "approver@ledgerlock.demo": "DEMO_APPROVER_PASSWORD",
    "admin@ledgerlock.demo": "DEMO_ADMIN_PASSWORD",
}


def validate_demo_credentials(db: Session) -> None:
    for email, environment_key in DEMO_PASSWORD_ENV.items():
        user = db.scalar(select(User).where(User.email == email))

        if user is None:
            continue

        configured_password = os.getenv(environment_key)

        if (
            not configured_password
            or len(configured_password) < 16
            or not verify_password(
                configured_password,
                user.password_hash
            )
        ):
            raise RuntimeError(
                f"Demo account {email} is not using its configured secret. "
                "Set a unique password of at least 16 characters and run "
                "seed_users.py before starting the application."
            )
