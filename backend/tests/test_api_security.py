from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import models
from core.security import hash_password
from core.config import get_frontend_origins
from database import Base, get_db
from models.user import User
from routes.approvals import router as approval_router
from routes.audit import router as audit_router
from routes.auth import router as auth_router
from routes.invoices import router as invoice_router


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    monkeypatch.setattr(
        "routes.invoices.STORAGE_DIR",
        tmp_path / "uploads",
    )

    with Session(engine) as db:
        db.add_all([
            User(
                full_name="Test Reviewer",
                email="reviewer@test.invalid",
                password_hash=hash_password("reviewer-test-password"),
                role="FINANCE_REVIEWER",
                is_active=True,
            ),
            User(
                full_name="Test Approver",
                email="approver@test.invalid",
                password_hash=hash_password("approver-test-password"),
                role="FINANCE_APPROVER",
                is_active=True,
            ),
            User(
                full_name="Test Clerk",
                email="clerk@test.invalid",
                password_hash=hash_password("clerk-test-password"),
                role="AP_CLERK",
                is_active=True,
            ),
        ])
        db.commit()

    def override_get_db():
        with Session(engine) as db:
            yield db

    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_frontend_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(auth_router)
    app.include_router(invoice_router)
    app.include_router(approval_router)
    app.include_router(audit_router)
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    Base.metadata.drop_all(engine)
    engine.dispose()


def login(client, email, password):
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_auth_roles_protect_invoice_pdf_and_audit_routes(api_client):
    client = api_client
    assert client.get("/api/invoices").status_code == 401
    assert client.get("/api/auth/me").status_code == 401
    assert client.post(
        "/api/invoices/upload",
        files={"file": ("sample_invoice.pdf", b"%PDF-", "application/pdf")},
    ).status_code == 401

    reviewer_token = login(
        client,
        "reviewer@test.invalid",
        "reviewer-test-password",
    )
    reviewer_headers = {"Authorization": f"Bearer {reviewer_token}"}

    sample_pdf = Path(__file__).parents[1] / "sample_invoice.pdf"
    upload_response = client.post(
        "/api/invoices/upload",
        headers=reviewer_headers,
        files={
            "file": (
                "sample_invoice.pdf",
                sample_pdf.read_bytes(),
                "application/pdf",
            )
        },
    )
    assert upload_response.status_code == 201
    invoice_id = upload_response.json()["id"]
    assert "raw_text" not in upload_response.json()

    assert client.get(
        "/api/auth/me",
        headers=reviewer_headers,
    ).json()["role"] == "FINANCE_REVIEWER"
    assert client.get(
        "/api/invoices",
        headers=reviewer_headers,
    ).status_code == 200
    assert client.get(
        f"/api/invoices/{invoice_id}",
        headers=reviewer_headers,
    ).status_code == 200
    assert client.get(
        f"/api/invoices/{invoice_id}/risk",
        headers=reviewer_headers,
    ).status_code == 200

    source_response = client.get(
        f"/api/invoices/{invoice_id}/source",
        headers=reviewer_headers,
    )
    assert source_response.status_code == 200
    assert source_response.content.startswith(b"%PDF-")
    assert client.get(
        f"/api/invoices/{invoice_id}/source"
    ).status_code == 401

    assert client.get(
        "/api/audit",
        headers=reviewer_headers,
    ).status_code == 200
    assert client.get(
        f"/api/invoices/{invoice_id}/audit",
        headers=reviewer_headers,
    ).status_code == 200

    clerk_token = login(
        client,
        "clerk@test.invalid",
        "clerk-test-password",
    )
    clerk_headers = {"Authorization": f"Bearer {clerk_token}"}
    assert client.get(
        "/api/invoices",
        headers=clerk_headers,
    ).status_code == 403
    assert client.post(
        f"/api/invoices/{invoice_id}/analyze",
        headers=clerk_headers,
    ).status_code == 403

    assert client.post(
        f"/api/invoices/{invoice_id}/approve",
        headers=reviewer_headers,
    ).status_code == 403


def test_login_rejects_wrong_password(api_client):
    response = api_client.post(
        "/api/auth/login",
        json={
            "email": "reviewer@test.invalid",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    "origin",
    [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
)
def test_documented_frontend_origins_pass_cors_preflight(api_client, origin):
    response = api_client.options(
        "/api/invoices",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
