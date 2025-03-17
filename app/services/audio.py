from models.audio import MusicSheet
from sqlalchemy.orm import Session    

def get_music_by_id(db: Session, id: int):
    return db.query(MusicSheet).filter(MusicSheet.id == id).first()

def get_all_music(db: Session):
    return db.query(MusicSheet).all()
