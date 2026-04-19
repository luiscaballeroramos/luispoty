from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    DateTime,
)
from sqlalchemy.orm import sessionmaker, declarative_base
from config import DB_ENGINE_NAME
from datetime import datetime

engine = create_engine(f"sqlite:///{DB_ENGINE_NAME}")
Session = sessionmaker(bind=engine)


def init_db():
    Base.metadata.create_all(engine)


Base = declarative_base()


class Track(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True)
    spotify_id = Column(String, unique=True, index=True)
    name = Column(String)
    duration_ms = Column(Integer)
    play_count = Column(Integer, default=0)
    last_played_at = Column(DateTime, nullable=True)


class ListeningEvent(Base):
    __tablename__ = "listening_events"

    id = Column(Integer, primary_key=True)
    track_id = Column(Integer, ForeignKey("tracks.id"))
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    played_ms = Column(Integer)
    is_skipped = Column(Boolean)
    created_at = Column(DateTime, default=datetime.now)


class RawPolling(Base):
    __tablename__ = "raw_polling"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now)
    raw_json = Column(String)


class RecentSync(Base):
    __tablename__ = "recent_sync"

    id = Column(Integer, primary_key=True)
    last_played_at = Column(DateTime)
