from telegram import Update
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)

from bot.services.admin_service import is_user_admin
from bot.services.chat_service import (
    get_or_create_chat,
    get_welcome_settings,
    get_welcome_buttons,
    set_welcome_enabled,
    set_welcome_message,
    add_welcome_button,
    remove_welcome_button,
    set_welcome_media,
    clear_welcome_media,
)
from bot.services.moderation_service import (
    get_or_create_moderation_settings,
    set_antiflood,
    set_captcha,
    set_warn_limit,
    set_warn_action,
)
from bot.keyboards.settings_kb import (
    main_menu_kb,
    greetings_menu_kb,
    buttons_menu_kb,
    confirm_kb,
    btn_confirm_kb,
    media_menu_kb,
    moderation_menu_kb,
    back_only_kb,
)
from bot.utils.placeholders import render_welcome_text

WAITING_TEXT, CONFIRM = range(2)
WAITING_BUTTON_TEXT, WAITING_BUTTON_URL, BUTTON_CONFIRM = range(2, 5)
WAITING_MEDIA = 5

WARN_LIMIT_CYCLE = [1, 3, 5, 10]
WARN_ACTION_CYCLE = ["mute", "kick", "ban"]


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == "private":
        await update.message.reply_text("⚠️ /settings only works inside a group, not in a private chat.")
        return

    if not await is_user_admin(context.bot, chat.id, user.id):
        await update.message.reply_text("⛔ Only group admins can access settings.")
        return

    await get_or_create_chat(chat.id, chat.type, chat.title or "")
    await update.message.reply_text("⚙️ <b>Bot Settings</b>", parse_mode="HTML", reply_markup=main_menu_kb())


async def handle_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    chat = update.effective_chat
    user = update.effective_user

    if not await is_user_admin(context.bot, chat.id, user.id):
        await query.answer("⛔ Only group admins can do this.", show_alert=True)
        return

    if query.data == "settings:greetings":
        settings = await get_welcome_settings(chat.id)
        enabled = settings.enabled if settings else False
        status_text = "✅ Enabled" if enabled else "❌ Disabled"
        await query.edit_message_text(
            f"👋 <b>Greetings</b>\n\nStatus: {status_text}",
            parse_mode="HTML",
            reply_markup=greetings_menu_kb(enabled),
        )

    elif query.data == "settings:buttons":
        buttons = await get_welcome_buttons(chat.id)
        text = "🔘 <b>Manage Buttons</b>\n\n"
        if buttons:
            text += "\n".join(f"• {b.text} → {b.url}" for b in buttons)
        else:
            text += "No buttons configured yet."
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=buttons_menu_kb(buttons))

    elif query.data == "settings:media":
        settings = await get_welcome_settings(chat.id)
        has_media = bool(settings and settings.media_file_id)
        status = "🖼 An image is set." if has_media else "No image set yet."
        await query.edit_message_text(
            f"🖼 <b>Welcome Media</b>\n\n{status}", parse_mode="HTML", reply_markup=media_menu_kb(has_media)
        )

    elif query.data == "settings:moderation":
        mod_settings = await get_or_create_moderation_settings(chat.id)
        await query.edit_message_text(
            "🛡 <b>Moderation</b>", parse_mode="HTML", reply_markup=moderation_menu_kb(mod_settings)
        )

    elif query.data == "settings:general":
        text = (
            "ℹ️ <b>General</b>\n\n"
            f"Chat name: {chat.title or 'this chat'}\n"
            f"Chat ID: <code>{chat.id}</code>\n"
            f"Chat type: {chat.type}\n\n"
            "Commands: /warn /mute /kick /ban /addcmd /announce /stats — see /help for the full list."
        )
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=back_only_kb())

    elif query.data == "settings:back":
        await query.edit_message_text("⚙️ <b>Bot Settings</b>", parse_mode="HTML", reply_markup=main_menu_kb())


async def handle_greetings_actions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    chat = update.effective_chat
    user = update.effective_user

    if not await is_user_admin(context.bot, chat.id, user.id):
        await query.answer("⛔ Only group admins can do this.", show_alert=True)
        return

    if query.data == "greetings:enable":
        await set_welcome_enabled(chat.id, True)
        await query.edit_message_text(
            "👋 <b>Greetings</b>\n\nStatus: ✅ Enabled", parse_mode="HTML", reply_markup=greetings_menu_kb(True)
        )

    elif query.data == "greetings:disable":
        await set_welcome_enabled(chat.id, False)
        await query.edit_message_text(
            "👋 <b>Greetings</b>\n\nStatus: ❌ Disabled", parse_mode="HTML", reply_markup=greetings_menu_kb(False)
        )

    elif query.data == "greetings:preview":
        settings = await get_welcome_settings(chat.id)
        if not settings:
            await query.answer("No settings found.", show_alert=True)
            return
        text = render_welcome_text(settings.message_text, user, chat)
        try:
            await context.bot.send_message(chat_id=chat.id, text=f"👀 Preview:\n\n{text}", parse_mode="HTML")
        except Exception as e:
            await context.bot.send_message(chat_id=chat.id, text=f"⚠️ Preview failed to render: {e}")


async def handle_moderation_actions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    chat = update.effective_chat
    user = update.effective_user
    if not await is_user_admin(context.bot, chat.id, user.id):
        await query.answer("⛔ Only group admins can do this.", show_alert=True)
        return

    settings = await get_or_create_moderation_settings(chat.id)

    if query.data == "moderation:antiflood_toggle":
        await set_antiflood(chat.id, enabled=not settings.antiflood_enabled)
    elif query.data == "moderation:captcha_toggle":
        await set_captcha(chat.id, enabled=not settings.captcha_enabled)
    elif query.data == "moderation:cycle_limit":
        try:
            idx = WARN_LIMIT_CYCLE.index(settings.warn_limit)
        except ValueError:
            idx = -1
        new_limit = WARN_LIMIT_CYCLE[(idx + 1) % len(WARN_LIMIT_CYCLE)]
        await set_warn_limit(chat.id, new_limit)
    elif query.data == "moderation:cycle_action":
        try:
            idx = WARN_ACTION_CYCLE.index(settings.warn_action)
        except ValueError:
            idx = -1
        new_action = WARN_ACTION_CYCLE[(idx + 1) % len(WARN_ACTION_CYCLE)]
        await set_warn_action(chat.id, new_action)

    settings = await get_or_create_moderation_settings(chat.id)
    await query.edit_message_text("🛡 <b>Moderation</b>", parse_mode="HTML", reply_markup=moderation_menu_kb(settings))


async def media_clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat = update.effective_chat
    user = update.effective_user
    if not await is_user_admin(context.bot, chat.id, user.id):
        await query.answer("⛔ Only group admins can do this.", show_alert=True)
        return
    await clear_welcome_media(chat.id)
    await query.edit_message_text("🖼 <b>Welcome Media</b>\n\nNo image set yet.", parse_mode="HTML", reply_markup=media_menu_kb(False))


async def media_set_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    chat = update.effective_chat
    user = update.effective_user
    if not await is_user_admin(context.bot, chat.id, user.id):
        await query.answer("⛔ Only group admins can do this.", show_alert=True)
        return ConversationHandler.END
    await query.edit_message_text("📷 Send the photo you want to use for the welcome message. /cancel to abort.")
    return WAITING_MEDIA


async def media_set_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message.photo:
        await update.message.reply_text("⚠️ That's not a photo. Please send an image, or /cancel.")
        return WAITING_MEDIA
    file_id = update.message.photo[-1].file_id  # largest size
    chat = update.effective_chat
    await set_welcome_media(chat.id, file_id, "photo")
    await update.message.reply_text("✅ Welcome image saved!")
    return ConversationHandler.END


async def media_set_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Cancelled.")
    return ConversationHandler.END


async def handle_button_remove(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    chat = update.effective_chat
    user = update.effective_user

    if not await is_user_admin(context.bot, chat.id, user.id):
        await query.answer("⛔ Only group admins can do this.", show_alert=True)
        return

    button_id = int(query.data.split(":")[-1])
    await remove_welcome_button(chat.id, button_id)

    buttons = await get_welcome_buttons(chat.id)
    text = "🔘 <b>Manage Buttons</b>\n\n"
    if buttons:
        text += "\n".join(f"• {b.text} → {b.url}" for b in buttons)
    else:
        text += "No buttons configured yet."
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=buttons_menu_kb(buttons))


# --- Edit welcome message conversation ---

async def edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    chat = update.effective_chat
    user = update.effective_user
    if not await is_user_admin(context.bot, chat.id, user.id):
        await query.answer("⛔ Only group admins can do this.", show_alert=True)
        return ConversationHandler.END

    await query.edit_message_text(
        "✏️ Send the new welcome message now.\n\n"
        "Available placeholders:\n"
        "<code>{user} {username} {first_name} {last_name} {user_id} {chat_name} {chat_id}</code>\n\n"
        "Send /cancel to abort.",
        parse_mode="HTML",
    )
    return WAITING_TEXT


async def edit_receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    new_text = update.message.text
    context.chat_data["pending_welcome_text"] = new_text

    chat = update.effective_chat
    user = update.effective_user
    preview = render_welcome_text(new_text, user, chat)

    await update.message.reply_text(f"👀 Preview:\n\n{preview}", parse_mode="HTML", reply_markup=confirm_kb())
    return CONFIRM


async def edit_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    chat = update.effective_chat

    if query.data == "confirm:save":
        new_text = context.chat_data.get("pending_welcome_text")
        if new_text:
            await set_welcome_message(chat.id, new_text)
        await query.edit_message_text("✅ Welcome message saved!")
    else:
        await query.edit_message_text("❌ Cancelled. No changes were made.")

    context.chat_data.pop("pending_welcome_text", None)
    return ConversationHandler.END


async def edit_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Cancelled.")
    context.chat_data.pop("pending_welcome_text", None)
    return ConversationHandler.END


# --- Add button conversation ---

async def button_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    chat = update.effective_chat
    user = update.effective_user
    if not await is_user_admin(context.bot, chat.id, user.id):
        await query.answer("⛔ Only group admins can do this.", show_alert=True)
        return ConversationHandler.END

    await query.edit_message_text('✏️ Send the button TEXT (e.g. "📜 Rules"). Send /cancel to abort.')
    return WAITING_BUTTON_TEXT


async def button_receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.chat_data["pending_button_text"] = update.message.text
    await update.message.reply_text("🔗 Now send the button URL (must start with http:// or https://).")
    return WAITING_BUTTON_URL


async def button_receive_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    url = update.message.text.strip()

    if not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text(
            "⚠️ That doesn't look like a valid URL. It must start with http:// or https://. Try again, or /cancel."
        )
        return WAITING_BUTTON_URL

    context.chat_data["pending_button_url"] = url
    text = context.chat_data.get("pending_button_text")

    await update.message.reply_text(
        f"👀 Preview: [{text}]({url})\n\nSave this button?",
        reply_markup=btn_confirm_kb(),
    )
    return BUTTON_CONFIRM


async def button_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    chat = update.effective_chat

    if query.data == "btnconfirm:save":
        text = context.chat_data.get("pending_button_text")
        url = context.chat_data.get("pending_button_url")
        if text and url:
            await add_welcome_button(chat.id, text, url)
        await query.edit_message_text("✅ Button saved!")
    else:
        await query.edit_message_text("❌ Cancelled. No button added.")

    context.chat_data.pop("pending_button_text", None)
    context.chat_data.pop("pending_button_url", None)
    return ConversationHandler.END


async def button_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Cancelled.")
    context.chat_data.pop("pending_button_text", None)
    context.chat_data.pop("pending_button_url", None)
    return ConversationHandler.END


def register(application):
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CallbackQueryHandler(handle_settings_menu, pattern="^settings:"))
    application.add_handler(
        CallbackQueryHandler(handle_greetings_actions, pattern="^greetings:(enable|disable|preview)$")
    )
    application.add_handler(CallbackQueryHandler(handle_button_remove, pattern="^buttons:remove:"))
    application.add_handler(CallbackQueryHandler(handle_moderation_actions, pattern="^moderation:"))
    application.add_handler(CallbackQueryHandler(media_clear, pattern="^media:clear$"))

    media_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(media_set_start, pattern="^media:set$")],
        states={
            WAITING_MEDIA: [MessageHandler(filters.PHOTO, media_set_receive)],
        },
        fallbacks=[CommandHandler("cancel", media_set_cancel)],
    )
    application.add_handler(media_conversation)

    edit_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_start, pattern="^greetings:edit$")],
        states={
            WAITING_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_receive_text)],
            CONFIRM: [CallbackQueryHandler(edit_confirm, pattern="^confirm:(save|cancel)$")],
        },
        fallbacks=[CommandHandler("cancel", edit_cancel)],
    )
    application.add_handler(edit_conversation)

    button_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_add_start, pattern="^buttons:add$")],
        states={
            WAITING_BUTTON_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, button_receive_text)],
            WAITING_BUTTON_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, button_receive_url)],
            BUTTON_CONFIRM: [CallbackQueryHandler(button_confirm, pattern="^btnconfirm:(save|cancel)$")],
        },
        fallbacks=[CommandHandler("cancel", button_cancel)],
    )
    application.add_handler(button_conversation)