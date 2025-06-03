from sqlalchemy import Column, Integer, String, Boolean, UniqueConstraint, Numeric
import hashlib
from .db import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)              # Название события
    description = Column(String, nullable=True)          # Описание
    date = Column(String, nullable=True)              # Дата и время события
    location = Column(String, nullable=True)             # Место проведения (район, адрес)
    price = Column(Numeric(10, 2), nullable=True)       # Цена
    is_outdoor = Column(Boolean, default=False)          # Открытое/закрытое помещение
    duration_minutes = Column(Integer, nullable=True)    # Продолжительность в минутах
    district = Column(String,nullable=True)              # район события
    source_channel = Column(String, nullable=True)       # Канал, откуда взято событие
    content_hash = Column(String, unique=True)            # Хэш, чтобы не сохранять одно и то же собитие
    

    __table_args__ = (
        UniqueConstraint("content_hash", name="uq_event_content_hash"),
    )
