# 🌟 GlowTap ($GTAP)

Telegram Mini App clicker game — Neon glow crystal tapping game similar to Notcoin/Hamster Kombat.

---

## 📁 Project Structure

```
glowtap/
├── frontend/          → Deploy to Vercel
│   ├── index.html     (full game UI)
│   └── vercel.json
└── backend/           → Deploy to Railway
    ├── main.py        (FastAPI app)
    ├── bot.py         (Telegram bot)
    ├── database.py    (MongoDB connection)
    ├── models.py      (Pydantic models)
    ├── routes/
    │   ├── user.py
    │   ├── game.py
    │   ├── leaderboard.py
    │   └── squad.py
    ├── requirements.txt
    ├── Procfile
    └── .env.example
```

---

## ✅ Features

- 💎 **Tap to earn** $GTAP points with energy system
- ⚡ **Level system** (20 levels, each boosts tap power)
- 🎰 **Lucky Spin** wheel (daily free spin)
- 🏆 **Leaderboard** (top 50, live rank)
- 📅 **Daily Login Bonus** (streak up to Day 7 = 5000 pts)
- 👥 **Referral System** (2000 pts inviter, 1000 pts invitee)
- 🛡️ **Squad System** (create/join, max 50 members)
- ✅ **Tasks** (channel join, Twitter follow, etc.)
- 🔋 **Boosts** (MultiTap, Energy Limit, Recharge Speed)

---

## 🚀 Deployment Steps

### Step 1 — MongoDB Atlas

1. Go to [mongodb.com/atlas](https://mongodb.com/atlas) → Create free cluster
2. Database name: `glowtap`
3. Collections: `users`, `squads` (auto-created)
4. **Network Access** → Allow `0.0.0.0/0`
5. Copy connection string → your `MONGO_URI`

---

### Step 2 — Telegram Bot Setup

1. Message [@BotFather](https://t.me/botfather) → `/newbot`
2. Name: `GlowTap` | Username: `glowtap_bot` (or your choice)
3. Copy the **Bot Token**
4. Get API_ID and API_HASH from [my.telegram.org](https://my.telegram.org)
5. After deploying frontend:
   - `/mybots` → Select bot → **Bot Settings** → **Menu Button**
   - Set URL to your Vercel URL

---

### Step 3 — Vercel (Frontend)

1. Push `frontend/` folder to GitHub
2. [vercel.com](https://vercel.com) → Import repo
3. **Root Directory** → `frontend`
4. Deploy → Copy URL (e.g. `https://glowtap.vercel.app`)
5. **Update `index.html`**:
   ```js
   const API_BASE = 'https://your-railway-url.up.railway.app';
   const BOT_USERNAME = 'glowtap_bot';
   ```
6. Redeploy

---

### Step 4 — Railway (Backend)

1. [railway.app](https://railway.app) → New Project → Deploy from GitHub
2. **Root Directory** → `backend`
3. Add **Environment Variables**:

| Variable | Value |
|----------|-------|
| `MONGO_URI` | Your MongoDB connection string |
| `BOT_TOKEN` | From BotFather |
| `API_ID` | From my.telegram.org |
| `API_HASH` | From my.telegram.org |
| `FRONTEND_URL` | Your Vercel URL |
| `ADMIN_IDS` | Your Telegram user ID (comma-separated) |

4. Railway auto-detects `Procfile` and runs the API
5. Copy your Railway URL

---

### Step 5 — Run the Bot

The bot runs separately. On Railway, add a second service or run locally:

```bash
cd backend
pip install -r requirements.txt
python bot.py
```

Or on Railway → Add Service → same repo, command: `python bot.py`

---

## 🔑 Two Lines to Change After Deployment

In `frontend/index.html`, find and update:

```js
const API_BASE = 'https://YOUR-RAILWAY-URL.up.railway.app';
const BOT_USERNAME = 'your_actual_bot_username';
```

---

## 🛡️ Security Notes

- The backend validates `X-Telegram-Init-Data` header for Telegram auth
- Rate limiting: add `slowapi` for production tap endpoints
- MongoDB indexes are created automatically on startup
- CORS is open by default — restrict to your Vercel URL in production

---

## 📡 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/user/{id}` | Get or create user |
| POST | `/api/user/{id}/update` | Save game state |
| POST | `/api/user/{id}/boost` | Purchase boost |
| POST | `/api/daily-claim/{id}` | Claim daily bonus |
| POST | `/api/spin/{id}` | Lucky spin |
| POST | `/api/task/complete/{id}` | Complete task |
| POST | `/api/referral/apply` | Apply referral code |
| GET | `/api/referrals/{id}` | Get referral data |
| GET | `/api/leaderboard` | Top 50 players |
| GET | `/api/leaderboard/rank/{id}` | User's rank |
| POST | `/api/squad/create` | Create squad |
| POST | `/api/squad/join` | Join squad |
| GET | `/api/squad/{id}` | Squad info |

---

## 🧪 Local Development

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env   # fill in your values
uvicorn main:app --reload --port 8000

# Frontend — just open in browser
# Set API_BASE = 'http://localhost:8000' in index.html temporarily
```

---

Made with 💙 — GlowTap $GTAP
