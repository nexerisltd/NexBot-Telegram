from datetime import datetime
from sqlalchemy import select, delete
from bot.database.db import get_session
from bot.database.models import ScheduledMessage


async def add_scheduled(chat_id: int, text: str, first_run: datetime, interval_seconds: int | None) -> ScheduledMessage:
    async with get_session() as session:
        msg = ScheduledMessage(
            chat_id=chat_id,
            text=text,
            interval_seconds=interval_seconds,
            next_run=first_run,
            active=True,
        )
        session.add(msg)
        await session.commit()
        await session.refresh(msg)
        return msg


async def list_scheduled(chat_id: int) -> list[ScheduledMessage]:
    async with get_session() as session:
        result = await session.execute(
            select(ScheduledMessage)
            .where(ScheduledMessage.chat_id == chat_id, ScheduledMessage.active == True)  # noqa: E712
            .order_by(ScheduledMessage.next_run)
        )
        return result.scalars().all()


async def remove_scheduled(chat_id: int, scheduled_id: int) -> bool:
    async with get_session() as session:
        result = await session.execute(
            delete(ScheduledMessage).where(
                ScheduledMessage.chat_id == chat_id, ScheduledMessage.id == scheduled_id
            )
        )
        await session.commit()
        return result.rowcount > 0


async def get_due(now: datetime | None = None) -> list[ScheduledMessage]:
    now = now or datetime.utcnow()
    async with get_session() as session:
        result = await session.execute(
            select(ScheduledMessage).where(
                ScheduledMessage.active == True, ScheduledMessage.next_run <= now  # noqa: E712
            )
        )
        return result.scalars().all()


async def advance_or_deactivate(scheduled_id: int, next_run: datetime | None) -> None:
    """After sending: reschedule a recurring message, or deactivate a one-time one."""
    async with get_session() as session:
        result = await session.execute(
            select(ScheduledMessage).where(ScheduledMessage.id == scheduled_id)
        )
        msg = result.scalar_one_or_none()
        if not msg:
            return
        if next_run is None:
            msg.active = False
        else:
            msg.next_run = next_run
        await session.commit()
