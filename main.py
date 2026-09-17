import os
import asyncio
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from bot.database.db import init_db
from bot.features.greetings.handlers import register as register_greetings
from bot.features.info.handlers import register as register_info
from bot.features.settings.handlers import register as register_settings
from bot.features.help.handlers import register as register_help
from bot.features.moderation.handlers import register as register_moderation
from bot.features.captcha.handlers import register as register_captcha
from bot.features.customcommands.handlers import register as register_customcommands
from bot.features.scheduler.handlers import register as register_scheduler
from bot.features.stats.handlers import register as register_stats
from bot.features.broadcast.handlers import register as register_broadcast

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").strip()
PORT = int(os.getenv("PORT", "8080"))

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.WARNING
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Bot is alive! ✅")


async def on_startup(application) -> None:
    await init_db()
    print("Database initialized ✅")


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN not found. Check your .env file.")

    app = ApplicationBuilder().token(BOT_TOKEN).post_init(on_startup).build()

    app.add_handler(CommandHandler("start", start))
    register_help(app)
    register_info(app)
    register_greetings(app)
    register_captcha(app)          # register before settings/moderation so the callback pattern is matched first
    register_settings(app)
    register_moderation(app)
    register_customcommands(app)   # keep near the end: it has a catch-all CommandHandler fallback
    register_scheduler(app)
    register_stats(app)
    register_broadcast(app)

    if WEBHOOK_URL:
        # Production mode (Render/Railway/etc): a tiny HTTP server listens on PORT
        # and Telegram pushes updates to it. This is what lets a free web-service
        # tier work — the process only needs to respond when Telegram calls it.
        url_path = BOT_TOKEN  # secret-ish path so randoms can't POST fake updates
        webhook_full_url = f"{WEBHOOK_URL.rstrip('/')}/{url_path}"
        print(f"Bot is starting in WEBHOOK mode on port {PORT} -> {webhook_full_url}")
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=url_path,
            webhook_url=webhook_full_url,
        )
    else:
        print("Bot is starting in POLLING mode (local development). Press Ctrl+C to stop.")
        app.run_polling()


if __name__ == "__main__":
    main()
