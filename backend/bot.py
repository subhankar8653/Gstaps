import asyncio
import os
import httpx
from pyrogram import Client, filters, enums
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
    Message,
)
from dotenv import load_dotenv

load_dotenv()

API_BASE   = os.getenv("API_BASE", "https://gstaps-production.up.railway.app")
WEBAPP_URL = os.getenv("FRONTEND_URL", "https://gstaps.vercel.app")
ADMIN_IDS  = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

bot = Client(
    "glowtap_bot",
    api_id=os.getenv("API_ID"),
    api_hash=os.getenv("API_HASH"),
    bot_token=os.getenv("BOT_TOKEN"),
)

def play_keyboard(url: str = WEBAPP_URL) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🎮 Play GlowTap", web_app=WebAppInfo(url=url))
    ]])


@bot.on_message(filters.command("start"))
async def start_cmd(client: Client, message: Message):
    user    = message.from_user
    user_id = str(user.id)
    name    = user.first_name + (" " + user.last_name if user.last_name else "")

    # Handle referral
    if len(message.command) > 1:
        referral_code = message.command[1]
        if referral_code != user_id:
            try:
                async with httpx.AsyncClient() as c:
                    await c.post(f"{API_BASE}/api/referral/apply",
                                 json={"user_id": user_id, "referrer_id": referral_code},
                                 timeout=5)
            except Exception:
                pass

    # Ensure user exists in DB
    try:
        async with httpx.AsyncClient() as c:
            await c.get(f"{API_BASE}/api/user/{user_id}",
                        params={"name": name, "photo_url": ""},
                        timeout=5)
    except Exception:
        pass

    welcome = (
        f"✨ **Welcome to GlowTap, {user.first_name}!**\n\n"
        "💎 Tap the glowing crystal to earn **$GTAP** tokens!\n"
        "🎰 Spin the Lucky Wheel daily for bonus points!\n"
        "👥 Invite friends and earn **2000 pts** per referral!\n"
        "🏆 Climb the leaderboard and dominate the rankings!\n\n"
        "**Tap below to start your journey ⬇️**"
    )

    await message.reply(
        welcome,
        reply_markup=play_keyboard(),
        parse_mode=enums.ParseMode.MARKDOWN,
    )


@bot.on_message(filters.command("stats"))
async def stats_cmd(client: Client, message: Message):
    user_id = str(message.from_user.id)
    try:
        async with httpx.AsyncClient() as c:
            res       = await c.get(f"{API_BASE}/api/user/{user_id}", timeout=5)
            data      = res.json()
            rank_res  = await c.get(f"{API_BASE}/api/leaderboard/rank/{user_id}", timeout=5)
            rank_data = rank_res.json()

        text = (
            f"📊 **Your GlowTap Stats**\n\n"
            f"💎 Points: **{data.get('points', 0):,}**\n"
            f"⚡ Level:  **{data.get('level', 1)}**\n"
            f"🏆 Rank:   **#{rank_data.get('rank', '—')}**\n"
            f"👥 Refs:   **{data.get('referral_count', 0)}**\n"
            f"🔥 Streak: **{data.get('daily_streak', 0)} days**"
        )
    except Exception:
        text = "⚠️ Could not fetch stats. Try again later."

    await message.reply(text, reply_markup=play_keyboard(), parse_mode=enums.ParseMode.MARKDOWN)


@bot.on_message(filters.command("broadcast") & filters.user(ADMIN_IDS))
async def broadcast_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply("Usage: /broadcast <message text>")
        return

    text = " ".join(message.command[1:])
    sent = fail = 0

    try:
        async with httpx.AsyncClient() as c:
            res   = await c.get(f"{API_BASE}/api/leaderboard?limit=10000", timeout=10)
            users = res.json()
    except Exception:
        await message.reply("❌ Could not fetch user list")
        return

    await message.reply(f"📢 Broadcasting to {len(users)} users...")
    for u in users:
        try:
            await client.send_message(
                int(u["_id"]),
                f"📢 **GlowTap Announcement**\n\n{text}",
                reply_markup=play_keyboard(),
                parse_mode=enums.ParseMode.MARKDOWN,
            )
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            fail += 1

    await message.reply(f"✅ Broadcast done! Sent: {sent} | Failed: {fail}")


@bot.on_message(filters.command("help"))
async def help_cmd(client: Client, message: Message):
    await message.reply(
        "🎮 **GlowTap Commands**\n\n"
        "/start — Open the game\n"
        "/stats — View your stats\n"
        "/help  — Show this message\n\n"
        "Tap below to play! ⬇️",
        reply_markup=play_keyboard(),
        parse_mode=enums.ParseMode.MARKDOWN,
    )


if __name__ == "__main__":
    print("🤖 GlowTap Bot starting...")
    bot.run()
