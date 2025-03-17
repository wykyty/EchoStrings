from sqlalchemy import Column, Integer, String, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from database import Base

class MusicSheet(Base):
    __tablename__ = 'music_sheet'
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    title = Column(String(50), nullable=False, unique=True, index=True)
    content = Column(Text)
    duration = Column(Float)  # 音乐时长
    audio_file_path = Column(String(225))

    author_id = Column(Integer, ForeignKey('users.id'))
