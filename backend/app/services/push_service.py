import asyncio

from sqlalchemy.orm import Session

from app.models import FeedEntry, PushTask, SendLog
from app.services.ai_service import enrich_entry_bilingual
from app.services.mail_service import get_smtp_settings, send_email


def _build_html(task_name: str, items: list[FeedEntry]) -> str:
    body = [f"<h2>{task_name}</h2>", "<ul>"]
    for item in items:
        title_zh = item.title_zh or item.title_en or item.title
        title_en = item.title_en or item.title
        summary_zh = item.summary_zh or ""
        summary_en = item.summary_en or ""
        body.append("<li>")
        body.append(f'<div><a href="{item.link}"><strong>{title_zh}</strong></a></div>')
        if title_en and title_en != title_zh:
            body.append(f"<div>{title_en}</div>")
        if summary_zh:
            body.append(f"<div>{summary_zh}</div>")
        if summary_en and summary_en != summary_zh:
            body.append(f"<div>{summary_en}</div>")
        body.append("</li>")
    body.append("</ul>")
    return "".join(body)


def run_push_task(db: Session, task: PushTask) -> dict:
    source_ids = [s.id for s in task.sources]
    if not source_ids:
        return {"sent": 0, "reason": "no sources"}

    items = (
        db.query(FeedEntry)
        .filter(FeedEntry.source_id.in_(source_ids), FeedEntry.sent.is_(False))
        .order_by(FeedEntry.id.asc())
        .limit(task.max_items)
        .all()
    )
    if not items:
        return {"sent": 0, "reason": "no new items"}

    # Lazy AI enrichment: only process entries that are going to be sent.
    for item in items:
        if item.ai_status != "success" or not item.summary_en or not item.summary_zh:
            enrich_entry_bilingual(db, item)

    html = _build_html(task.name, items)
    smtp_settings = get_smtp_settings(db)
    success = 0
    for recipient in task.recipients:
        if not recipient.enabled:
            continue
        try:
            asyncio.run(send_email(recipient.email, f"[RSS] {task.name}", html, smtp_settings))
            db.add(SendLog(task_id=task.id, recipient_email=recipient.email, status="success", message=f"items={len(items)}"))
            success += 1
        except Exception as exc:
            db.add(SendLog(task_id=task.id, recipient_email=recipient.email, status="failed", message=str(exc)[:1000]))

    if success > 0:
        for item in items:
            item.sent = True

    db.commit()
    return {"sent": success, "items": len(items)}
