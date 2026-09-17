import time
from datetime import datetime, timezone
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from telegram.constants import ChatMemberStatus

from bot.services.admin_service import is_user_admin
from bot.services.chat_service import get_or_create_chat
from bot.services.moderation_service import (
    get_or_create_moderation_settings,
    add_warning,
    get_warning_count,
    clear_warnings,
)
from bot.utils.duration import parse_duration

FULL_PERMISSIONS = ChatPermissions(
    can_send_messages=True,
    can_send_audios=True,
    can_send_documents=True,
    can_send_photos=True,
    can_send_videos=True,
    can_send_video_notes=True,
    can_send_voice_notes=True,
    can_send_polls=True,
    can_send_other_messages=True,
    can_add_web_page_previews=True,
)
MUTED_PERMISSIONS = ChatPermissions(can_send_messages=False)


async def _require_group_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private":
        await update.message.reply_text("⚠️ This command only works inside a group.")
        return False
    if not await is_user_admin(context.bot, chat.id, user.id):
        await update.message.reply_text("⛔ Only group admins can use this command.")
        return False
    return True


def _get_target(update: Update):
    """A moderation command targets the user being replied to."""
    if update.message.reply_to_message:
        return update.message.reply_to_message.from_user
    return None


async def _bot_can_restrict(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> bool:
    me = await context.bot.get_chat_member(chat_id, context.bot.id)
    return getattr(me, "can_restrict_members", False) or me.status == ChatMemberStatus.OWNER


# --- Warn ---

async def warn_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_group_admin(update, context):
        return
    target = _get_target(update)
    if not target:
        await update.message.reply_text("↩️ Reply to the user's message with /warn [reason].")
        return
    if target.id == context.bot.id:
        return

    chat = update.effective_chat
    await get_or_create_chat(chat.id, chat.type, chat.title or "")
    settings = await get_or_create_moderation_settings(chat.id)

    reason = " ".join(context.args) if context.args else None
    count = await add_warning(chat.id, target.id, reason)

    name = target.first_name or (f"@{target.username}" if target.username else str(target.id))

    if count >= settings.warn_limit:
        await clear_warnings(chat.id, target.id)
        action = settings.warn_action
        try:
            if action == "ban":
                await context.bot.ban_chat_member(chat.id, target.id)
                await update.message.reply_text(f"🔨 {name} reached {count}/{settings.warn_limit} warnings and was banned.")
            elif action == "kick":
                await context.bot.ban_chat_member(chat.id, target.id)
                await context.bot.unban_chat_member(chat.id, target.id)
                await update.message.reply_text(f"👢 {name} reached {count}/{settings.warn_limit} warnings and was kicked.")
            else:  # mute
                await context.bot.restrict_chat_member(chat.id, target.id, permissions=MUTED_PERMISSIONS)
                await update.message.reply_text(f"🔇 {name} reached {count}/{settings.warn_limit} warnings and was muted.")
        except Exception as e:
            await update.message.reply_text(f"⚠️ Warning limit reached but action failed: {e}")
    else:
        reason_text = f"\nReason: {reason}" if reason else ""
        await update.message.reply_text(f"⚠️ {name} warned ({count}/{settings.warn_limit}).{reason_text}")


async def warnings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    target = _get_target(update) or update.effective_user
    count = await get_warning_count(chat.id, target.id)
    settings = await get_or_create_moderation_settings(chat.id)
    name = target.first_name or (f"@{target.username}" if target.username else str(target.id))
    await update.message.reply_text(f"⚠️ {name} has {count}/{settings.warn_limit} warnings.")


async def unwarn_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_group_admin(update, context):
        return
    target = _get_target(update)
    if not target:
        await update.message.reply_text("↩️ Reply to the user's message with /unwarn.")
        return
    chat = update.effective_chat
    await clear_warnings(chat.id, target.id)
    name = target.first_name or (f"@{target.username}" if target.username else str(target.id))
    await update.message.reply_text(f"✅ Cleared warnings for {name}.")


# --- Mute / Unmute ---

async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_group_admin(update, context):
        return
    target = _get_target(update)
    if not target:
        await update.message.reply_text("↩️ Reply to the user's message with /mute [duration, e.g. 1h].")
        return
    if target.id == context.bot.id:
        return

    chat = update.effective_chat
    until = None
    if context.args:
        delta = parse_duration(context.args[0])
        if delta:
            until = datetime.now(timezone.utc) + delta

    try:
        await context.bot.restrict_chat_member(
            chat.id, target.id, permissions=MUTED_PERMISSIONS, until_date=until
        )
        name = target.first_name or (f"@{target.username}" if target.username else str(target.id))
        suffix = f" for {context.args[0]}" if until else " indefinitely"
        await update.message.reply_text(f"🔇 Muted {name}{suffix}.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Failed to mute: {e}")


async def unmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_group_admin(update, context):
        return
    target = _get_target(update)
    if not target:
        await update.message.reply_text("↩️ Reply to the user's message with /unmute.")
        return
    chat = update.effective_chat
    try:
        await context.bot.restrict_chat_member(chat.id, target.id, permissions=FULL_PERMISSIONS)
        name = target.first_name or (f"@{target.username}" if target.username else str(target.id))
        await update.message.reply_text(f"🔊 Unmuted {name}.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Failed to unmute: {e}")


# --- Kick / Ban / Unban ---

async def kick_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_group_admin(update, context):
        return
    target = _get_target(update)
    if not target:
        await update.message.reply_text("↩️ Reply to the user's message with /kick.")
        return
    if target.id == context.bot.id:
        return
    chat = update.effective_chat
    try:
        await context.bot.ban_chat_member(chat.id, target.id)
        await context.bot.unban_chat_member(chat.id, target.id)  # unban = allowed to rejoin
        name = target.first_name or (f"@{target.username}" if target.username else str(target.id))
        await update.message.reply_text(f"👢 Kicked {name}.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Failed to kick: {e}")


async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_group_admin(update, context):
        return
    target = _get_target(update)
    if not target:
        await update.message.reply_text("↩️ Reply to the user's message with /ban.")
        return
    if target.id == context.bot.id:
        return
    chat = update.effective_chat
    try:
        await context.bot.ban_chat_member(chat.id, target.id)
        name = target.first_name or (f"@{target.username}" if target.username else str(target.id))
        await update.message.reply_text(f"🔨 Banned {name}.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Failed to ban: {e}")


async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_group_admin(update, context):
        return
    if not context.args:
        await update.message.reply_text("Usage: /unban <user_id>")
        return
    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("⚠️ user_id must be a number. Tip: /info in the group shows IDs.")
        return
    chat = update.effective_chat
    try:
        await context.bot.unban_chat_member(chat.id, user_id, only_if_banned=True)
        await update.message.reply_text(f"✅ Unbanned user {user_id}.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Failed to unban: {e}")


# --- Purge ---

async def purge_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _require_group_admin(update, context):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("↩️ Reply to the first message you want deleted, with /purge.")
        return

    chat = update.effective_chat
    start_id = update.message.reply_to_message.message_id
    end_id = update.message.message_id

    deleted = 0
    for msg_id in range(start_id, end_id + 1):
        try:
            await context.bot.delete_message(chat.id, msg_id)
            deleted += 1
        except Exception:
            pass  # message already gone / too old to delete — skip silently

    note = await context.bot.send_message(chat.id, f"🧹 Purged {deleted} messages.")
    context.job_queue.run_once(
        lambda ctx: ctx.bot.delete_message(chat.id, note.message_id), when=5
    )


# --- Anti-flood (in-memory sliding window, no DB writes on the hot path) ---

async def antiflood_watcher(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or update.effective_chat.type not in ("group", "supergroup"):
        return

    chat = update.effective_chat
    user = update.effective_user
    if user is None or user.is_bot:
        return

    settings = await get_or_create_moderation_settings(chat.id)
    if not settings.antiflood_enabled:
        return

    if await is_user_admin(context.bot, chat.id, user.id):
        return  # never flood-limit admins

    bucket = context.bot_data.setdefault("flood", {})
    key = (chat.id, user.id)
    now = time.time()
    timestamps = [t for t in bucket.get(key, []) if now - t < settings.antiflood_window]
    timestamps.append(now)
    bucket[key] = timestamps

    if len(timestamps) > settings.antiflood_limit:
        bucket[key] = []  # reset so we don't re-trigger every message while muted
        try:
            if settings.antiflood_action == "ban":
                await context.bot.ban_chat_member(chat.id, user.id)
                await update.message.reply_text(f"🔨 {user.first_name} was banned for flooding.")
            elif settings.antiflood_action == "kick":
                await context.bot.ban_chat_member(chat.id, user.id)
                await context.bot.unban_chat_member(chat.id, user.id)
                await update.message.reply_text(f"👢 {user.first_name} was kicked for flooding.")
            else:
                await context.bot.restrict_chat_member(chat.id, user.id, permissions=MUTED_PERMISSIONS)
                await update.message.reply_text(f"🔇 {user.first_name} was muted for flooding.")
        except Exception as e:
            print(f"[antiflood] action failed in {chat.id}: {e}")


def register(application):
    application.add_handler(CommandHandler("warn", warn_command))
    application.add_handler(CommandHandler("warnings", warnings_command))
    application.add_handler(CommandHandler("unwarn", unwarn_command))
    application.add_handler(CommandHandler("mute", mute_command))
    application.add_handler(CommandHandler("unmute", unmute_command))
    application.add_handler(CommandHandler("kick", kick_command))
    application.add_handler(CommandHandler("ban", ban_command))
    application.add_handler(CommandHandler("unban", unban_command))
    application.add_handler(CommandHandler("purge", purge_command))

    # Anti-flood runs in its own group so it doesn't block other message handlers.
    application.add_handler(
        MessageHandler(filters.ChatType.GROUPS & filters.ALL & ~filters.StatusUpdate.ALL, antiflood_watcher),
        group=5,
    )
