from sqlalchemy import select, func, delete
from bot.database.db import get_session
from bot.database.models import ModerationSettings, Warning


async def get_or_create_moderation_settings(chat_id: int) -> ModerationSettings:
    async with get_session() as session:
        result = await session.execute(
            select(ModerationSettings).where(ModerationSettings.chat_id == chat_id)
        )
        settings = result.scalar_one_or_none()
        if settings is None:
            settings = ModerationSettings(chat_id=chat_id)
            session.add(settings)
            await session.commit()
            await session.refresh(settings)
        return settings


async def set_warn_limit(chat_id: int, limit: int) -> None:
    async with get_session() as session:
        result = await session.execute(select(ModerationSettings).where(ModerationSettings.chat_id == chat_id))
        settings = result.scalar_one_or_none()
        if settings:
            settings.warn_limit = max(1, limit)
            await session.commit()


async def set_warn_action(chat_id: int, action: str) -> None:
    assert action in ("mute", "kick", "ban")
    async with get_session() as session:
        result = await session.execute(select(ModerationSettings).where(ModerationSettings.chat_id == chat_id))
        settings = result.scalar_one_or_none()
        if settings:
            settings.warn_action = action
            await session.commit()


async def set_antiflood(
    chat_id: int,
    enabled: bool | None = None,
    limit: int | None = None,
    window: int | None = None,
    action: str | None = None,
) -> None:
    async with get_session() as session:
        result = await session.execute(select(ModerationSettings).where(ModerationSettings.chat_id == chat_id))
        settings = result.scalar_one_or_none()
        if not settings:
            return
        if enabled is not None:
            settings.antiflood_enabled = enabled
        if limit is not None:
            settings.antiflood_limit = limit
        if window is not None:
            settings.antiflood_window = window
        if action is not None:
            settings.antiflood_action = action
        await session.commit()


async def set_captcha(chat_id: int, enabled: bool | None = None, timeout: int | None = None) -> None:
    async with get_session() as session:
        result = await session.execute(select(ModerationSettings).where(ModerationSettings.chat_id == chat_id))
        settings = result.scalar_one_or_none()
        if not settings:
            return
        if enabled is not None:
            settings.captcha_enabled = enabled
        if timeout is not None:
            settings.captcha_timeout = timeout
        await session.commit()


async def add_warning(chat_id: int, user_id: int, reason: str | None = None) -> int:
    """Add a warning and return the user's new total warning count in this chat."""
    async with get_session() as session:
        session.add(Warning(chat_id=chat_id, user_id=user_id, reason=reason))
        await session.commit()

        result = await session.execute(
            select(func.count()).select_from(Warning).where(
                Warning.chat_id == chat_id, Warning.user_id == user_id
            )
        )
        return result.scalar_one()


async def get_warning_count(chat_id: int, user_id: int) -> int:
    async with get_session() as session:
        result = await session.execute(
            select(func.count()).select_from(Warning).where(
                Warning.chat_id == chat_id, Warning.user_id == user_id
            )
        )
        return result.scalar_one()


async def clear_warnings(chat_id: int, user_id: int) -> None:
    async with get_session() as session:
        await session.execute(
            delete(Warning).where(Warning.chat_id == chat_id, Warning.user_id == user_id)
        )
        await session.commit()
