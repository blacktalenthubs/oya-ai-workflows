"""SQLAlchemy ORM models - database table definitions."""

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class TeamRecord(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    league = Column(String(255))
    location = Column(String(255))
    website = Column(String(500))
    social_facebook = Column(String(500))
    social_instagram = Column(String(500))
    social_twitter = Column(String(500))
    team_type = Column(String(50))
    competitive_level = Column(String(50))
    team_size_estimate = Column(Integer)
    source_url = Column(String(500))
    scraped_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    leads = relationship("LeadRecord", back_populates="team")


class LeadRecord(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    team_name = Column(String(255), nullable=False)
    league = Column(String(255))
    location = Column(String(255))
    contact_name = Column(String(255))
    contact_email = Column(String(255))
    contact_phone = Column(String(50))
    contact_role = Column(String(100))
    team_type = Column(String(50))
    competitive_level = Column(String(50))
    buying_potential = Column(String(20))
    custom_kit_likelihood = Column(Float)
    status = Column(String(50), default="new")
    email_valid = Column(Boolean)
    email_bounce_risk = Column(Float)
    notes = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    team = relationship("TeamRecord", back_populates="leads")


class ScrapeJobRecord(Base):
    __tablename__ = "scrape_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(100), nullable=False)
    query = Column(String(500), nullable=False)
    status = Column(String(50), default="pending")
    total_found = Column(Integer, default=0)
    total_valid = Column(Integer, default=0)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)


class CampaignRecord(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    channel = Column(String(50), nullable=False)
    status = Column(String(50), default="draft")
    template_subject = Column(String(500))
    template_body = Column(Text)
    segment_filter = Column(Text)  # JSON string
    total_recipients = Column(Integer, default=0)
    sent_count = Column(Integer, default=0)
    open_count = Column(Integer, default=0)
    reply_count = Column(Integer, default=0)
    bounce_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class DesignRecord(Base):
    __tablename__ = "designs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    team_name = Column(String(255), nullable=False)
    primary_color = Column(String(7), default="#000000")
    secondary_color = Column(String(7), default="#FFFFFF")
    accent_color = Column(String(7))
    mascot = Column(String(255))
    city = Column(String(255))
    vibe = Column(String(50))
    template_id = Column(String(50))
    collar_style = Column(String(50))
    pattern_style = Column(String(50))
    status = Column(String(50), default="draft")
    image_path = Column(String(500))
    thumbnail_path = Column(String(500))
    ai_prompt_used = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    videos = relationship("VideoJobRecord", back_populates="design")


class VideoJobRecord(Base):
    __tablename__ = "video_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    design_id = Column(Integer, ForeignKey("designs.id"), nullable=True)
    scene_type = Column(String(50), default="stadium")
    style = Column(String(50), default="cinematic")
    duration_seconds = Column(Integer, default=15)
    platforms = Column(String(255), default="instagram")  # comma-separated
    status = Column(String(50), default="queued")
    input_image_path = Column(String(500))
    output_video_path = Column(String(500))
    ai_prompt_used = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime)

    design = relationship("DesignRecord", back_populates="videos")
