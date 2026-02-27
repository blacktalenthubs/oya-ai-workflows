"""Pydantic models for all OYA AI Workflow entities."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# --- Enums ---

class TeamType(str, Enum):
    YOUTH = "youth"
    AMATEUR = "amateur"
    ADULT = "adult"
    ACADEMY = "academy"
    SEMI_PRO = "semi_pro"
    SUNDAY_LEAGUE = "sunday_league"


class CompetitiveLevel(str, Enum):
    RECREATIONAL = "recreational"
    COMPETITIVE = "competitive"
    SEMI_PRO = "semi_pro"
    ELITE = "elite"


class LeadStatus(str, Enum):
    NEW = "new"
    VALIDATED = "validated"
    ENRICHED = "enriched"
    SEGMENTED = "segmented"
    CONTACTED = "contacted"
    RESPONDED = "responded"
    CONVERTED = "converted"
    UNSUBSCRIBED = "unsubscribed"


class BuyingPotential(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CampaignStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class CampaignChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"


class DesignStatus(str, Enum):
    DRAFT = "draft"
    GENERATED = "generated"
    APPROVED = "approved"
    EXPORTED = "exported"


class DesignVibe(str, Enum):
    AGGRESSIVE = "aggressive"
    CLEAN = "clean"
    CLASSIC = "classic"
    MODERN = "modern"
    MINIMAL = "minimal"
    BOLD = "bold"


class VideoStatus(str, Enum):
    QUEUED = "queued"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class SceneType(str, Enum):
    URBAN_SOCCER = "urban_soccer"
    STREET_FOOTBALL = "street_football"
    STADIUM = "stadium"
    TRAINING_GROUND = "training_ground"
    LOCKER_ROOM = "locker_room"
    NIGHT_MATCH = "night_match"
    DAYLIGHT_MATCH = "daylight_match"
    LIFESTYLE = "lifestyle"
    CULTURAL = "cultural"


class VideoPlatform(str, Enum):
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    WEB = "web"


# --- Workflow 1: Lead Engine ---

class Contact(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role: Optional[str] = None  # e.g. "manager", "admin", "coach"


class Team(BaseModel):
    id: Optional[int] = None
    name: str
    league: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    social_facebook: Optional[str] = None
    social_instagram: Optional[str] = None
    social_twitter: Optional[str] = None
    team_type: Optional[TeamType] = None
    competitive_level: Optional[CompetitiveLevel] = None
    team_size_estimate: Optional[int] = None
    source_url: Optional[str] = None
    scraped_at: Optional[datetime] = None


class Lead(BaseModel):
    id: Optional[int] = None
    team_id: Optional[int] = None
    team_name: str
    league: Optional[str] = None
    location: Optional[str] = None
    contact: Optional[Contact] = None
    team_type: Optional[TeamType] = None
    competitive_level: Optional[CompetitiveLevel] = None
    buying_potential: Optional[BuyingPotential] = None
    custom_kit_likelihood: Optional[float] = Field(None, ge=0.0, le=1.0)
    status: LeadStatus = LeadStatus.NEW
    email_valid: Optional[bool] = None
    email_bounce_risk: Optional[float] = Field(None, ge=0.0, le=1.0)
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ScrapeJob(BaseModel):
    id: Optional[int] = None
    source: str  # "google_maps", "web", "league_directory"
    query: str
    status: str = "pending"  # pending, running, completed, failed
    total_found: int = 0
    total_valid: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# --- Workflow 1: Outreach ---

class MessageTemplate(BaseModel):
    id: Optional[int] = None
    name: str
    channel: CampaignChannel
    subject: Optional[str] = None  # for email
    body: str
    variables: list[str] = []  # e.g. ["team_name", "league", "location"]


class Campaign(BaseModel):
    id: Optional[int] = None
    name: str
    channel: CampaignChannel
    status: CampaignStatus = CampaignStatus.DRAFT
    template_id: Optional[int] = None
    segment_filter: Optional[dict] = None  # e.g. {"team_type": "youth", "region": "London"}
    total_recipients: int = 0
    sent_count: int = 0
    open_count: int = 0
    reply_count: int = 0
    bounce_count: int = 0
    created_at: Optional[datetime] = None


# --- Workflow 2: Jersey Design ---

class DesignInput(BaseModel):
    team_name: str
    primary_color: str = "#000000"
    secondary_color: str = "#FFFFFF"
    accent_color: Optional[str] = None
    mascot: Optional[str] = None
    city: Optional[str] = None
    vibe: DesignVibe = DesignVibe.MODERN
    league_type: Optional[str] = None
    cultural_identity: Optional[str] = None
    template_id: Optional[str] = None
    collar_style: Optional[str] = None
    pattern_style: Optional[str] = None


class Design(BaseModel):
    id: Optional[int] = None
    input_params: DesignInput
    status: DesignStatus = DesignStatus.DRAFT
    image_url: Optional[str] = None  # local path or S3 URL
    thumbnail_url: Optional[str] = None
    ai_prompt_used: Optional[str] = None
    variants: list[str] = []  # URLs to variant images
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# --- Workflow 3: Video/Content ---

class VideoJob(BaseModel):
    id: Optional[int] = None
    design_id: Optional[int] = None
    scene_type: SceneType = SceneType.STADIUM
    style: str = "cinematic"
    duration_seconds: int = 15
    platforms: list[VideoPlatform] = [VideoPlatform.INSTAGRAM]
    status: VideoStatus = VideoStatus.QUEUED
    input_image_url: Optional[str] = None
    output_video_url: Optional[str] = None
    output_formats: dict[str, str] = {}  # {"tiktok": "url", "instagram": "url"}
    ai_prompt_used: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
