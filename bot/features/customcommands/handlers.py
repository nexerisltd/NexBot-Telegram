from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

from bot.services.admin_service import is_user_admin
from bot.services.chat_service import get_or_create_chat
from bot.services import customcmd_service
from bot.utils.placeholders import render_welcome_text

RESERVED = {
    "start", "help", "info", "settings", "cancel",
    "warn", "warnings", "unwarn", "mute", "unmute", "kick", "ban", "unban", "purge",
    "addcmd", "delcmd", "commands", "announce", "announcements", "unannounce",
    "stats", "broadcast",
}


async def addcmd_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private":
        await update.message.reply_text("⚠️ This only works inside a group.")
        return
    if not await is_user_admin(context.bot, chat.id, user.id):
        await update.message.reply_text("⛔ Only group admins can add custom commands.")
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /addcmd <trigger> <response text>\nExample: /addcmd rules Please read the pinned rules!"
        )
        return

    trigger = context.args[0].lower().lstrip("/")
    if trigger in RESERVED:
        await update.message.reply_text(f"⚠️ '{trigger}' is a built-in command and can't be overridden.")
        return

    response_text = " ".join(context.args[1:])
    await get_or_create_chat(chat.id, chat.type, chat.title or "")
    await customcmd_service.add_command(chat.id, trigger, response_text)
    await update.message.reply_text(f"✅ Saved custom command: /{trigger}")


async def delcmd_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user
    if not await is_user_admin(context.bot, chat.id, user.id):
        await update.message.reply_text("⛔ Only group admins can remove custom commands.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /delcmd <trigger>")
        return

    trigger = context.args[0].lower().lstrip("/")
    removed = await customcmd_service.remove_command(chat.id, trigger)
    if removed:
        await update.message.reply_text(f"🗑 Removed /{trigger}.")
    else:
        await update.message.reply_text(f"No custom command named /{trigger} was found.")


async def commands_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    cmds = await customcmd_service.list_commands(chat.id)
    if not cmds:
        await update.message.reply_text("No custom commands set up yet. Admins can add one with /addcmd.")
        return
    listing = "\n".join(f"• /{c.trigger}" for c in cmds)
    await update.message.reply_text(f"📋 <b>Custom Commands</b>\n\n{listing}", parse_mode="HTML")


async def dispatch_custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fallback handler: fires for any /command not matched by a built-in CommandHandler."""
    if not update.message or not update.message.text:
        return
    chat = update.effective_chat
    if chat.type == "private":
        return

    first_word = update.message.text.split()[0]
    trigger = first_word[1:].split("@")[0].lower()  # strip leading "/" and any "@BotName"
    if trigger in RESERVED:
        return

    cmd = await customcmd_service.get_command(chat.id, trigger)
    if cmd is None:
        return

    text = render_welcome_text(cmd.response_text, update.effective_user, chat)
    await update.message.reply_text(text)


def register(application):
    application.add_handler(CommandHandler("addcmd", addcmd_command))
    application.add_handler(CommandHandler("delcmd", delcmd_command))
    application.add_handler(CommandHandler("commands", commands_command))
    # Runs after all built-in CommandHandlers (higher group number = later), so it
    # only ever fires for commands nothing else already claimed.
    application.add_handler(MessageHandler(filters.COMMAND, dispatch_custom_command), group=10)
