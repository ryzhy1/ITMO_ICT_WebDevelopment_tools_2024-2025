from sqlmodel import SQLModel
from pydantic import EmailStr, field_validator
from pydantic_core.core_schema import ValidationInfo

class UserLogin(SQLModel):
    username: str
    password: str

    @field_validator("username", "password")
    @classmethod
    def check_not_empty(cls, value: str, info: ValidationInfo) -> str:
        if not value.strip():
            raise ValueError(f"{info.field_name} cannot be empty or contain only whitespace")
        return value.strip()

class UserCreate(SQLModel):
    username: str
    email: EmailStr
    password: str

    @field_validator("username", "password")
    @classmethod
    def check_not_empty(cls, value: str, info: ValidationInfo) -> str:
        if not value.strip():
            raise ValueError(f"{info.field_name} cannot be empty or contain only whitespace")
        return value.strip()

    @field_validator("username")
    @classmethod
    def check_username_length(cls, value: str) -> str:
        if len(value) < 3:
            raise ValueError("Username must be at least 3 characters long")
        return value

    @field_validator("password")
    @classmethod
    def check_password_length(cls, value: str) -> str:
        if len(value) < 6:
            raise ValueError("Password must be at least 6 characters long")
        return value

class UserChangePassword(SQLModel):
    old_password: str
    new_password: str

    @field_validator("old_password", "new_password")
    @classmethod
    def check_not_empty(cls, value: str, info: ValidationInfo) -> str:
        if not value.strip():
            raise ValueError(f"{info.field_name} cannot be empty or contain only whitespace")
        return value.strip()

    @field_validator("new_password")
    @classmethod
    def check_password_length(cls, value: str) -> str:
        if len(value) < 6:
            raise ValueError("New password must be at least 6 characters long")
        return value