from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

from bot.services import stats_service


async def count_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or update.effective_chat.type not in ("group", "supergroup"):
        return
    await stats_service.increment_message(update.effective_chat.id)


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat.type == "private":
        await update.message.reply_text("⚠️ /stats only works inside a group.")
        return

    today = await stats_service.get_today(chat.id)
    week = await stats_service.get_totals(chat.id, days=7)

    today_msgs = today.message_count if today else 0
    today_joins = today.new_members if today else 0

    text = (
        f"📊 <b>Stats for {chat.title}</b>\n\n"
        f"Today: {today_msgs} messages, {today_joins} new members\n"
        f"Last {week['days']} days: {week['messages']} messages, {week['new_members']} new members"
    )
    await update.message.reply_text(text, parse_mode="HTML")


def register(application):
    application.add_handler(CommandHandler("stats", stats_command))
    # Passive counter, runs alongside everything else without interfering.
    application.add_handler(
        MessageHandler(filters.ChatType.GROUPS & filters.ALL & ~filters.StatusUpdate.ALL, count_message),
        group=6,
    )
