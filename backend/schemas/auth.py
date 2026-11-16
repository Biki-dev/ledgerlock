from pydantic import BaseModel, Field


class LoginRequest(BaseModel):

    email: str

    password: str = Field(
        min_length=8,
        max_length=128
    )


class UserOut(BaseModel):

    id: int

    full_name: str

    email: str

    role: str


class LoginResponse(BaseModel):

    access_token: str

    token_type: str = "bearer"

    user: UserOut