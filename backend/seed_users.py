import os

from database import SessionLocal, Base, engine

from models.user import User

from core.security import hash_password


Base.metadata.create_all(bind=engine)


DEMO_USERS = [

    {
        "full_name": "Finance Reviewer",
        "email": "reviewer@ledgerlock.demo",
        "password": os.getenv(
            "DEMO_REVIEWER_PASSWORD",
            "Review123!"
        ),
        "role": "FINANCE_REVIEWER"
    },

    {
        "full_name": "Finance Approver",
        "email": "approver@ledgerlock.demo",
        "password": os.getenv(
            "DEMO_APPROVER_PASSWORD",
            "Approve123!"
        ),
        "role": "FINANCE_APPROVER"
    },

    {
        "full_name": "System Administrator",
        "email": "admin@ledgerlock.demo",
        "password": os.getenv(
            "DEMO_ADMIN_PASSWORD",
            "Admin123!"
        ),
        "role": "ADMIN"
    }
]


db = SessionLocal()

try:

    for data in DEMO_USERS:

        existing = db.query(User).filter(
            User.email == data["email"]
        ).first()

        if existing:
            print("Already exists:", data["email"])
            continue

        user = User(

            full_name=data["full_name"],

            email=data["email"],

            password_hash=hash_password(
                data["password"]
            ),

            role=data["role"],

            is_active=True
        )

        db.add(user)

        print("Created:", data["email"])

    db.commit()

finally:

    db.close()