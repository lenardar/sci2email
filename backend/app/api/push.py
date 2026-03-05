from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models import AppConfig, PushTask, Recipient, RssSource, User
from app.schemas.push import (
    AiSettingsIn,
    AiSettingsOut,
    PushTaskIn,
    PushTaskOut,
    RecipientIn,
    RecipientOut,
    SmtpSettingsIn,
    SmtpSettingsOut,
)
from app.services.mail_service import get_smtp_settings
from app.services.push_service import run_push_task

router = APIRouter(prefix="/api/push", tags=["push"])


def _save_config(db: Session, key: str, value: str) -> None:
    row = db.query(AppConfig).filter(AppConfig.key == key).first()
    if not row:
        row = AppConfig(key=key, value=value)
        db.add(row)
    else:
        row.value = value


def _read_config(db: Session, key: str, default: str = "") -> str:
    row = db.query(AppConfig).filter(AppConfig.key == key).first()
    if not row:
        return default
    return row.value or default


def _task_to_out(task: PushTask) -> PushTaskOut:
    return PushTaskOut(
        id=task.id,
        name=task.name,
        enabled=task.enabled,
        timezone=task.timezone,
        send_times=task.send_times.split(",") if task.send_times else [],
        max_items=task.max_items,
        source_ids=[s.id for s in task.sources],
        recipient_ids=[r.id for r in task.recipients],
    )


@router.get("/smtp-settings", response_model=SmtpSettingsOut)
def get_smtp_config(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    smtp = get_smtp_settings(db)
    return SmtpSettingsOut(
        smtp_host=smtp["smtp_host"] or settings.smtp_host,
        smtp_port=smtp["smtp_port"] or settings.smtp_port,
        smtp_username=smtp["smtp_username"] or settings.smtp_username,
        smtp_from_email=smtp["smtp_from_email"] or settings.smtp_from_email or settings.smtp_username,
        smtp_use_tls=smtp["smtp_use_tls"],
        has_smtp_password=bool(smtp["smtp_password"]),
    )


@router.get("/ai-settings", response_model=AiSettingsOut)
def get_ai_settings(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    enabled = _read_config(db, "ai_enabled", str(settings.ai_enabled)).lower() in ("1", "true", "yes")
    base_url = _read_config(db, "ai_base_url", settings.ai_base_url)
    model = _read_config(db, "ai_model", settings.ai_model)
    timeout = int(_read_config(db, "ai_timeout_seconds", str(settings.ai_timeout_seconds)))
    api_key = _read_config(db, "ai_api_key", settings.ai_api_key)
    return AiSettingsOut(
        ai_enabled=enabled,
        ai_base_url=base_url,
        ai_model=model,
        ai_timeout_seconds=timeout,
        has_ai_api_key=bool(api_key),
    )


@router.put("/ai-settings", response_model=AiSettingsOut)
def update_ai_settings(payload: AiSettingsIn, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _save_config(db, "ai_enabled", "true" if payload.ai_enabled else "false")
    _save_config(db, "ai_base_url", payload.ai_base_url.strip())
    _save_config(db, "ai_model", payload.ai_model.strip())
    _save_config(db, "ai_timeout_seconds", str(payload.ai_timeout_seconds))
    if payload.ai_api_key.strip():
        _save_config(db, "ai_api_key", payload.ai_api_key.strip())
    db.commit()
    return get_ai_settings(_, db)


@router.put("/smtp-settings", response_model=SmtpSettingsOut)
def update_smtp_config(payload: SmtpSettingsIn, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _save_config(db, "smtp_host", payload.smtp_host.strip())
    _save_config(db, "smtp_port", str(payload.smtp_port))
    _save_config(db, "smtp_username", payload.smtp_username)
    _save_config(db, "smtp_from_email", payload.smtp_from_email)
    _save_config(db, "smtp_use_tls", "true" if payload.smtp_use_tls else "false")

    # Keep existing password if user leaves this field empty on updates.
    if payload.smtp_password.strip():
        _save_config(db, "smtp_password", payload.smtp_password)

    db.commit()
    smtp = get_smtp_settings(db)
    return SmtpSettingsOut(
        smtp_host=smtp["smtp_host"],
        smtp_port=smtp["smtp_port"],
        smtp_username=smtp["smtp_username"],
        smtp_from_email=smtp["smtp_from_email"],
        smtp_use_tls=smtp["smtp_use_tls"],
        has_smtp_password=bool(smtp["smtp_password"]),
    )


@router.get("/recipients", response_model=list[RecipientOut])
def list_recipients(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Recipient).order_by(Recipient.id.desc()).all()


@router.post("/recipients", response_model=RecipientOut)
def create_recipient(payload: RecipientIn, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    recipient = Recipient(email=payload.email, enabled=payload.enabled)
    db.add(recipient)
    db.commit()
    db.refresh(recipient)
    return recipient


@router.delete("/recipients/{recipient_id}")
def delete_recipient(recipient_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    recipient = db.query(Recipient).filter(Recipient.id == recipient_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
    db.delete(recipient)
    db.commit()
    return {"ok": True}


@router.get("/tasks", response_model=list[PushTaskOut])
def list_tasks(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [_task_to_out(t) for t in db.query(PushTask).order_by(PushTask.id.desc()).all()]


@router.post("/tasks", response_model=PushTaskOut)
def create_task(payload: PushTaskIn, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = PushTask(
        name=payload.name,
        enabled=payload.enabled,
        timezone=payload.timezone,
        send_times=",".join(payload.send_times),
        max_items=payload.max_items,
    )
    task.sources = db.query(RssSource).filter(RssSource.id.in_(payload.source_ids)).all() if payload.source_ids else []
    task.recipients = db.query(Recipient).filter(Recipient.id.in_(payload.recipient_ids)).all() if payload.recipient_ids else []
    db.add(task)
    db.commit()
    db.refresh(task)
    return _task_to_out(task)


@router.put("/tasks/{task_id}", response_model=PushTaskOut)
def update_task(task_id: int, payload: PushTaskIn, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.query(PushTask).filter(PushTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.name = payload.name
    task.enabled = payload.enabled
    task.timezone = payload.timezone
    task.send_times = ",".join(payload.send_times)
    task.max_items = payload.max_items
    task.sources = db.query(RssSource).filter(RssSource.id.in_(payload.source_ids)).all() if payload.source_ids else []
    task.recipients = db.query(Recipient).filter(Recipient.id.in_(payload.recipient_ids)).all() if payload.recipient_ids else []
    db.commit()
    db.refresh(task)
    return _task_to_out(task)


@router.delete("/tasks/{task_id}")
def delete_task(task_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.query(PushTask).filter(PushTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"ok": True}


@router.post("/tasks/{task_id}/run")
def run_task(task_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.query(PushTask).filter(PushTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return run_push_task(db, task)
