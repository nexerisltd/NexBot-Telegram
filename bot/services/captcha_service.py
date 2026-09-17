from datetime import datetime
from sqlalchemy import select, delete
from bot.database.db import get_session
from bot.database.models import PendingCaptcha


async def create_pending(chat_id: int, user_id: int, join_message_id: int | None, expires_at: datetime) -> PendingCaptcha:
    async with get_session() as session:
        pending = PendingCaptcha(
            chat_id=chat_id, user_id=user_id, join_message_id=join_message_id, expires_at=expires_at
        )
        session.add(pending)
        await session.commit()
        await session.refresh(pending)
        return pending


async def set_verify_message(pending_id: int, message_id: int) -> None:
    async with get_session() as session:
        result = await session.execute(select(PendingCaptcha).where(PendingCaptcha.id == pending_id))
        pending = result.scalar_one_or_none()
        if pending:
            pending.verify_message_id = message_id
            await session.commit()


async def get_pending(chat_id: int, user_id: int) -> PendingCaptcha | None:
    async with get_session() as session:
        result = await session.execute(
            select(PendingCaptcha).where(PendingCaptcha.chat_id == chat_id, PendingCaptcha.user_id == user_id)
        )
        return result.scalar_one_or_none()


async def remove_pending(pending_id: int) -> None:
    async with get_session() as session:
        await session.execute(delete(PendingCaptcha).where(PendingCaptcha.id == pending_id))
        await session.commit()


async def get_expired(now: datetime | None = None) -> list[PendingCaptcha]:
    now = now or datetime.utcnow()
    async with get_session() as session:
        result = await session.execute(select(PendingCaptcha).where(PendingCaptcha.expires_at <= now))
        return result.scalars().all()
