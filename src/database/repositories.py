"""CRUD repositories for all entities."""

import json
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.database.models import (
    CampaignRecord,
    DesignRecord,
    LeadRecord,
    ScrapeJobRecord,
    TeamRecord,
    VideoJobRecord,
)


# --- Teams ---

def create_team(session: Session, **kwargs) -> TeamRecord:
    team = TeamRecord(**kwargs)
    session.add(team)
    session.commit()
    session.refresh(team)
    return team


def get_teams(session: Session, limit: int = 100, offset: int = 0) -> list[TeamRecord]:
    return session.query(TeamRecord).offset(offset).limit(limit).all()


def get_team_count(session: Session) -> int:
    return session.query(func.count(TeamRecord.id)).scalar() or 0


# --- Leads ---

def create_lead(session: Session, **kwargs) -> LeadRecord:
    lead = LeadRecord(**kwargs)
    session.add(lead)
    session.commit()
    session.refresh(lead)
    return lead


def get_leads(
    session: Session,
    status: str | None = None,
    team_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[LeadRecord]:
    query = session.query(LeadRecord)
    if status:
        query = query.filter(LeadRecord.status == status)
    if team_type:
        query = query.filter(LeadRecord.team_type == team_type)
    return query.order_by(LeadRecord.created_at.desc()).offset(offset).limit(limit).all()


def get_lead_count(session: Session, status: str | None = None) -> int:
    query = session.query(func.count(LeadRecord.id))
    if status:
        query = query.filter(LeadRecord.status == status)
    return query.scalar() or 0


def update_lead_status(session: Session, lead_id: int, status: str) -> LeadRecord | None:
    lead = session.query(LeadRecord).filter(LeadRecord.id == lead_id).first()
    if lead:
        lead.status = status
        lead.updated_at = datetime.now(timezone.utc)
        session.commit()
        session.refresh(lead)
    return lead


# --- Scrape Jobs ---

def create_scrape_job(session: Session, **kwargs) -> ScrapeJobRecord:
    job = ScrapeJobRecord(**kwargs)
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def get_scrape_jobs(session: Session, limit: int = 20) -> list[ScrapeJobRecord]:
    return (
        session.query(ScrapeJobRecord)
        .order_by(ScrapeJobRecord.id.desc())
        .limit(limit)
        .all()
    )


# --- Campaigns ---

def create_campaign(session: Session, **kwargs) -> CampaignRecord:
    if "segment_filter" in kwargs and isinstance(kwargs["segment_filter"], dict):
        kwargs["segment_filter"] = json.dumps(kwargs["segment_filter"])
    campaign = CampaignRecord(**kwargs)
    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    return campaign


def get_campaigns(session: Session, limit: int = 20) -> list[CampaignRecord]:
    return (
        session.query(CampaignRecord)
        .order_by(CampaignRecord.created_at.desc())
        .limit(limit)
        .all()
    )


def get_campaign_count(session: Session, status: str | None = None) -> int:
    query = session.query(func.count(CampaignRecord.id))
    if status:
        query = query.filter(CampaignRecord.status == status)
    return query.scalar() or 0


# --- Designs ---

def create_design(session: Session, **kwargs) -> DesignRecord:
    design = DesignRecord(**kwargs)
    session.add(design)
    session.commit()
    session.refresh(design)
    return design


def get_designs(session: Session, limit: int = 50) -> list[DesignRecord]:
    return (
        session.query(DesignRecord)
        .order_by(DesignRecord.created_at.desc())
        .limit(limit)
        .all()
    )


def get_design_count(session: Session, status: str | None = None) -> int:
    query = session.query(func.count(DesignRecord.id))
    if status:
        query = query.filter(DesignRecord.status == status)
    return query.scalar() or 0


# --- Video Jobs ---

def create_video_job(session: Session, **kwargs) -> VideoJobRecord:
    job = VideoJobRecord(**kwargs)
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def get_video_jobs(session: Session, limit: int = 20) -> list[VideoJobRecord]:
    return (
        session.query(VideoJobRecord)
        .order_by(VideoJobRecord.created_at.desc())
        .limit(limit)
        .all()
    )


def get_video_job_count(session: Session, status: str | None = None) -> int:
    query = session.query(func.count(VideoJobRecord.id))
    if status:
        query = query.filter(VideoJobRecord.status == status)
    return query.scalar() or 0
