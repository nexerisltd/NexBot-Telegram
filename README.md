# NexBot — Telegram Multi-Group Bot

A multi-purpose Telegram bot you can add to many groups. Every group gets its own independent settings (welcome message, moderation rules, custom commands, etc.) stored in a database — nothing is hardcoded to one group.

## Features

- 👋 **Greetings** — customizable welcome message, image, buttons, placeholders (`{first_name}`, `{chat_name}`, etc.), auto-delete after N seconds
- 🛡 **Moderation** — `/warn` `/unwarn` `/warnings`, `/mute` `/unmute`, `/kick`, `/ban` `/unban`, `/purge`, plus automatic anti-flood (spam) protection
- 🤖 **Captcha / join verification** — new members must tap a button within a time limit or they're removed
- ⚙️ **Custom commands** — `/addcmd`, `/delcmd`, `/commands`
- 📅 **Scheduled announcements** — `/announce`, `/announcements`, `/unannounce`
- 📊 **Stats** — `/stats` (daily + 7-day message and join counts)
- 📢 **Broadcast** — `/broadcast` (bot owner only, sends to every group the bot is in)
- ⚙️ **Interactive `/settings` panel** — inline-keyboard admin UI for greetings, welcome media, moderation toggles, and general info
- 🆘 **`/help`** — shows commands available to your role (regular user vs. group admin)
- `/info` — user + chat info

Every command that changes a group's settings re-checks that the caller is a **live** Telegram admin of that group — nothing is trusted from the database alone.

## Local setup (Windows)

1. Extract this zip into `C:\Users\arabi\telegram-bot`
2. Open PowerShell in that folder:
   ```powershell
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Open `.env` and paste your real BotFather token:
   ```
   BOT_TOKEN=your_real_token_here
   ```
   Also set `OWNER_ID` to your own numeric Telegram user ID if you want to use `/broadcast` (message @userinfobot to get your ID).
4. Run the bot:
   ```powershell
   python main.py
   ```
   With no `WEBHOOK_URL` set, it runs in **polling mode** — perfect for local development.

## Running 24/7 (deployment)

Two things changed on most hosts in 2025–2026 that are worth knowing before you deploy:

1. **Render's free "background worker" tier no longer exists** — background workers now start at $7/month. The only free compute is a **free web service**, which spins down after ~15 minutes of no incoming HTTP traffic.
2. A polling bot never receives HTTP traffic, so on a free web service it would spin down and stop polling. The fix built into this project: **webhook mode**. Telegram pushes updates to your service's URL instead of the bot constantly asking Telegram for them — so the free web service only needs to wake up when someone actually messages the bot (a few seconds' cold-start delay after idle periods, which is fine for a welcome/moderation bot).
3. **Free-tier SQLite is not persistent** — Render's free web service disk is wiped on every restart/redeploy. For a bot you actually care about, use a real free Postgres database instead of the default SQLite file.

### Recommended free-cost setup: Render (compute) + Supabase (database)

**Step 1 — Free Postgres on Supabase**
1. Go to supabase.com → New Project (free tier, 500 MB, doesn't expire).
2. Project Settings → Database → copy the "Connection string" (URI, with the password filled in).
3. Turn it into this format for `.env`:
   ```
   DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@YOUR_HOST:5432/postgres
   ```
   (Same string Supabase gives you, just with `postgresql+asyncpg://` at the front instead of `postgresql://`.)

**Step 2 — Deploy to Render**
1. Push this project to a GitHub repo (make sure `.env` is **not** committed — it's already in `.gitignore`).
2. In the Render dashboard: New + → Blueprint → point it at your repo. Render will read `render.yaml` (included in this project) and create a free web service automatically.
3. In the service's Environment tab, set:
   - `BOT_TOKEN` — your real token
   - `OWNER_ID` — your Telegram user ID
   - `DATABASE_URL` — the Supabase string from Step 1
   - `WEBHOOK_URL` — leave blank for the very first deploy, then after Render gives you a URL like `https://nexbot-telegram.onrender.com`, set `WEBHOOK_URL` to that exact URL and redeploy.
4. Once redeployed, send `/start` to your bot in Telegram — it should reply "Bot is alive! ✅" (allow a few seconds if the service had gone idle).

**Cost:** $0/month as long as you stay within Render's free instance hours (750/month — enough for one always-on-ish service) and Supabase's free 500 MB.

### Alternatives
- **Railway / Fly.io**: both moved away from meaningful free ongoing compute in 2025–2026 (Railway free tier is now trial credit only; Fly.io is pure pay-as-you-go with only a 2-hour/7-day trial). They still work well and are cheap (a few dollars/month), just no longer genuinely free 24/7.
- **Your own VPS**: run `python main.py` inside `tmux`/`screen`, or better, as a `systemd` service so it restarts on crash/reboot. Leave `WEBHOOK_URL` empty to keep using simple polling mode — no port or webhook setup needed on a VPS you control.

## Project structure

```
bot/
├── database/        # SQLAlchemy models (chats, warnings, custom commands, scheduled messages, captchas, stats...) + async DB connection
├── services/         # DB access layer, one file per feature area
├── features/
│   ├── greetings/     # welcome message handler (new_chat_members, buttons, media, auto-delete)
│   ├── info/           # /info command
│   ├── help/            # /help command
│   ├── settings/         # interactive admin settings panel
│   ├── moderation/        # /warn /mute /kick /ban /purge + anti-flood
│   ├── captcha/             # join verification
│   ├── customcommands/       # /addcmd /delcmd + dispatch
│   ├── scheduler/              # /announce + periodic dispatch job
│   ├── stats/                    # /stats + passive message counter
│   └── broadcast/                  # /broadcast (owner only)
├── keyboards/        # inline keyboard layouts
└── utils/             # placeholders, duration parsing
main.py                 # entry point — registers everything, chooses polling vs. webhook
render.yaml, Procfile     # Render deployment config
```

## Security notes

- `.env` is in `.gitignore` — never commit it or paste its contents anywhere.
- If a bot token is ever exposed, revoke and regenerate it immediately via BotFather.
- `/broadcast` only works for the Telegram user ID in `OWNER_ID` — set this before you rely on it.
- The webhook URL path includes your bot token as a shared secret so random requests can't inject fake Telegram updates; Render/most hosts serve everything over HTTPS by default.
"# NexBot-Telegram" 
