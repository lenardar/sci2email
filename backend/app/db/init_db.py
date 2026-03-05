from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.base import Base
from app.db.session import engine
from app.models import User


def _ensure_feed_entry_columns(db: Session) -> None:
    rows = db.execute(text("PRAGMA table_info(feed_entries)")).fetchall()
    existing = {row[1] for row in rows}
    alter_sql = {
        "title_en": "ALTER TABLE feed_entries ADD COLUMN title_en VARCHAR(500) DEFAULT ''",
        "title_zh": "ALTER TABLE feed_entries ADD COLUMN title_zh VARCHAR(500) DEFAULT ''",
        "content_en": "ALTER TABLE feed_entries ADD COLUMN content_en TEXT DEFAULT ''",
        "summary_en": "ALTER TABLE feed_entries ADD COLUMN summary_en TEXT DEFAULT ''",
        "summary_zh": "ALTER TABLE feed_entries ADD COLUMN summary_zh TEXT DEFAULT ''",
        "ai_status": "ALTER TABLE feed_entries ADD COLUMN ai_status VARCHAR(20) DEFAULT 'pending'",
        "ai_error": "ALTER TABLE feed_entries ADD COLUMN ai_error TEXT DEFAULT ''",
        "ai_updated_at": "ALTER TABLE feed_entries ADD COLUMN ai_updated_at DATETIME",
    }
    for column_name, sql in alter_sql.items():
        if column_name not in existing:
            db.execute(text(sql))
    db.commit()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    db = Session(bind=engine)
    try:
        _ensure_feed_entry_columns(db)
        admin = db.query(User).filter(User.username == settings.admin_username).first()
        if not admin:
            db.add(User(username=settings.admin_username, hashed_password=get_password_hash(settings.admin_password)))
            db.commit()
    finally:
        db.close()
