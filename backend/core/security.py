import os

from datetime import datetime, timedelta, timezone

import jwt

from dotenv import load_dotenv

from pwdlib import PasswordHash


load_dotenv()


SECRET_KEY = os.getenv("JWT_SECRET_KEY")

ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

TOKEN_EXPIRE_MINUTES = int(
    os.getenv("JWT_EXPIRE_MINUTES", "60")
)

if not SECRET_KEY or len(SECRET_KEY) < 32:
    raise RuntimeError(
        "JWT_SECRET_KEY must be configured with at least 32 characters."
    )

password_hasher = PasswordHash.recommended()


def hash_password(password: str):

    return password_hasher.hash(password)


def verify_password(password: str, hashed: str):

    return password_hasher.verify(
        password,
        hashed
    )


def create_access_token(user_id: int):

    expires = (
        datetime.now(timezone.utc)
        + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    )

    payload = {
        "sub": str(user_id),
        "exp": expires
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def decode_access_token(token: str):

    return jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM]
    )