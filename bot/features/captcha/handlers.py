from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import ContextTypes, CallbackQueryHandler

from bot.services import captcha_service

RESTRICTED_PERMISSIONS = ChatPermissions(can_send_messages=False)
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


async def start_captcha(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user, timeout_seconds: int) -> None:
    """Restrict a newly-joined user and post a verify-button challenge."""
    try:
        await context.bot.restrict_chat_member(chat_id, user.id, permissions=RESTRICTED_PERMISSIONS)
    except Exception as e:
        print(f"[captcha] could not restrict {user.id} in {chat_id}: {e}")
        return  # if we can't restrict, don't bother with a captcha message either

    expires_at = datetime.utcnow() + timedelta(seconds=timeout_seconds)
    pending = await captcha_service.create_pending(chat_id, user.id, None, expires_at)

    name = user.first_name or (f"@{user.username}" if user.username else str(user.id))
    kb = InlineKeyboardMarkup(
        [[InlineKeyboardButton("✅ I'm not a robot", callback_data=f"captcha:verify:{pending.id}:{user.id}")]]
    )
    sent = await context.bot.send_message(
        chat_id=chat_id,
        text=f"👋 {name}, please tap the button below within {timeout_seconds}s to verify you're human.",
        reply_markup=kb,
    )
    await captcha_service.set_verify_message(pending.id, sent.message_id)

    context.job_queue.run_once(
        _captcha_timeout,
        when=timeout_seconds,
        data={"pending_id": pending.id, "chat_id": chat_id, "user_id": user.id, "message_id": sent.message_id},
    )


async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    parts = query.data.split(":")  # captcha:verify:<pending_id>:<user_id>
    pending_id, target_user_id = int(parts[2]), int(parts[3])

    if query.from_user.id != target_user_id:
        await query.answer("This button isn't for you.", show_alert=True)
        return

    chat = update.effective_chat
    await query.answer("Verified ✅")

    try:
        await context.bot.restrict_chat_member(chat.id, target_user_id, permissions=FULL_PERMISSIONS)
    except Exception as e:
        print(f"[captcha] could not unrestrict {target_user_id} in {chat.id}: {e}")

    await captcha_service.remove_pending(pending_id)
    try:
        await query.edit_message_text("✅ Verified! Welcome to the group.")
    except Exception:
        pass


async def _captcha_timeout(context: ContextTypes.DEFAULT_TYPE) -> None:
    data = context.job.data
    pending = await captcha_service.get_pending(data["chat_id"], data["user_id"])
    if pending is None:
        return  # already verified

    await captcha_service.remove_pending(pending.id)
    try:
        await context.bot.ban_chat_member(data["chat_id"], data["user_id"])
        await context.bot.unban_chat_member(data["chat_id"], data["user_id"])  # kick, not permanent ban
    except Exception as e:
        print(f"[captcha] timeout kick failed: {e}")
    try:
        await context.bot.edit_message_text(
            chat_id=data["chat_id"], message_id=data["message_id"], text="⌛ Verification timed out. User removed."
        )
    except Exception:
        pass


def register(application):
    application.add_handler(CallbackQueryHandler(verify_callback, pattern=r"^captcha:verify:\d+:\d+$"))
