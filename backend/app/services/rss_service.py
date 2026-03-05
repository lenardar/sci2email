import feedparser
from sqlalchemy.orm import Session

from app.models import FeedEntry, PullLog, RssSource


def pull_source(db: Session, source: RssSource) -> int:
    added = 0
    try:
        feed = feedparser.parse(source.url)
        for item in feed.entries[:50]:
            uid = getattr(item, "id", None) or getattr(item, "link", None)
            if not uid:
                continue
            exists = db.query(FeedEntry).filter(FeedEntry.source_id == source.id, FeedEntry.entry_uid == uid).first()
            if exists:
                continue
            entry = FeedEntry(
                source_id=source.id,
                entry_uid=uid,
                title=getattr(item, "title", ""),
                title_en=getattr(item, "title", ""),
                title_zh=getattr(item, "title", ""),
                link=getattr(item, "link", ""),
                content_en=(getattr(item, "summary", "") or getattr(item, "description", "") or "")[:8000],
                published_at=getattr(item, "published", ""),
                ai_status="pending",
            )
            db.add(entry)
            added += 1
        db.add(PullLog(source_id=source.id, status="success", message=f"added={added}"))
        db.commit()
    except Exception as exc:
        db.add(PullLog(source_id=source.id, status="failed", message=str(exc)[:1000]))
        db.commit()
    return added


def pull_enabled_sources(db: Session) -> int:
    total = 0
    sources = db.query(RssSource).filter(RssSource.enabled.is_(True)).all()
    for source in sources:
        total += pull_source(db, source)
    return total
