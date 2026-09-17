from sqlalchemy import select
from bot.database.db import get_session
from bot.database.models import Chat, WelcomeSettings


async def get_or_create_chat(chat_id: int, chat_type: str, chat_title: str) -> Chat:
    """Fetch a chat's row, creating it (with default welcome settings) if it's new."""
    async with get_session() as session:
        result = await session.execute(select(Chat).where(Chat.chat_id == chat_id))
        chat = result.scalar_one_or_none()

        if chat is None:
            chat = Chat(chat_id=chat_id, chat_type=chat_type, chat_title=chat_title)
            session.add(chat)
            await session.flush()  # so chat_id is available for the FK below

            welcome = WelcomeSettings(chat_id=chat_id)  # defaults: enabled=False
            session.add(welcome)

            await session.commit()
        else:
            # Keep the stored title in sync in case the group was renamed
            if chat.chat_title != chat_title:
                chat.chat_title = chat_title
                await session.commit()

        return chat


async def get_all_chats() -> list[Chat]:
    """Return every chat the bot is registered in (used for broadcast)."""
    async with get_session() as session:
        result = await session.execute(select(Chat))
        return result.scalars().all()


async def set_welcome_media(chat_id: int, file_id: str, media_type: str = "photo") -> None:
    async with get_session() as session:
        result = await session.execute(
            select(WelcomeSettings).where(WelcomeSettings.chat_id == chat_id)
        )
        settings = result.scalar_one_or_none()
        if settings:
            settings.media_file_id = file_id
            settings.media_type = media_type
            await session.commit()


async def clear_welcome_media(chat_id: int) -> None:
    async with get_session() as session:
        result = await session.execute(
            select(WelcomeSettings).where(WelcomeSettings.chat_id == chat_id)
        )
        settings = result.scalar_one_or_none()
        if settings:
            settings.media_file_id = None
            settings.media_type = None
            await session.commit()


async def set_delete_after(chat_id: int, seconds: int | None) -> None:
    async with get_session() as session:
        result = await session.execute(
            select(WelcomeSettings).where(WelcomeSettings.chat_id == chat_id)
        )
        settings = result.scalar_one_or_none()
        if settings:
            settings.delete_after_seconds = seconds
            await session.commit()


async def get_welcome_settings(chat_id: int) -> WelcomeSettings | None:
    async with get_session() as session:
        result = await session.execute(
            select(WelcomeSettings).where(WelcomeSettings.chat_id == chat_id)
        )
        return result.scalar_one_or_none()


async def get_welcome_buttons(chat_id: int):
    from bot.database.models import WelcomeButton
    async with get_session() as session:
        result = await session.execute(
            select(WelcomeButton)
            .where(WelcomeButton.chat_id == chat_id)
            .order_by(WelcomeButton.row, WelcomeButton.position)
        )
        return result.scalars().all()


async def set_welcome_enabled(chat_id: int, enabled: bool) -> None:
    async with get_session() as session:
        result = await session.execute(
            select(WelcomeSettings).where(WelcomeSettings.chat_id == chat_id)
        )
        settings = result.scalar_one_or_none()
        if settings:
            settings.enabled = enabled
            await session.commit()


async def set_welcome_message(chat_id: int, text: str) -> None:
    async with get_session() as session:
        result = await session.execute(
            select(WelcomeSettings).where(WelcomeSettings.chat_id == chat_id)
        )
        settings = result.scalar_one_or_none()
        if settings:
            settings.message_text = text
            await session.commit()
async def add_welcome_button(chat_id: int, text: str, url: str) -> None:
    from bot.database.models import WelcomeButton
    async with get_session() as session:
        result = await session.execute(
            select(WelcomeButton).where(WelcomeButton.chat_id == chat_id)
        )
        existing = result.scalars().all()
        count = len(existing)
        row = count // 2       # 2 buttons per row, auto-arranged
        position = count % 2
        session.add(WelcomeButton(chat_id=chat_id, row=row, position=position, text=text, url=url))
        await session.commit()


async def remove_welcome_button(chat_id: int, button_id: int) -> None:
    from bot.database.models import WelcomeButton
    async with get_session() as session:
        result = await session.execute(
            select(WelcomeButton)
            .where(WelcomeButton.chat_id == chat_id)
            .order_by(WelcomeButton.row, WelcomeButton.position)
        )
        buttons = result.scalars().all()
        target = next((b for b in buttons if b.id == button_id), None)
        remaining = [b for b in buttons if b.id != button_id]

        if target:
            await session.delete(target)

        # Re-flow remaining buttons so rows stay compact (2 per row)
        for i, b in enumerate(remaining):
            b.row = i // 2
            b.position = i % 2

        await session.commit()