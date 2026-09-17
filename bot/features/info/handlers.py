from telegram import Update
from telegram.ext import ContextTypes, CommandHandler


async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user

    text = (
        f"👤 <b>User Info</b>\n"
        f"Name: {user.first_name}\n"
        f"Username: @{user.username if user.username else 'none'}\n"
        f"User ID: <code>{user.id}</code>\n\n"
        f"💬 <b>Chat Info</b>\n"
        f"Chat Name: {chat.title or 'Private chat'}\n"
        f"Chat ID: <code>{chat.id}</code>\n"
        f"Chat Type: {chat.type}"
    )

    await update.message.reply_text(text, parse_mode="HTML")


def register(application):
    application.add_handler(CommandHandler("info", info_command))
