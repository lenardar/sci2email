from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import PullLog, SendLog, User
from app.schemas.logs import PullLogOut, SendLogOut

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("/pull", response_model=list[PullLogOut])
def list_pull_logs(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(PullLog).order_by(PullLog.id.desc()).limit(100).all()


@router.get("/send", response_model=list[SendLogOut])
def list_send_logs(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(SendLog).order_by(SendLog.id.desc()).limit(100).all()
