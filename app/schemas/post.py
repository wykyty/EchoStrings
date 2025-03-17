from pydantic import BaseModel, Field
from fastapi import Form
from datetime import datetime

class PostCreate(BaseModel):
    author_name: str
    title: str
    content: str
    # tags: list = Field([], title="List of tags")
    time: datetime
    like_count: int
    comment_count: int

    @classmethod
    def as_form(
        cls, 
        author_name: str = Form(..., min_length=1, max_length=50, description="Author name"), 
        title: str = Form(..., min_length=1, max_length=50, description="Title"), 
        content: str = Form(None, description="Content")
    ):
        return cls(
            author_name=author_name,
            title=title,
            content=content,
            time=datetime.utcnow(),
            like_count=0,
            comment_count=0
        )
