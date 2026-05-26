from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import connect_db
from routes import user, game, leaderboard, squad
import os

app = FastAPI(title="GlowTap API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your Vercel URL in production
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await connect_db()

app.include_router(user.router, prefix="/api")
app.include_router(game.router, prefix="/api")
app.include_router(leaderboard.router, prefix="/api")
app.include_router(squad.router, prefix="/api")

@app.get("/")
async def root():
    return {"status": "GlowTap API Running 🚀", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"ok": True}
