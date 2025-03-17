from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
from models.user import User

class Post(Base):
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(50), index=True, nullable=False, unique=True)
    content = Column(Text, nullable=True)

    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    time = Column(DateTime, default=datetime.utcnow)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    file_list = Column(JSON, nullable=True)

    author = relationship('User', backref='posts')
    comments = relationship('Comment', backref='posts', lazy='dynamic')


class Comment(Base):
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    post_id = Column(Integer, ForeignKey('posts.id'), nullable=False)
    time = Column(DateTime, default=datetime.utcnow)

    author = relationship('User', backref='comments')