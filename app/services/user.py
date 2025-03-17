from models.user import User
from sqlalchemy.orm import Session

def get_user_by_id(db: Session, user_id):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, user):
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def update_user(db: Session, user):
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user_id):
    user = db.query(User).filter(User.id == user_id).first()
    db.delete(user)
    db.commit()
    return user