import os
import asyncio
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from bot.services.chat_service import get_all_chats

OWNER_ID = os.getenv("OWNER_ID")


def _is_owner(user_id: int) -> bool:
    return bool(OWNER_ID) and str(user_id) == str(OWNER_ID)


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not _is_owner(user.id):
        await update.message.reply_text("⛔ This command is restricted to the bot owner.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message> — sends to every group the bot is in.")
        return

    text = "📢 " + " ".join(context.args)
    chats = await get_all_chats()

    sent, failed = 0, 0
    for chat in chats:
        try:
            await context.bot.send_message(chat_id=chat.chat_id, text=text)
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)  # stay comfortably under Telegram's rate limits

    await update.message.reply_text(f"✅ Broadcast sent to {sent} chats ({failed} failed).")


def register(application):
    application.add_handler(CommandHandler("broadcast", broadcast_command))
