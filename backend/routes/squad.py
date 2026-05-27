from fastapi import APIRouter, HTTPException
from database import db
from models import SquadCreate, SquadJoin
from datetime import datetime
import uuid

router = APIRouter()


@router.post("/squad/create")
async def create_squad(body: SquadCreate):
    user = await db.users.find_one({"_id": body.user_id})
    if not user:
        raise HTTPException(404, "User not found")
    if user.get("squad_id"):
        raise HTTPException(400, "Already in a squad. Leave first.")

    squad_id = str(uuid.uuid4())[:8].upper()
    squad = {
        "_id":        squad_id,
        "name":       body.name,
        "creator_id": body.user_id,
        "members":    [{"user_id": body.user_id, "name": user.get("name","Player"), "points": user.get("points",0)}],
        "total_points": user.get("points", 0),
        "created_at": datetime.utcnow(),
    }
    await db.squads.insert_one(squad)
    await db.users.update_one({"_id": body.user_id}, {"$set": {"squad_id": squad_id}})
    return {"squad_id": squad_id, "name": body.name}


@router.post("/squad/join")
async def join_squad(body: SquadJoin):
    user  = await db.users.find_one({"_id": body.user_id})
    squad = await db.squads.find_one({"_id": body.squad_id})

    if not user:
        raise HTTPException(404, "User not found")
    if not squad:
        raise HTTPException(404, "Squad not found")
    if len(squad.get("members", [])) >= 50:
        raise HTTPException(400, "Squad is full (max 50)")
    if user.get("squad_id"):
        raise HTTPException(400, "Already in a squad")

    member_entry = {"user_id": body.user_id, "name": user.get("name","Player"), "points": user.get("points",0)}
    await db.squads.update_one(
        {"_id": body.squad_id},
        {"$push": {"members": member_entry},
         "$inc":  {"total_points": user.get("points", 0)}}
    )
    await db.users.update_one({"_id": body.user_id}, {"$set": {"squad_id": body.squad_id}})
    return {"squad_id": body.squad_id}


@router.get("/squad/{squad_id}")
async def get_squad(squad_id: str):
    squad = await db.squads.find_one({"_id": squad_id})
    if not squad:
        raise HTTPException(404, "Squad not found")

    # BUG FIX: total_points is stale (members earn points after joining).
    # Recalculate live from member user_ids for accurate display.
    member_ids = [m["user_id"] for m in squad.get("members", [])]
    if member_ids:
        pipeline = [
            {"$match": {"_id": {"$in": member_ids}}},
            {"$group": {"_id": None, "total": {"$sum": "$points"},
                        "members": {"$push": {"user_id": "$_id", "name": "$name", "points": "$points"}}}}
        ]
        agg = await db.users.aggregate(pipeline).to_list(1)
        if agg:
            squad["total_points"] = agg[0]["total"]
            squad["members"]      = agg[0]["members"]

    squad["_id"] = squad_id
    return squad


@router.get("/squad/leaderboard/top")
async def squad_leaderboard(limit: int = 20):
    cursor = db.squads.find({}, {"name":1,"total_points":1,"members":1}).sort("total_points",-1).limit(limit)
    squads = []
    async for s in cursor:
        squads.append({
            "_id":          s["_id"],
            "name":         s.get("name","Squad"),
            "total_points": s.get("total_points",0),
            "member_count": len(s.get("members",[])),
        })
    return squads
