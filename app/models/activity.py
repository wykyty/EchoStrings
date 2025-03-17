from sqlalchemy import Column, Integer, String, ForeignKey, Text, JSON, DateTime, Float
from sqlalchemy.orm import relationship
from database import Base

# 活动模型
class Activity(Base):
    __tablename__ = "activity"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(50), nullable=False, unique=True, index=True)  # 活动标题
    start_time = Column(DateTime, nullable=False, comment="活动开始时间") 
    end_time = Column(DateTime, nullable=False, comment="活动结束时间")
    status = Column(String(10), nullable=False)  # 状态
    participants = Column(Integer, nullable=False)  # 参与人数
    
    cover_url = Column(String(255), nullable=False)  # 封面图片
    intro_url = Column(String(255), nullable=True)  # 简介文件路径

    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    hotworks = relationship("Work", back_populates="activity")

# 作品模型
class Work(Base):
    __tablename__ = "works"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(50), nullable=False, unique=True, index=True)
    # duration = Column(Float, nullable=False)  # 时长
    author = Column(String(50), nullable=False)  # 作者
    content_url = Column(String(255), nullable=False)  # 内容文件

    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    activity_id = Column(Integer, ForeignKey("activity.id"), nullable=False)
    activity = relationship("Activity", back_populates="hotworks")

    