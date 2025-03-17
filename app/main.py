from fastapi import FastAPI, Response
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from routers import audio, ai, user, post, activity
from database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="EchoStrings")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(activity.router)
app.include_router(post.router)
app.include_router(ai.router)
app.include_router(audio.router)
app.include_router(user.router)


@app.get("/")
async def root():
    return {"message": "Welcome to EchoStrings."}

@app.options("/{full_path:path}")
async def preflight(full_path: str, response: Response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
