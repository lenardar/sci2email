from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


push_task_sources = Table(
    "push_task_sources",
    Base.metadata,
    Column("task_id", ForeignKey("push_tasks.id"), primary_key=True),
    Column("source_id", ForeignKey("rss_sources.id"), primary_key=True),
)

push_task_recipients = Table(
    "push_task_recipients",
    Base.metadata,
    Column("task_id", ForeignKey("push_tasks.id"), primary_key=True),
    Column("recipient_id", ForeignKey("recipients.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)


class RssGroup(Base):
    __tablename__ = "rss_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)

    sources: Mapped[list["RssSource"]] = relationship(back_populates="group")


class RssSource(Base):
    __tablename__ = "rss_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    url: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("rss_groups.id"), nullable=True)

    group: Mapped[Optional[RssGroup]] = relationship(back_populates="sources")


class Recipient(Base):
    __tablename__ = "recipients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class PushTask(Base):
    __tablename__ = "push_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Shanghai")
    send_times: Mapped[str] = mapped_column(String(200), default="09:00")
    max_items: Mapped[int] = mapped_column(Integer, default=20)

    sources: Mapped[list[RssSource]] = relationship(secondary=push_task_sources)
    recipients: Mapped[list[Recipient]] = relationship(secondary=push_task_recipients)


class FeedEntry(Base):
    __tablename__ = "feed_entries"
    __table_args__ = (UniqueConstraint("source_id", "entry_uid", name="uq_source_entry_uid"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("rss_sources.id"), nullable=False)
    entry_uid: Mapped[str] = mapped_column(String(500), nullable=False)
    title: Mapped[str] = mapped_column(String(500), default="")
    title_en: Mapped[str] = mapped_column(String(500), default="")
    title_zh: Mapped[str] = mapped_column(String(500), default="")
    link: Mapped[str] = mapped_column(String(1000), default="")
    content_en: Mapped[str] = mapped_column(Text, default="")
    summary_en: Mapped[str] = mapped_column(Text, default="")
    summary_zh: Mapped[str] = mapped_column(Text, default="")
    published_at: Mapped[str] = mapped_column(String(120), default="")
    ai_status: Mapped[str] = mapped_column(String(20), default="pending")
    ai_error: Mapped[str] = mapped_column(Text, default="")
    ai_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    sent: Mapped[bool] = mapped_column(Boolean, default=False)


class PullLog(Base):
    __tablename__ = "pull_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("rss_sources.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class SendLog(Base):
    __tablename__ = "send_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("push_tasks.id"), nullable=False)
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class AppConfig(Base):
    __tablename__ = "app_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, default="")
