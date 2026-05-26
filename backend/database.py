import motor.motor_asyncio
import os
from dotenv import load_dotenv

load_dotenv()

client = None
db     = None

async def connect_db():
    global client, db
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
    db     = client["glowtap"]
    # Create indexes for performance
    await db.users.create_index("points")
    await db.squads.create_index("total_points")
    print("✅ MongoDB connected")
