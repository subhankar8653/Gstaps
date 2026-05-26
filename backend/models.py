from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class Boosts(BaseModel):
    multitap: int = 1
    energy_limit: int = 1
    recharge_speed: int = 1

class UserUpdate(BaseModel):
    points: Optional[int]         = None
    energy: Optional[int]         = None
    max_energy: Optional[int]     = None
    taps_per_tap: Optional[float] = None
    energy_recharge_rate: Optional[int] = None
    level: Optional[int]          = None
    boosts: Optional[dict]        = None

class BoostRequest(BaseModel):
    boost_type: str  # multitap | energy_limit | recharge_speed

class TaskComplete(BaseModel):
    task_id: str

class ReferralApply(BaseModel):
    user_id: str
    referrer_id: str

class SquadCreate(BaseModel):
    user_id: str
    name: str

class SquadJoin(BaseModel):
    user_id: str
    squad_id: str
