import os
import json
import tempfile

from dotenv import load_dotenv

load_dotenv()


KANE_BASE_URL = os.getenv(
    "KANE_BASE_URL",
    "http://localhost:5173"
)

APPROVER_EMAIL = "approver@ledgerlock.demo"

APPROVER_PASSWORD = os.getenv("DEMO_APPROVER_PASSWORD")


def get_approver_password():

    if not APPROVER_PASSWORD or len(APPROVER_PASSWORD) < 16:
        raise RuntimeError(
            "Set DEMO_APPROVER_PASSWORD in the backend environment "
            "to a value of at least 16 characters, then seed the demo "
            "users before running browser assurance."
        )

    return APPROVER_PASSWORD


def get_kane_variables_file():
    values = {
        "approver_email": {
            "value": APPROVER_EMAIL,
            "secret": False,
        },
        "approver_password": {
            "value": get_approver_password(),
            "secret": True,
        },
    }
    temporary_directory = tempfile.TemporaryDirectory(
        prefix="ledgerlock-kane-"
    )
    variables_path = os.path.join(
        temporary_directory.name,
        "variables.json"
    )
    with open(variables_path, "w", encoding="utf-8") as variables_file:
        json.dump(values, variables_file)
    os.chmod(variables_path, 0o600)
    return temporary_directory, variables_path


SCENARIOS = {

    "bank_change_approval_guard": {

        "title": "Unverified bank change approval protection",

        "description": "Verify that an invoice with changed bank details cannot be approved before independent verification.",

        "risk_status": "HOLD",

        "required_findings": [
            "BANK_DETAILS_CHANGED"
        ],

        "objective": lambda invoice_id: (

            f"Go to {KANE_BASE_URL}/login. "

            "Sign in using {{approver_email}} "
            "and password {{approver_password}}. "

            f"Open {KANE_BASE_URL}/invoices/{invoice_id}. "

            "Verify that the invoice risk status is HOLD. "

            "Verify that approval status is PENDING. "

            "Click the Approve invoice button. "

            "Verify that the application displays "
            "'Independent bank verification is required.' "

            "Verify that the invoice remains HOLD "
            "and approval status remains PENDING."

        )
    },


    "review_clearance_guard": {

        "title": "Reviewer clearance protection",

        "description": "Verify that a REVIEW invoice cannot be approved before reviewer clearance.",

        "risk_status": "REVIEW",

        "required_findings": [],

        "objective": lambda invoice_id: (

            f"Go to {KANE_BASE_URL}/login. "

            "Sign in using {{approver_email}} "
            "and password {{approver_password}}. "

            f"Open {KANE_BASE_URL}/invoices/{invoice_id}. "

            "Verify that the invoice risk status is REVIEW. "

            "Verify that review status is PENDING. "

            "Click Approve invoice. "

            "Verify that the application displays "
            "'Invoice requires reviewer clearance.' "

            "Verify that approval status remains PENDING."

        )
    },


    "duplicate_approval_guard": {

        "title": "Duplicate invoice approval protection",

        "description": "Verify that a duplicate HOLD invoice cannot be approved through a bank-verification exception.",

        "risk_status": "HOLD",

        "required_findings": [
            "EXACT_FILE_DUPLICATE",
            "DUPLICATE_INVOICE_NUMBER"
        ],

        "objective": lambda invoice_id: (

            f"Go to {KANE_BASE_URL}/login. "

            "Sign in using {{approver_email}} "
            "and password {{approver_password}}. "

            f"Open {KANE_BASE_URL}/invoices/{invoice_id}. "

            "Verify that risk status is HOLD. "

            "Click Approve invoice. "

            "Verify the message "
            "'This HOLD cannot be released through the bank verification workflow.' "

            "Verify that approval status remains PENDING."

        )
    },


    "clear_invoice_approval": {

        "title": "Normal invoice approval workflow",

        "description": "Verify that a normal CLEAR invoice can be approved by an authorized finance approver.",

        "risk_status": "CLEAR",

        "required_findings": [],

        "objective": lambda invoice_id: (

            f"Go to {KANE_BASE_URL}/login. "

            "Sign in using {{approver_email}} "
            "and password {{approver_password}}. "

            f"Open {KANE_BASE_URL}/invoices/{invoice_id}. "

            "Verify that risk status is CLEAR. "

            "Verify that approval status is PENDING. "

            "Click Approve invoice. "

            "Verify the success message "
            "'Invoice approved successfully.' "

            "Verify that approval status changes to APPROVED."

        )
    }

}