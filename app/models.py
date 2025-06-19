from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase

class Base(AsyncAttrs, DeclarativeBase):
    pass

class Truth(Base):
    __tablename__ = "truths"
    id = Column(String, primary_key=True, unique=True, nullable=False)
    timestamp = Column(DateTime, nullable=False) 
    content = Column(Text, nullable=False)
    url = Column(String, nullable=True)
