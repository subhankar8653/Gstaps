from fastapi import APIRouter, HTTPException
from database import db
from models import TaskComplete, ReferralApply
from datetime import datetime, date
import random

router = APIRouter()

DAILY_REWARDS   = [500, 1000, 2000, 3000, 3500, 4000, 5000]
SPIN_SEGMENTS   = [100, 500, 1000, 2500, 0, 5000, 200, 750]
SPIN_WEIGHTS    = [20,  15,   12,    8,  15,   3,  17,  10]  # probability weights

TASK_REWARDS = {
    "tg_join":  2000,
    "tg_share": 1000,
    "twitter":  1500,
    "invite3":  5000,
    "play7":    8000,
}


# ── DAILY CLAIM ──────────────────────────────────────────────
@router.post("/daily-claim/{user_id}")
async def daily_claim(user_id: str):
    user = await db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(404, "User not found")

    today_str = date.today().isoformat()
    if user.get("last_claim_date") == today_str:
        raise HTTPException(400, "Already claimed today")

    # Calculate streak
    streak = user.get("daily_streak", 0)
    last   = user.get("last_claim_date")
    if last:
        try:
            last_date = date.fromisoformat(last)
            delta     = (date.today() - last_date).days
            streak    = streak + 1 if delta == 1 else 1
        except Exception:
            streak = 1
    else:
        streak = 1

    day_idx      = min(streak - 1, 6)
    points_earned = DAILY_REWARDS[day_idx]

    await db.users.update_one(
        {"_id": user_id},
        {"$set": {
            "last_claim_date": today_str,
            "daily_streak":    streak,
            "last_seen":       datetime.utcnow(),
        },
         "$inc": {"points": points_earned}}
    )
    return {"points_earned": points_earned, "streak": streak, "day": streak}


# ── LUCKY SPIN ───────────────────────────────────────────────
@router.post("/spin/{user_id}")
async def lucky_spin(user_id: str):
    user = await db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(404, "User not found")

    today_str = date.today().isoformat()
    if user.get("last_spin_date") == today_str:
        raise HTTPException(400, "Already spun today")

    reward = random.choices(SPIN_SEGMENTS, weights=SPIN_WEIGHTS, k=1)[0]

    update = {"$set": {"last_spin_date": today_str, "last_seen": datetime.utcnow()}}
    if reward > 0:
        update["$inc"] = {"points": reward}

    await db.users.update_one({"_id": user_id}, update)
    return {"reward": reward}


# ── TASK COMPLETE ─────────────────────────────────────────────
@router.post("/task/complete/{user_id}")
async def complete_task(user_id: str, body: TaskComplete):
    user = await db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(404, "User not found")

    task_id = body.task_id
    if task_id in (user.get("completed_tasks") or []):
        raise HTTPException(400, "Task already completed")

    reward = TASK_REWARDS.get(task_id, 0)
    if reward == 0:
        raise HTTPException(400, "Unknown task")

    await db.users.update_one(
        {"_id": user_id},
        {"$inc": {"points": reward},
         "$push": {"completed_tasks": task_id},
         "$set":  {"last_seen": datetime.utcnow()}}
    )
    return {"points_earned": reward, "task_id": task_id}


# ── REFERRAL APPLY ────────────────────────────────────────────
@router.post("/referral/apply")
async def apply_referral(body: ReferralApply):
    user_id     = body.user_id
    referrer_id = body.referrer_id

    if user_id == referrer_id:
        raise HTTPException(400, "Cannot refer yourself")

    user = await db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(404, "User not found")

    if user.get("referred_by"):
        raise HTTPException(400, "Already referred")

    referrer = await db.users.find_one({"_id": referrer_id})
    if not referrer:
        raise HTTPException(404, "Referrer not found")

    # Give rewards
    await db.users.update_one(
        {"_id": user_id},
        {"$set":  {"referred_by": referrer_id},
         "$inc":  {"points": 1000}}  # invitee bonus
    )
    await db.users.update_one(
        {"_id": referrer_id},
        {"$inc": {"points": 2000, "referral_count": 1, "referral_earnings": 2000}}
    )
    return {"status": "ok", "invitee_bonus": 1000, "inviter_bonus": 2000}


# ── GET REFERRALS ─────────────────────────────────────────────
@router.get("/referrals/{user_id}")
async def get_referrals(user_id: str):
    user = await db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(404, "User not found")

    # Get list of friends who used this user as referrer
    cursor  = db.users.find({"referred_by": user_id}, {"name": 1, "points": 1, "_id": 1})
    friends = []
    async for f in cursor:
        friends.append({"name": f.get("name", "Player"), "points": f.get("points", 0)})

    return {
        "referral_count":    user.get("referral_count", 0),
        "referral_earnings": user.get("referral_earnings", 0),
        "friends":           friends
    }
