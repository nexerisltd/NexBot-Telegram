from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👋 Greetings", callback_data="settings:greetings")],
        [InlineKeyboardButton("🛡 Moderation", callback_data="settings:moderation")],
        [InlineKeyboardButton("ℹ️ General", callback_data="settings:general")],
    ])


def greetings_menu_kb(enabled: bool) -> InlineKeyboardMarkup:
    if enabled:
        toggle_button = InlineKeyboardButton("🔴 Disable", callback_data="greetings:disable")
    else:
        toggle_button = InlineKeyboardButton("🟢 Enable", callback_data="greetings:enable")

    return InlineKeyboardMarkup([
        [toggle_button],
        [InlineKeyboardButton("✏️ Edit Message", callback_data="greetings:edit")],
        [InlineKeyboardButton("🖼 Welcome Media", callback_data="settings:media")],
        [InlineKeyboardButton("🔘 Manage Buttons", callback_data="settings:buttons")],
        [InlineKeyboardButton("👀 Preview", callback_data="greetings:preview")],
        [InlineKeyboardButton("⬅️ Back", callback_data="settings:back")],
    ])


def media_menu_kb(has_media: bool) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton("🖼 Set/Replace Image", callback_data="media:set")]]
    if has_media:
        rows.append([InlineKeyboardButton("❌ Remove Image", callback_data="media:clear")])
    rows.append([InlineKeyboardButton("⬅️ Back", callback_data="settings:greetings")])
    return InlineKeyboardMarkup(rows)


def moderation_menu_kb(settings) -> InlineKeyboardMarkup:
    flood_toggle = InlineKeyboardButton(
        "🔴 Anti-flood: On (tap to disable)" if settings.antiflood_enabled else "🟢 Anti-flood: Off (tap to enable)",
        callback_data="moderation:antiflood_toggle",
    )
    captcha_toggle = InlineKeyboardButton(
        "🔴 Captcha: On (tap to disable)" if settings.captcha_enabled else "🟢 Captcha: Off (tap to enable)",
        callback_data="moderation:captcha_toggle",
    )
    return InlineKeyboardMarkup([
        [flood_toggle],
        [captcha_toggle],
        [InlineKeyboardButton(f"⚠️ Warn limit: {settings.warn_limit} (tap to cycle)", callback_data="moderation:cycle_limit")],
        [InlineKeyboardButton(f"🔨 Warn action: {settings.warn_action} (tap to cycle)", callback_data="moderation:cycle_action")],
        [InlineKeyboardButton("⬅️ Back", callback_data="settings:back")],
    ])


def back_only_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="settings:back")]])


def buttons_menu_kb(buttons) -> InlineKeyboardMarkup:
    rows = []
    for b in buttons:
        rows.append([InlineKeyboardButton(f"❌ Remove: {b.text}", callback_data=f"buttons:remove:{b.id}")])
    rows.append([InlineKeyboardButton("➕ Add Button", callback_data="buttons:add")])
    rows.append([InlineKeyboardButton("⬅️ Back", callback_data="settings:greetings")])
    return InlineKeyboardMarkup(rows)


def confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Save", callback_data="confirm:save"),
            InlineKeyboardButton("❌ Cancel", callback_data="confirm:cancel"),
        ],
    ])


def btn_confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Save", callback_data="btnconfirm:save"),
            InlineKeyboardButton("❌ Cancel", callback_data="btnconfirm:cancel"),
        ],
    ])