from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from bot.services.admin_service import is_user_admin

USER_COMMANDS = (
    "/start — check the bot is alive\n"
    "/help — show this message\n"
    "/info — your info and this chat's info\n"
    "/warnings — check your (or a replied user's) warning count\n"
    "/stats — chat activity stats\n"
    "/commands — list this chat's custom commands"
)

ADMIN_COMMANDS = (
    "\n\n🛡 <b>Admin only</b>\n"
    "/settings — open the settings panel\n"
    "/warn /unwarn — reply to a user to warn/clear a warning\n"
    "/mute [duration] /unmute — reply to a user, e.g. /mute 1h\n"
    "/kick /ban /unban <user_id> — reply to a user (unban needs their ID)\n"
    "/purge — reply to the first message to delete, deletes up to here\n"
    "/addcmd <trigger> <text> /delcmd <trigger> — manage custom commands\n"
    "/announce <interval|once:delay> <text> — schedule announcements\n"
    "/announcements /unannounce <id> — manage scheduled announcements"
)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user

    text = f"🆘 <b>Commands</b>\n\n{USER_COMMANDS}"

    if chat.type != "private" and await is_user_admin(context.bot, chat.id, user.id):
        text += ADMIN_COMMANDS

    await update.message.reply_text(text, parse_mode="HTML")


def register(application):
    application.add_handler(CommandHandler("help", help_command))
