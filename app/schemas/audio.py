from pydantic import BaseModel

class MusicSheetRequest(BaseModel):
    author_id: int
    title: str
    content: str
    base64_data: str

class MusicSheetCreate(BaseModel):
    title: str
    content: str   
    audio_file_path: str | None = None

class MusicSheetResponse(MusicSheetCreate):
    id: int
        