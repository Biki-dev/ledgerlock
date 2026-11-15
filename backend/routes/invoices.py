import hashlib
import uuid

from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile
)

from fastapi.responses import FileResponse

from sqlalchemy.orm import Session
from sqlalchemy import select

from database import get_db

from models.invoice import Invoice, InvoiceItem

from schemas.invoice import InvoiceOut , InvoiceRiskOut

from services.pdf_extractor import extract_pdf_text
from services.invoice_parser import parse_invoice_text
from services.vendor_service import resolve_vendor
from services.fraud_engine import run_fraud_analysis

router = APIRouter(
    prefix="/api/invoices",
    tags=["Invoices"]
)

BASE_DIR = Path(__file__).resolve().parents[1]

STORAGE_DIR = BASE_DIR / "storage" / "invoices"

STORAGE_DIR.mkdir(
    parents=True,
    exist_ok=True
)

MAX_UPLOAD_SIZE = 10 * 1024 * 1024


@router.post(
    "/{invoice_id}/analyze",
    response_model=InvoiceOut
)
def analyze_invoice_endpoint(
    invoice_id: int,
    db: Session = Depends(get_db)
):

    invoice = db.get(Invoice, invoice_id)

    if not invoice:

        raise HTTPException(
            status_code=404,
            detail="Invoice not found"
        )

    try:

        run_fraud_analysis(db, invoice)

        db.commit()

        db.refresh(invoice)

        return invoice

    except Exception:

        db.rollback()

        raise


@router.get(
    "/{invoice_id}/risk",
    response_model=InvoiceRiskOut
)
def get_invoice_risk(
    invoice_id: int,
    db: Session = Depends(get_db)
):

    invoice = db.get(Invoice, invoice_id)

    if not invoice:

        raise HTTPException(
            status_code=404,
            detail="Invoice not found"
        )

    return {
        "invoice_id": invoice.id,
        "risk_status": invoice.risk_status,
        "risk_score": invoice.risk_score,
        "findings": invoice.risk_findings
    }


@router.post(
    "/upload",
    response_model=InvoiceOut,
    status_code=201
)
async def upload_invoice(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    # 1. Extension validation

    original_filename = file.filename or "invoice.pdf"

    if not original_filename.lower().endswith(".pdf"):

        raise HTTPException(
            status_code=415,
            detail="Only PDF files are supported"
        )

    # 2. Read file with size limit

    content = await file.read(MAX_UPLOAD_SIZE + 1)

    if len(content) > MAX_UPLOAD_SIZE:

        raise HTTPException(
            status_code=413,
            detail="Maximum upload size is 10 MB"
        )

    # 3. Validate actual PDF signature

    if not content.startswith(b"%PDF-"):

        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file"
        )

    # 4. Extract PDF text

    try:

        result = extract_pdf_text(content)

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    # 5. Parse invoice fields

    parsed = parse_invoice_text(result.text)

    # 6. Resolve vendor

    vendor = resolve_vendor(
        db,
        parsed["vendor_name"],
        parsed["gstin"]
    )

    # 7. Calculate extraction status

    required_fields = [
        parsed["vendor_name"],
        parsed["invoice_number"],
        parsed["total"]
    ]

    extraction_status = (
        "EXTRACTED"
        if all(value is not None for value in required_fields)
        else "NEEDS_REVIEW"
    )

    # 8. Generate unique storage filename

    stored_filename = f"{uuid.uuid4().hex}.pdf"

    storage_path = STORAGE_DIR / stored_filename

    # 9. Generate SHA256

    sha256 = hashlib.sha256(content).hexdigest()

    # 10. Save PDF

    storage_path.write_bytes(content)

    try:

        # 11. Create invoice record

        invoice = Invoice(

            vendor_id=vendor.id if vendor else None,

            vendor_name=parsed["vendor_name"],

            invoice_number=parsed["invoice_number"],

            invoice_date=parsed["invoice_date"],

            gstin=parsed["gstin"],

            bank_account=parsed["bank_account"],

            ifsc=parsed["ifsc"],

            subtotal=parsed["subtotal"],

            tax=parsed["tax"],

            total=parsed["total"],

            source_filename=original_filename[:255],

            storage_path=str(storage_path),

            sha256=sha256,

            extraction_method=result.method,

            extraction_status=extraction_status,

            extraction_confidence=parsed["extraction_confidence"],

            field_confidence=parsed["field_confidence"],

            extraction_warning=result.warning,

            raw_text=result.text
        )

        db.add(invoice)

        db.flush()

        # 12. Save extracted line items

        for item in parsed["items"]:

            invoice_item = InvoiceItem(

                invoice_id=invoice.id,

                description=item["description"],

                quantity=item["quantity"],

                unit_price=item["unit_price"],

                line_total=item["line_total"]
            )

            db.add(invoice_item)

        # 13. Commit transaction


        db.flush()

        # Run Phase 2 fraud analysis.

        run_fraud_analysis(db, invoice)

        # Save invoice + findings together.

        db.commit()

        db.refresh(invoice)

        return invoice

    except Exception:

        db.rollback()

        storage_path.unlink(missing_ok=True)

        raise

@router.get(
    "",
    response_model=list[InvoiceOut]
)
def get_invoices(
    db: Session = Depends(get_db)
):

    invoices = db.scalars(
        select(Invoice)
        .order_by(Invoice.uploaded_at.desc())
        .limit(100)
    ).all()

    return invoices


@router.get(
    "/{invoice_id}",
    response_model=InvoiceOut
)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db)
):

    invoice = db.get(Invoice, invoice_id)

    if not invoice:

        raise HTTPException(
            status_code=404,
            detail="Invoice not found"
        )

    return invoice


@router.get("/{invoice_id}/source")
def download_invoice(
    invoice_id: int,
    db: Session = Depends(get_db)
):

    invoice = db.get(Invoice, invoice_id)

    if not invoice:
        raise HTTPException(404, "Invoice not found")

    path = Path(invoice.storage_path)

    if not path.is_file():
        raise HTTPException(404, "PDF file not found")

    return FileResponse(
        path=path,
        media_type="application/pdf",
        filename=invoice.source_filename
    )