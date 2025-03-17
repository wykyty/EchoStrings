from pydantic import BaseModel, Field, validator
from fastapi import Form
from datetime import datetime
from fastapi.exceptions import ValidationException


class ActivityCreate(BaseModel):
    title: str # = Field(..., max_length=50, description='活动标题')
    start_time: datetime # = Field(..., description='活动开始时间', example='2025-03-14 12:00')
    end_time: datetime # = Field(..., description='活动结束时间', example='2025-03-15 12:00')
    status: str
    participants: int
    creator_id: int

    @classmethod
    def as_form(
        cls,
        title: str = Form(..., max_length=50, description='活动标题'),
        start_time: datetime = Form(..., description='活动开始时间', example='2025-03-14 12:00', format='YYYY-MM-DD HH:mm'),
        end_time: datetime = Form(..., description='活动结束时间', example='2025-03-15 12:00', format='YYYY-MM-DD HH:mm'),
        status: str = Form("未开始", max_length=10, description='活动状态'),
        participants: int = Form(0, description='参与人数'),
        creator_id: int = Form(..., description='创建者ID')
    ):
        return cls(title=title, start_time=start_time, end_time=end_time, status=status, participants=participants, creator_id=creator_id)
    
    @validator('end_time')
    def validate_time_range(cls, end_time, values):
        if 'start_time' in values and end_time < values['start_time']:
            raise ValidationException(detail='结束时间不能早于开始时间')
        return end_time
    

class WorkCreate(BaseModel):
    title: str
    author_id: int

    @classmethod
    def as_form(
        cls,
        title: str = Form(..., max_length=50, description='作品标题'),
        author_id: int = Form(..., description='作者ID')
    ):
        return cls(title=title, author_id=author_id)
        
