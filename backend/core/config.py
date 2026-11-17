import os


DEFAULT_FRONTEND_ORIGINS = (
    "http://localhost:5173,http://127.0.0.1:5173"
)


def get_frontend_origins(value: str | None = None) -> list[str]:
    configured = value if value is not None else os.getenv(
        "FRONTEND_ORIGINS",
        DEFAULT_FRONTEND_ORIGINS
    )
    return [origin.strip() for origin in configured.split(",") if origin.strip()]
