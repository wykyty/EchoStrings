from fastapi import FastAPI
import uvicorn
from api.audio import router as audio_router
from api.ai import router as ai_router

app = FastAPI(title="EchoStrings")

app.include_router(audio_router)
app.include_router(ai_router)

@app.get("/")
async def root():
    return {"message": "Welcome to EchoStrings."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
