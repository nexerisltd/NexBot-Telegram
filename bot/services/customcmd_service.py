from sqlalchemy import select, delete
from bot.database.db import get_session
from bot.database.models import CustomCommand


async def add_command(chat_id: int, trigger: str, response_text: str) -> None:
    trigger = trigger.lower().lstrip("/")
    async with get_session() as session:
        result = await session.execute(
            select(CustomCommand).where(CustomCommand.chat_id == chat_id, CustomCommand.trigger == trigger)
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.response_text = response_text
        else:
            session.add(CustomCommand(chat_id=chat_id, trigger=trigger, response_text=response_text))
        await session.commit()


async def remove_command(chat_id: int, trigger: str) -> bool:
    trigger = trigger.lower().lstrip("/")
    async with get_session() as session:
        result = await session.execute(
            delete(CustomCommand).where(CustomCommand.chat_id == chat_id, CustomCommand.trigger == trigger)
        )
        await session.commit()
        return result.rowcount > 0


async def get_command(chat_id: int, trigger: str) -> CustomCommand | None:
    trigger = trigger.lower().lstrip("/")
    async with get_session() as session:
        result = await session.execute(
            select(CustomCommand).where(CustomCommand.chat_id == chat_id, CustomCommand.trigger == trigger)
        )
        return result.scalar_one_or_none()


async def list_commands(chat_id: int) -> list[CustomCommand]:
    async with get_session() as session:
        result = await session.execute(
            select(CustomCommand).where(CustomCommand.chat_id == chat_id).order_by(CustomCommand.trigger)
        )
        return result.scalars().all()
