from pydantic import BaseModel, Field
from fastapi import Form

class UserCreate(BaseModel):
    username: str
    password: str
    level: int

    @classmethod
    def as_form(
        cls,
        username: str = Form(..., min_length=1, max_length=50, description="Username, 1-50位"),
        password: str = Form(..., min_length=6, max_length=50, description="Password, 最短6位"),
        level: int = Form(..., ge=0, le=100, description="Level, 0-100")
    ):
        return cls(username=username, password=password, level=level)

