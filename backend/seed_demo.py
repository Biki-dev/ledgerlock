from decimal import Decimal

from datetime import date

from database import SessionLocal, Base, engine

from models import Vendor, Invoice, InvoiceItem

from services.vendor_service import normalize_vendor_name


Base.metadata.create_all(bind=engine)


vendors_data = [
    {
        "name": "ABC Industrial Supplies",
        "gstin": "DEMO-GSTIN-001",
        "bank_account": "900000000001",
        "ifsc": "DEMO0000001",
        "product": "Steel Rod",
        "price": Decimal("100.00"),
    },
    {
        "name": "Northstar Components",
        "gstin": "DEMO-GSTIN-002",
        "bank_account": "900000000002",
        "ifsc": "DEMO0000002",
        "product": "Copper Wire",
        "price": Decimal("200.00"),
    },
    {
        "name": "Brahmaputra Stationers",
        "gstin": "DEMO-GSTIN-003",
        "bank_account": "900000000003",
        "ifsc": "DEMO0000003",
        "product": "Bearing",
        "price": Decimal("500.00"),
    }
]


db = SessionLocal()

try:

    for data in vendors_data:

        vendor = db.query(Vendor).filter(
            Vendor.gstin == data["gstin"]
        ).first()

        if vendor:
            continue

        vendor = Vendor(

            name=data["name"],

            normalized_name=normalize_vendor_name(
                data["name"]
            ),

            gstin=data["gstin"],

            bank_account=data["bank_account"],

            ifsc=data["ifsc"],

            is_verified=True
        )

        db.add(vendor)

        db.flush()

        # Generate three historical invoices per vendor.

        for i in range(1, 4):

            quantity = Decimal("10")

            unit_price = data["price"] + Decimal(i - 1)

            subtotal = quantity * unit_price

            tax = subtotal * Decimal("0.18")

            total = subtotal + tax

            invoice = Invoice(

                vendor_id=vendor.id,

                vendor_name=vendor.name,

                invoice_number=f"HIST-{vendor.id}-{i}",

                invoice_date=date(2026, 8 + i, 10),

                gstin=vendor.gstin,

                bank_account=vendor.bank_account,

                ifsc=vendor.ifsc,

                subtotal=subtotal,

                tax=tax,

                total=total,

                source_filename=f"historical_{vendor.id}_{i}.pdf",

                storage_path="",

                sha256=f"seed-{vendor.id}-{i}",

                extraction_method="SEED",

                extraction_status="EXTRACTED",

                extraction_confidence=1.0,

                raw_text="Synthetic historical invoice"
            )

            db.add(invoice)

            db.flush()

            item = InvoiceItem(

                invoice_id=invoice.id,

                description=data["product"],

                quantity=quantity,

                unit_price=unit_price,

                line_total=subtotal
            )

            db.add(item)

    db.commit()

    print("Demo vendors and invoice history created.")

finally:

    db.close()