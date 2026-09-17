from datetime import datetime, timedelta
from telegram.ext import ContextTypes, CommandHandler
from telegram import Update

from bot.services.admin_service import is_user_admin
from bot.services.chat_service import get_or_create_chat
from bot.services import schedule_service
from bot.utils.duration import parse_duration, format_duration

CHECK_INTERVAL_SECONDS = 30


async def announce_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private":
        await update.message.reply_text("⚠️ This only works inside a group.")
        return
    if not await is_user_admin(context.bot, chat.id, user.id):
        await update.message.reply_text("⛔ Only group admins can schedule announcements.")
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "Usage:\n"
            "/announce <interval> <message> — repeats every <interval> (e.g. 6h, 1d)\n"
            "/announce once:<delay> <message> — sends once after <delay> (e.g. once:30m)"
        )
        return

    when_arg = context.args[0]
    text = " ".join(context.args[1:])

    if when_arg.lower().startswith("once:"):
        delay = parse_duration(when_arg.split(":", 1)[1])
        if not delay:
            await update.message.reply_text("⚠️ Couldn't parse that delay. Use e.g. once:30m, once:2h.")
            return
        interval_seconds = None
        first_run = datetime.utcnow() + delay
    else:
        delay = parse_duration(when_arg)
        if not delay:
            await update.message.reply_text("⚠️ Couldn't parse that interval. Use e.g. 1h, 6h, 1d.")
            return
        interval_seconds = int(delay.total_seconds())
        first_run = datetime.utcnow() + delay

    await get_or_create_chat(chat.id, chat.type, chat.title or "")
    msg = await schedule_service.add_scheduled(chat.id, text, first_run, interval_seconds)

    if interval_seconds:
        await update.message.reply_text(
            f"📅 Scheduled (id {msg.id}): repeats every {format_duration(interval_seconds)}, next run in {when_arg}."
        )
    else:
        await update.message.reply_text(f"📅 Scheduled (id {msg.id}): will send once, in {when_arg[5:]}.")


async def announcements_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    items = await schedule_service.list_scheduled(chat.id)
    if not items:
        await update.message.reply_text("No active scheduled announcements. Add one with /announce.")
        return
    lines = []
    for it in items:
        kind = f"every {format_duration(it.interval_seconds)}" if it.interval_seconds else "one-time"
        lines.append(f"• id {it.id} ({kind}): {it.text[:60]}")
    await update.message.reply_text("📅 <b>Scheduled Announcements</b>\n\n" + "\n".join(lines), parse_mode="HTML")


async def unannounce_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user
    if not await is_user_admin(context.bot, chat.id, user.id):
        await update.message.reply_text("⛔ Only group admins can do this.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /unannounce <id> (see /announcements for IDs)")
        return
    try:
        sid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("⚠️ id must be a number.")
        return
    removed = await schedule_service.remove_scheduled(chat.id, sid)
    await update.message.reply_text("🗑 Removed." if removed else "No scheduled announcement with that id.")


async def scheduler_tick(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Runs periodically (job_queue.run_repeating) and sends anything that's due."""
    due = await schedule_service.get_due()
    for item in due:
        try:
            await context.bot.send_message(chat_id=item.chat_id, text=item.text)
        except Exception as e:
            print(f"[scheduler] failed to send scheduled message {item.id} to {item.chat_id}: {e}")

        if item.interval_seconds:
            next_run = item.next_run + timedelta(seconds=item.interval_seconds)
            # Keep advancing if we're badly behind (e.g. bot was offline for a while)
            now = datetime.utcnow()
            while next_run <= now:
                next_run += timedelta(seconds=item.interval_seconds)
            await schedule_service.advance_or_deactivate(item.id, next_run)
        else:
            await schedule_service.advance_or_deactivate(item.id, None)


def register(application):
    application.add_handler(CommandHandler("announce", announce_command))
    application.add_handler(CommandHandler("announcements", announcements_command))
    application.add_handler(CommandHandler("unannounce", unannounce_command))
    application.job_queue.run_repeating(scheduler_tick, interval=CHECK_INTERVAL_SECONDS, first=10)
