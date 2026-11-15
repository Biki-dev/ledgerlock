from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine

# Import models so SQLAlchemy registers all tables.
from models import Vendor, Invoice, InvoiceItem

from routes.invoices import router as invoice_router


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="LedgerLock API",
    description="AI Invoice Intelligence and Payment Security",
    version="1.0.0"
)


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


app.include_router(invoice_router)