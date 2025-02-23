from fastapi import FastAPI
import uvicorn
from .api.audio import router as audio_router

app = FastAPI(title="EchoStrings")

app.include_router(audio_router)

@app.get("/")
async def root():
    return {"message": "Hello, World"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
