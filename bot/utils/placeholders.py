from telegram import User, Chat as TgChat


def render_welcome_text(template: str, user: User, chat: TgChat) -> str:
    """Safely substitute placeholders like {user}, {first_name}, {chat_name}, etc."""
    username = f"@{user.username}" if user.username else user.first_name

    values = {
        "user": username,
        "username": user.username or user.first_name,
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
        "user_id": str(user.id),
        "chat_name": chat.title or "this chat",
        "chat_id": str(chat.id),
    }

    text = template
    for key, val in values.items():
        text = text.replace("{" + key + "}", val)

    return text
