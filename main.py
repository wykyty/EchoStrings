from fastapi import FastAPI
from api.audio import router as audio_router

app = FastAPI()

app.include_router(audio_router)

@app.get("/")
async def root():
    return {"message": "Hello, World"}