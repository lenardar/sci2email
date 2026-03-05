from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler

from app.db.session import SessionLocal
from app.models import PushTask
from app.services.push_service import run_push_task
from app.services.rss_service import pull_enabled_sources

scheduler = BackgroundScheduler()
_last_run: set[str] = set()


def _pull_job():
    db = SessionLocal()
    try:
        pull_enabled_sources(db)
    finally:
        db.close()


def _dispatch_job():
    db = SessionLocal()
    try:
        tasks = db.query(PushTask).filter(PushTask.enabled.is_(True)).all()
        for task in tasks:
            try:
                now = datetime.now(ZoneInfo(task.timezone))
            except Exception:
                now = datetime.now(ZoneInfo("Asia/Shanghai"))
            current = now.strftime("%H:%M")
            due_times = [t.strip() for t in (task.send_times or "").split(",") if t.strip()]
            if current not in due_times:
                continue
            key = f"{task.id}:{now.strftime('%Y-%m-%d %H:%M')}"
            if key in _last_run:
                continue
            _last_run.add(key)
            run_push_task(db, task)

        # Keep memory bounded.
        if len(_last_run) > 5000:
            _last_run.clear()
    finally:
        db.close()


def start_scheduler():
    if scheduler.running:
        return
    scheduler.add_job(_pull_job, "interval", minutes=15, id="pull_rss", replace_existing=True)
    scheduler.add_job(_dispatch_job, "interval", minutes=1, id="dispatch_push", replace_existing=True)
    scheduler.start()


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
