from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Alert(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    severity: int
    lat: float
    lon: float
    source: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PushSubscription(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    endpoint: str
    p256dh: str
    auth: str
