from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# Import models so SQLAlchemy registers all tables.
from models import (
    Vendor,
    Invoice,
    InvoiceItem,
    RiskFinding
)

from routes.invoices import router as invoice_router
from migrate_phase2 import migrate_phase2
from migrate_phase3 import migrate_phase3
from core.demo_credentials import validate_demo_credentials
from database import SessionLocal

from routes.auth import router as auth_router

from routes.approvals import router as approval_router
from routes.audit import router as audit_router


migrate_phase2()
migrate_phase3()


app = FastAPI(
    title="LedgerLock API",
    description="AI Invoice Intelligence and Payment Security",
    version="1.0.0"
)


@app.on_event("startup")
def check_demo_credentials():
    db: Session = SessionLocal()

    try:
        validate_demo_credentials(db)
    finally:
        db.close()


app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173"
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]
)


@app.get("/health")
def health():

    return {"status": "ok"}

app.include_router(approval_router)
app.include_router(invoice_router)
app.include_router(auth_router)
app.include_router(audit_router)