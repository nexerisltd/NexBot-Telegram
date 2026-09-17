from sqlalchemy import Column, Integer, BigInteger, String, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone

Base = declarative_base()


def utcnow():
    # Naive UTC on purpose: SQLite has no timezone-aware datetime type, so we keep
    # every stored datetime naive-UTC and compare naive-UTC everywhere for consistency.
    return datetime.utcnow()


class Chat(Base):
    __tablename__ = "chats"

    chat_id = Column(BigInteger, primary_key=True)  # Telegram's chat_id
    chat_type = Column(String(20), nullable=False)   # "group", "supergroup", "channel"
    chat_title = Column(String(255), nullable=True)

    welcome_settings = relationship(
        "WelcomeSettings", back_populates="chat", uselist=False, cascade="all, delete-orphan"
    )
    buttons = relationship(
        "WelcomeButton", back_populates="chat", cascade="all, delete-orphan"
    )
    moderation_settings = relationship(
        "ModerationSettings", back_populates="chat", uselist=False, cascade="all, delete-orphan"
    )


class WelcomeSettings(Base):
    __tablename__ = "welcome_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, ForeignKey("chats.chat_id"), unique=True, nullable=False)

    enabled = Column(Boolean, default=False, nullable=False)
    message_text = Column(Text, default="Welcome {first_name} to {chat_name}! 👋")
    parse_mode = Column(String(20), default="HTML")  # "HTML" or "MarkdownV2"

    media_file_id = Column(String(255), nullable=True)
    media_type = Column(String(20), nullable=True)  # "photo" for now; extendable later

    delete_after_seconds = Column(Integer, nullable=True)  # null = never auto-delete

    chat = relationship("Chat", back_populates="welcome_settings")


class WelcomeButton(Base):
    __tablename__ = "welcome_buttons"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, ForeignKey("chats.chat_id"), nullable=False)

    row = Column(Integer, nullable=False, default=0)       # which row of buttons
    position = Column(Integer, nullable=False, default=0)  # order within the row
    text = Column(String(64), nullable=False)
    url = Column(String(512), nullable=False)

    chat = relationship("Chat", back_populates="buttons")


class ModerationSettings(Base):
    __tablename__ = "moderation_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, ForeignKey("chats.chat_id"), unique=True, nullable=False)

    warn_limit = Column(Integer, default=3, nullable=False)
    warn_action = Column(String(20), default="mute", nullable=False)  # mute, kick, ban

    antiflood_enabled = Column(Boolean, default=False, nullable=False)
    antiflood_limit = Column(Integer, default=5, nullable=False)     # messages
    antiflood_window = Column(Integer, default=10, nullable=False)   # seconds
    antiflood_action = Column(String(20), default="mute", nullable=False)

    captcha_enabled = Column(Boolean, default=False, nullable=False)
    captcha_timeout = Column(Integer, default=120, nullable=False)   # seconds

    chat = relationship("Chat", back_populates="moderation_settings")


class Warning(Base):
    __tablename__ = "warnings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, ForeignKey("chats.chat_id"), nullable=False)
    user_id = Column(BigInteger, nullable=False)
    reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class CustomCommand(Base):
    __tablename__ = "custom_commands"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, ForeignKey("chats.chat_id"), nullable=False)
    trigger = Column(String(64), nullable=False)
    response_text = Column(Text, nullable=False)


class ScheduledMessage(Base):
    __tablename__ = "scheduled_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, ForeignKey("chats.chat_id"), nullable=False)
    text = Column(Text, nullable=False)
    interval_seconds = Column(Integer, nullable=True)  # None = one-time only
    next_run = Column(DateTime, nullable=False)
    active = Column(Boolean, default=True, nullable=False)


class PendingCaptcha(Base):
    __tablename__ = "pending_captchas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    join_message_id = Column(Integer, nullable=True)
    verify_message_id = Column(Integer, nullable=True)
    expires_at = Column(DateTime, nullable=False)


class DailyStat(Base):
    __tablename__ = "daily_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, ForeignKey("chats.chat_id"), nullable=False)
    date = Column(String(10), nullable=False)  # "YYYY-MM-DD"
    message_count = Column(Integer, default=0, nullable=False)
    new_members = Column(Integer, default=0, nullable=False)
