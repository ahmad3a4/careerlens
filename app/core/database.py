from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    func,
)
# from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from app.core.config import DATABASE_URL

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    job_query = Column(String(255), nullable=False)
    alert_interval_hours = Column(Integer, default=6)
    candidate_summary = Column(JSON, nullable=False)
    best_score = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)

    seen_jobs = relationship("SeenJob", back_populates="user", cascade="all, delete-orphan")


class SeenJob(Base):
    __tablename__ = "seen_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_link = Column(Text, nullable=False)
    job_title = Column(String(255), nullable=True)
    job_company = Column(String(255), nullable=True)
    job_score = Column(Integer, default=0)
    pi_alerted = Column(Boolean, default=False)
    seen_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="seen_jobs")


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
