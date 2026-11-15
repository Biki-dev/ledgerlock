import re

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from models.vendor import Vendor


def normalize_vendor_name(name: str):

    return " ".join(
        re.findall(
            r"[a-z0-9]+",
            name.lower()
        )
    )


def resolve_vendor(
    db: Session,
    vendor_name: str | None,
    gstin: str | None
):

    vendor = None

    if gstin:

        vendor = db.scalar(
            select(Vendor).where(
                func.upper(Vendor.gstin) == gstin.upper()
            )
        )

    elif vendor_name:

        normalized = normalize_vendor_name(vendor_name)

        vendor = db.scalar(
            select(Vendor).where(
                Vendor.normalized_name == normalized
            ).limit(1)
        )

    if vendor:
        return vendor

    if not vendor_name:
        return None

    new_vendor = Vendor(
        name=vendor_name,
        normalized_name=normalize_vendor_name(vendor_name),
        gstin=gstin,
        bank_account=None,
        ifsc=None,
        is_verified=False
    )

    db.add(new_vendor)
    db.flush()

    return new_vendor