from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime

class TruthBase(BaseModel):
    id: str
    timestamp: datetime
    content: str
    url: Optional[str] = None

class TruthCreate(TruthBase):
    pass

class TruthOut(TruthBase):
    class Config:
        orm_mode = True
