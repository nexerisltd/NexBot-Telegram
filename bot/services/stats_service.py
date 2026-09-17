from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func
from bot.database.db import get_session
from bot.database.models import DailyStat


def _today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


async def _get_or_create_today(session, chat_id: int) -> DailyStat:
    today = _today_str()
    result = await session.execute(
        select(DailyStat).where(DailyStat.chat_id == chat_id, DailyStat.date == today)
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = DailyStat(chat_id=chat_id, date=today, message_count=0, new_members=0)
        session.add(row)
        await session.flush()
    return row


async def increment_message(chat_id: int) -> None:
    async with get_session() as session:
        row = await _get_or_create_today(session, chat_id)
        row.message_count += 1
        await session.commit()


async def increment_new_member(chat_id: int) -> None:
    async with get_session() as session:
        row = await _get_or_create_today(session, chat_id)
        row.new_members += 1
        await session.commit()


async def get_today(chat_id: int) -> DailyStat | None:
    async with get_session() as session:
        today = _today_str()
        result = await session.execute(
            select(DailyStat).where(DailyStat.chat_id == chat_id, DailyStat.date == today)
        )
        return result.scalar_one_or_none()


async def get_totals(chat_id: int, days: int = 7) -> dict:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    async with get_session() as session:
        result = await session.execute(
            select(func.sum(DailyStat.message_count), func.sum(DailyStat.new_members))
            .where(DailyStat.chat_id == chat_id, DailyStat.date >= cutoff)
        )
        messages, joins = result.one()
        return {"messages": messages or 0, "new_members": joins or 0, "days": days}
