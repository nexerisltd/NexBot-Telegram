from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, filters, MessageHandler
from telegram.constants import ParseMode

from bot.services.chat_service import get_or_create_chat, get_welcome_settings, get_welcome_buttons
from bot.services.moderation_service import get_or_create_moderation_settings
from bot.services import stats_service
from bot.utils.placeholders import render_welcome_text
from bot.features.captcha.handlers import start_captcha


async def handle_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fires when one or more users join a group the bot is in."""
    if not update.message or not update.message.new_chat_members:
        return

    chat = update.effective_chat

    # Make sure this chat is registered (creates it with defaults if it's new)
    await get_or_create_chat(chat.id, chat.type, chat.title or "")

    mod_settings = await get_or_create_moderation_settings(chat.id)

    settings = await get_welcome_settings(chat.id)

    for new_user in update.message.new_chat_members:
        if new_user.is_bot and new_user.id == context.bot.id:
            continue  # Don't greet the bot itself when it's added to a group

        await stats_service.increment_new_member(chat.id)

        if mod_settings.captcha_enabled:
            await start_captcha(context, chat.id, new_user, mod_settings.captcha_timeout)

        if settings is None or not settings.enabled:
            continue  # Welcome system disabled for this chat

        text = render_welcome_text(settings.message_text, new_user, chat)

        reply_markup = None
        buttons = await get_welcome_buttons(chat.id)
        if buttons:
            rows: dict[int, list] = {}
            for b in buttons:
                rows.setdefault(b.row, []).append(
                    InlineKeyboardButton(text=b.text, url=b.url)
                )
            keyboard = [rows[r] for r in sorted(rows.keys())]
            reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            parse_mode = ParseMode.HTML if settings.parse_mode == "HTML" else ParseMode.MARKDOWN_V2

            if settings.media_file_id and settings.media_type == "photo":
                sent = await context.bot.send_photo(
                    chat_id=chat.id,
                    photo=settings.media_file_id,
                    caption=text,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                )
            else:
                sent = await context.bot.send_message(
                    chat_id=chat.id,
                    text=text,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                )

            if settings.delete_after_seconds:
                context.job_queue.run_once(
                    _delete_message,
                    when=settings.delete_after_seconds,
                    data={"chat_id": chat.id, "message_id": sent.message_id},
                )

        except Exception as e:
            # Bad formatting, revoked permissions, etc. should never crash the bot
            print(f"[greetings] Failed to send welcome in chat {chat.id}: {e}")


async def _delete_message(context: ContextTypes.DEFAULT_TYPE) -> None:
    job_data = context.job.data
    try:
        await context.bot.delete_message(chat_id=job_data["chat_id"], message_id=job_data["message_id"])
    except Exception as e:
        print(f"[greetings] Failed to auto-delete message: {e}")


def register(application):
    application.add_handler(
        MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_new_members)
    )
