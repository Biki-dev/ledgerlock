import jwt

from fastapi import (
    Depends,
    HTTPException,
    status
)

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from sqlalchemy.orm import Session

from database import get_db

from models.user import User

from core.security import decode_access_token


bearer = HTTPBearer(auto_error=False)


def get_current_user(

    credentials: HTTPAuthorizationCredentials | None =
        Depends(bearer),

    db: Session = Depends(get_db)

):

    if not credentials:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:

        payload = decode_access_token(
            credentials.credentials
        )

        user_id = int(payload["sub"])

    except (jwt.InvalidTokenError, ValueError, KeyError):

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired authentication token"
        )

    user = db.get(User, user_id)

    if not user or not user.is_active:

        raise HTTPException(
            status_code=401,
            detail="Inactive or unknown user"
        )

    return user


def require_roles(*allowed_roles):

    def role_dependency(
        current_user: User = Depends(get_current_user)
    ):

        if current_user.role not in allowed_roles:

            raise HTTPException(
                status_code=403,
                detail="You do not have permission for this action"
            )

        return current_user

    return role_dependency