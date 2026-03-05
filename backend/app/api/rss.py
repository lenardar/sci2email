from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
import xml.etree.ElementTree as ET

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import FeedEntry, RssGroup, RssSource, User
from app.schemas.rss import EntryOut, GroupIn, GroupOut, ReaderStatsOut, SourceIn, SourceOut
from app.services.ai_service import enrich_entry_bilingual
from app.services.rss_service import pull_enabled_sources, pull_source

router = APIRouter(prefix="/api/rss", tags=["rss"])


def _find_or_create_group(db: Session, name: Optional[str]) -> Optional[int]:
    if not name or not name.strip():
        return None
    group_name = name.strip()
    group = db.query(RssGroup).filter(RssGroup.name == group_name).first()
    if not group:
        group = RssGroup(name=group_name)
        db.add(group)
        db.flush()
    return group.id


def _walk_opml(node: ET.Element, current_group: Optional[str], rows: list[tuple[str, str, Optional[str]]]) -> None:
    xml_url = node.attrib.get("xmlUrl") or node.attrib.get("xmlurl")
    title = node.attrib.get("title") or node.attrib.get("text") or "Untitled"
    if xml_url:
        rows.append((title.strip(), xml_url.strip(), current_group))
        return

    next_group = current_group
    if node.attrib.get("text"):
        next_group = node.attrib.get("text")
    for child in node.findall("outline"):
        _walk_opml(child, next_group, rows)


@router.get("/groups", response_model=list[GroupOut])
def list_groups(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(RssGroup).order_by(RssGroup.id.desc()).all()


@router.post("/groups", response_model=GroupOut)
def create_group(payload: GroupIn, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    group = RssGroup(name=payload.name)
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


@router.delete("/groups/{group_id}")
def delete_group(group_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    group = db.query(RssGroup).filter(RssGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    db.delete(group)
    db.commit()
    return {"ok": True}


@router.get("/sources", response_model=list[SourceOut])
def list_sources(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(RssSource).order_by(RssSource.id.desc()).all()


@router.post("/sources", response_model=SourceOut)
def create_source(payload: SourceIn, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    source = RssSource(name=payload.name, url=str(payload.url), group_id=payload.group_id, enabled=payload.enabled)
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.put("/sources/{source_id}", response_model=SourceOut)
def update_source(source_id: int, payload: SourceIn, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    source = db.query(RssSource).filter(RssSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    source.name = payload.name
    source.url = str(payload.url)
    source.group_id = payload.group_id
    source.enabled = payload.enabled
    db.commit()
    db.refresh(source)
    return source


@router.delete("/sources/{source_id}")
def delete_source(source_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    source = db.query(RssSource).filter(RssSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    db.delete(source)
    db.commit()
    return {"ok": True}


@router.post("/sources/{source_id}/test")
def test_source(source_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    source = db.query(RssSource).filter(RssSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    added = pull_source(db, source)
    return {"ok": True, "added": added}


@router.post("/import-opml")
async def import_opml(
    file: UploadFile = File(...),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not file.filename.lower().endswith(".opml"):
        raise HTTPException(status_code=400, detail="Only .opml file is supported")

    try:
        content = await file.read()
        root = ET.fromstring(content)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid OPML content")

    body = root.find("body")
    if body is None:
        raise HTTPException(status_code=400, detail="OPML body not found")

    rows: list[tuple[str, str, Optional[str]]] = []
    for outline in body.findall("outline"):
        _walk_opml(outline, None, rows)

    created = 0
    updated = 0
    skipped = 0
    for name, url, group_name in rows:
        source = db.query(RssSource).filter(RssSource.url == url).first()
        group_id = _find_or_create_group(db, group_name)
        if source:
            # If source already exists, update group when possible.
            if group_id is not None and source.group_id != group_id:
                source.group_id = group_id
                updated += 1
            else:
                skipped += 1
            continue

        db.add(RssSource(name=name or url, url=url, group_id=group_id, enabled=True))
        created += 1

    db.commit()
    return {"ok": True, "created": created, "updated": updated, "skipped": skipped}


@router.get("/export-opml")
def export_opml(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    opml = ET.Element("opml", {"version": "2.0"})
    head = ET.SubElement(opml, "head")
    ET.SubElement(head, "title").text = "sci2email-rss-export"
    body = ET.SubElement(opml, "body")

    groups = {g.id: g.name for g in db.query(RssGroup).all()}
    grouped_nodes: dict[Optional[int], ET.Element] = {}
    grouped_nodes[None] = body

    for source in db.query(RssSource).order_by(RssSource.id.asc()).all():
        group_parent = body
        if source.group_id and source.group_id in groups:
            if source.group_id not in grouped_nodes:
                grouped_nodes[source.group_id] = ET.SubElement(body, "outline", {"text": groups[source.group_id], "title": groups[source.group_id]})
            group_parent = grouped_nodes[source.group_id]
        ET.SubElement(
            group_parent,
            "outline",
            {
                "text": source.name,
                "title": source.name,
                "type": "rss",
                "xmlUrl": source.url,
            },
        )

    xml_bytes = ET.tostring(opml, encoding="utf-8", xml_declaration=True)
    return Response(
        content=xml_bytes,
        media_type="text/xml; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="rss-export.opml"'},
    )


@router.post("/pull-now")
def pull_now(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    added = pull_enabled_sources(db)
    return {"ok": True, "added": added}


@router.get("/stats", response_model=ReaderStatsOut)
def reader_stats(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ReaderStatsOut(
        source_count=db.query(RssSource).count(),
        group_count=db.query(RssGroup).count(),
        entry_count=db.query(FeedEntry).count(),
    )


@router.get("/entries", response_model=list[EntryOut])
def list_entries(
    group_id: Optional[int] = Query(default=None),
    source_id: Optional[int] = Query(default=None),
    q: str = Query(default=""),
    limit: int = Query(default=100, ge=1, le=500),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(FeedEntry, RssSource, RssGroup).join(RssSource, FeedEntry.source_id == RssSource.id).outerjoin(RssGroup, RssSource.group_id == RssGroup.id)

    if group_id is not None:
        query = query.filter(RssSource.group_id == group_id)
    if source_id is not None:
        query = query.filter(FeedEntry.source_id == source_id)
    if q.strip():
        like_value = f"%{q.strip()}%"
        query = query.filter(
            or_(
                FeedEntry.title.ilike(like_value),
                FeedEntry.title_en.ilike(like_value),
                FeedEntry.title_zh.ilike(like_value),
            )
        )

    rows = query.order_by(FeedEntry.id.desc()).limit(limit).all()
    return [
        EntryOut(
            id=entry.id,
            source_id=entry.source_id,
            source_name=source.name,
            group_id=source.group_id,
            group_name=group.name if group else "未分组",
            title=entry.title,
            title_en=entry.title_en or entry.title,
            title_zh=entry.title_zh or entry.title,
            summary_en=entry.summary_en or "",
            summary_zh=entry.summary_zh or "",
            link=entry.link,
            published_at=entry.published_at,
            ai_status=entry.ai_status or "pending",
        )
        for entry, source, group in rows
    ]


@router.post("/entries/{entry_id}/ai-refresh")
def refresh_entry_ai(entry_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    entry = db.query(FeedEntry).filter(FeedEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    enrich_entry_bilingual(db, entry)
    db.commit()
    return {"ok": True, "ai_status": entry.ai_status}


@router.post("/ai-refresh-batch")
def refresh_ai_batch(
    group_id: Optional[int] = Query(default=None),
    source_id: Optional[int] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    only_pending: bool = Query(default=False),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(FeedEntry).join(RssSource, FeedEntry.source_id == RssSource.id)
    if group_id is not None:
        query = query.filter(RssSource.group_id == group_id)
    if source_id is not None:
        query = query.filter(FeedEntry.source_id == source_id)
    if only_pending:
        query = query.filter(FeedEntry.ai_status != "success")

    entries = query.order_by(FeedEntry.id.desc()).limit(limit).all()
    success = 0
    failed = 0
    for entry in entries:
        enrich_entry_bilingual(db, entry)
        if entry.ai_status == "success":
            success += 1
        else:
            failed += 1
    db.commit()
    return {"ok": True, "total": len(entries), "success": success, "failed": failed}
