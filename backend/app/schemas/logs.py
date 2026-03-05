from datetime import datetime

from pydantic import BaseModel


class PullLogOut(BaseModel):
    id: int
    source_id: int
    status: str
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


class SendLogOut(BaseModel):
    id: int
    task_id: int
    recipient_email: str
    status: str
    message: str
    created_at: datetime

    class Config:
        from_attributes = True
