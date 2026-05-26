from fastapi import APIRouter
from database import db

router = APIRouter()


@router.get("/leaderboard")
async def get_leaderboard(limit: int = 50):
    cursor = db.users.find(
        {},
        {"name": 1, "points": 1, "level": 1, "photo_url": 1, "_id": 1}
    ).sort("points", -1).limit(limit)

    players = []
    async for p in cursor:
        players.append({
            "_id":       p["_id"],
            "name":      p.get("name", "Player"),
            "points":    p.get("points", 0),
            "level":     p.get("level", 1),
            "photo_url": p.get("photo_url", ""),
        })
    return players


@router.get("/leaderboard/rank/{user_id}")
async def get_user_rank(user_id: str):
    user = await db.users.find_one({"_id": user_id})
    if not user:
        return {"rank": None}

    pts  = user.get("points", 0)
    rank = await db.users.count_documents({"points": {"$gt": pts}}) + 1
    return {"rank": rank, "points": pts}
