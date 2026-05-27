from fastapi import APIRouter, HTTPException, Header
from database import db
from models import UserUpdate, BoostRequest
from datetime import datetime
from auth import get_verified_user_id

router = APIRouter()

BOOST_COSTS = [2000, 4000, 8000, 16000, 32000, 64000, 128000, 256000, 512000, 1000000]

# Points update mein allowed fields only — client se arbitrary points set nahi
SAFE_UPDATE_FIELDS = {"energy", "boosts", "level", "taps_per_tap", "max_energy", "energy_recharge_rate"}

def default_user(user_id: str, name: str = "Guest", photo_url: str = "") -> dict:
    return {
        "_id":                user_id,
        "name":               name,
        "photo_url":          photo_url,
        "points":             0,
        "energy":             500,
        "max_energy":         500,
        "taps_per_tap":       1.0,
        "energy_recharge_rate": 1,
        "level":              1,
        "boosts":             {"multitap": 1, "energy_limit": 1, "recharge_speed": 1},
        "completed_tasks":    [],
        "referred_by":        None,
        "referral_count":     0,
        "referral_earnings":  0,
        "daily_streak":       0,
        "last_claim_date":    None,
        "last_spin_date":     None,
        "squad_id":           None,
        "created_at":         datetime.utcnow(),
        "last_seen":          datetime.utcnow(),
    }


@router.get("/user/{user_id}")
async def get_or_create_user(user_id: str, name: str = "Guest", photo_url: str = ""):
    user = await db.users.find_one({"_id": user_id})
    if not user:
        user = default_user(user_id, name, photo_url)
        await db.users.insert_one(user)
    else:
        await db.users.update_one(
            {"_id": user_id},
            {"$set": {
                "name":      name or user["name"],
                "photo_url": photo_url or user["photo_url"],
                "last_seen": datetime.utcnow()
            }}
        )
    user.pop("_id", None)
    user["user_id"] = user_id
    return user


@router.post("/user/{user_id}/update")
async def update_user(
    user_id: str,
    data: UserUpdate,
    x_telegram_init_data: str | None = Header(default=None)
):
    verified_id = get_verified_user_id(x_telegram_init_data)
    if verified_id and verified_id != user_id:
        raise HTTPException(403, "Unauthorized")

    # 'points' field is NOT allowed via client update
    raw = {k: v for k, v in data.dict().items() if v is not None}
    update_dict = {k: v for k, v in raw.items() if k in SAFE_UPDATE_FIELDS}
    update_dict["last_seen"] = datetime.utcnow()

    if not update_dict:
        return {"status": "ok"}

    await db.users.update_one({"_id": user_id}, {"$set": update_dict}, upsert=True)
    return {"status": "ok"}


# ── TAP ENDPOINT ─────────────────────────────────────────────
@router.post("/user/{user_id}/tap")
async def record_tap(
    user_id: str,
    x_telegram_init_data: str | None = Header(default=None)
):
    """
    BUG FIX (tap batch): Frontend batches taps and sends count,
    server multiplies by taps_per_tap to prevent point manipulation.
    """
    verified_id = get_verified_user_id(x_telegram_init_data)
    if verified_id and verified_id != user_id:
        raise HTTPException(403, "Unauthorized")

    user = await db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(404, "User not found")

    taps_per_tap = user.get("taps_per_tap", 1.0)
    points_earned = int(taps_per_tap)

    await db.users.update_one(
        {"_id": user_id},
        {"$inc": {"points": points_earned},
         "$set": {"last_seen": datetime.utcnow()}}
    )
    return {"points_earned": points_earned, "total_points": user.get("points", 0) + points_earned}


@router.post("/user/{user_id}/boost")
async def buy_boost(
    user_id: str,
    body: BoostRequest,
    x_telegram_init_data: str | None = Header(default=None)
):
    verified_id = get_verified_user_id(x_telegram_init_data)
    if verified_id and verified_id != user_id:
        raise HTTPException(403, "Unauthorized")

    user = await db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(404, "User not found")

    boost_type = body.boost_type
    if boost_type not in ["multitap", "energy_limit", "recharge_speed"]:
        raise HTTPException(400, "Invalid boost type")

    current_lvl = user.get("boosts", {}).get(boost_type, 1)
    cost_idx    = min(current_lvl - 1, 9)
    cost        = BOOST_COSTS[cost_idx]

    if user["points"] < cost:
        raise HTTPException(400, f"Not enough points. Need {cost}")

    new_lvl = current_lvl + 1
    update  = {
        f"boosts.{boost_type}": new_lvl,
        "points":    user["points"] - cost,
        "last_seen": datetime.utcnow()
    }

    if boost_type == "multitap":
        update["taps_per_tap"] = 1 + (new_lvl - 1) * 0.5
    elif boost_type == "energy_limit":
        update["max_energy"] = 500 + (new_lvl - 1) * 500
    elif boost_type == "recharge_speed":
        update["energy_recharge_rate"] = new_lvl

    await db.users.update_one({"_id": user_id}, {"$set": update})
    return {"status": "ok", "new_level": new_lvl, "cost": cost}
