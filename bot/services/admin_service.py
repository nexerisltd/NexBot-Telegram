from telegram import Bot
from telegram.constants import ChatMemberStatus


async def is_user_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
    """Check the user's LIVE admin status via Telegram's API — never trust a cached/stored role."""
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except Exception:
        return False