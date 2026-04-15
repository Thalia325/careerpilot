import re

from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    username: str
    full_name: str


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=100)
    role: str = Field(default="student", pattern=r"^(student|teacher)$")
    email: str = Field(default="", max_length=120)
    teacher_code: str | None = Field(default=None, max_length=120)

    @field_validator("password")
    @classmethod
    def password_must_contain_letter_and_digit(cls, v: str) -> str:
        if not re.search(r"[a-zA-Z]", v) or not re.search(r"\d", v):
            raise ValueError("密码必须同时包含英文字母和数字")
        return v

    @field_validator("email")
    @classmethod
    def email_format(cls, v: str) -> str:
        email = v.strip()
        if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise ValueError("邮箱格式不正确")
        return email
