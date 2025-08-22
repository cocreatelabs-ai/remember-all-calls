from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class CallResponse(BaseModel):
    id: int
    filename: str
    status: str
    upload_timestamp: datetime
    duration_seconds: Optional[float] = None

class CallDetail(BaseModel):
    id: int
    filename: str
    status: str
    upload_timestamp: datetime
    duration_seconds: Optional[float] = None
    transcription: Optional[str] = None
    summary: Optional[str] = None
    key_topics: Optional[List[str]] = None
    sentiment: Optional[str] = None
    actions: List[dict] = []

class ActionItem(BaseModel):
    action_id: str
    action_text: str
    priority: Optional[str] = "medium"
    status: str = "pending"