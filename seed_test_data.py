import asyncio
from bot.database.db import get_session, init_db
from bot.database.models import WelcomeSettings, WelcomeButton
from sqlalchemy import select

TEST_CHAT_ID = -5305664854  # NexBot-Testing group


async def seed():
    await init_db()
    async with get_session() as session:
        result = await session.execute(
            select(WelcomeSettings).where(WelcomeSettings.chat_id == TEST_CHAT_ID)
        )
        settings = result.scalar_one_or_none()

        if settings is None:
            print("❌ No welcome_settings row found — make sure the bot has already")
            print("   seen this chat (e.g. it processed a new_chat_members event) before running this script.")
            return

        settings.enabled = True
        settings.message_text = "Welcome {first_name} (@{username}) to {chat_name}! 👋\n\nGlad to have you here."
        settings.parse_mode = "HTML"

        # Add a couple of test buttons
        session.add(WelcomeButton(chat_id=TEST_CHAT_ID, row=0, position=0, text="📜 Rules", url="https://telegram.org"))
        session.add(WelcomeButton(chat_id=TEST_CHAT_ID, row=0, position=1, text="🌐 Website", url="https://telegram.org"))

        await session.commit()
        print("✅ Welcome settings enabled and buttons added for chat", TEST_CHAT_ID)


if __name__ == "__main__":
    asyncio.run(seed())
