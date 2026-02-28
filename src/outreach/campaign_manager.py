"""Campaign management: create, send, and track outreach campaigns."""

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.database.models import CampaignRecord, LeadRecord
from src.outreach.email_sender import send_emails_batch
from src.outreach.sms_sender import send_sms_batch
from src.outreach.template_engine import fill_template


def get_eligible_leads(
    session: Session,
    channel: str,
    segment_filter: dict | None = None,
) -> list[LeadRecord]:
    """Get leads eligible for outreach based on channel and segment filters."""
    query = session.query(LeadRecord)

    # Must have contact info for the channel
    if channel == "email":
        query = query.filter(LeadRecord.contact_email.isnot(None))
        query = query.filter(LeadRecord.contact_email != "")
    elif channel == "sms":
        query = query.filter(LeadRecord.contact_phone.isnot(None))
        query = query.filter(LeadRecord.contact_phone != "")

    # Exclude already unsubscribed
    query = query.filter(LeadRecord.status != "unsubscribed")

    # Apply segment filters
    if segment_filter:
        if segment_filter.get("team_type"):
            query = query.filter(LeadRecord.team_type == segment_filter["team_type"])
        if segment_filter.get("competitive_level"):
            query = query.filter(LeadRecord.competitive_level == segment_filter["competitive_level"])
        if segment_filter.get("buying_potential"):
            query = query.filter(LeadRecord.buying_potential == segment_filter["buying_potential"])
        if segment_filter.get("status"):
            query = query.filter(LeadRecord.status == segment_filter["status"])

    return query.all()


def create_campaign(
    session: Session,
    name: str,
    channel: str,
    subject: str,
    body: str,
    segment_filter: dict | None = None,
) -> CampaignRecord:
    """Create a new campaign record."""
    leads = get_eligible_leads(session, channel, segment_filter)

    campaign = CampaignRecord(
        name=name,
        channel=channel,
        status="draft",
        template_subject=subject,
        template_body=body,
        segment_filter=json.dumps(segment_filter) if segment_filter else None,
        total_recipients=len(leads),
        created_at=datetime.now(timezone.utc),
    )
    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    return campaign


def run_email_campaign(
    session: Session,
    campaign: CampaignRecord,
    segment_filter: dict | None = None,
    rate_limit: float = 2.0,
    on_progress: callable = None,
) -> dict:
    """Execute an email campaign. Returns summary stats."""
    leads = get_eligible_leads(session, "email", segment_filter)

    recipients = []
    for lead in leads:
        recipients.append({
            "email": lead.contact_email,
            "name": lead.contact_name or "",
            "team_name": lead.team_name,
            "contact_name": lead.contact_name or "there",
            "league": lead.league or "",
            "location": lead.location or "",
        })

    campaign.status = "active"
    session.commit()

    results = send_emails_batch(
        recipients=recipients,
        subject=campaign.template_subject or "",
        body_template=campaign.template_body or "",
        rate_limit=rate_limit,
        on_progress=on_progress,
    )

    # Update campaign stats
    sent = sum(1 for r in results if r.success)
    bounced = sum(1 for r in results if not r.success and r.error)

    campaign.sent_count = sent
    campaign.bounce_count = bounced
    campaign.status = "completed"

    # Update lead statuses
    for lead, result in zip(leads, results):
        if result.success:
            lead.status = "contacted"
            lead.updated_at = datetime.now(timezone.utc)

    session.commit()

    return {
        "total": len(recipients),
        "sent": sent,
        "bounced": bounced,
        "results": results,
    }


def run_sms_campaign(
    session: Session,
    campaign: CampaignRecord,
    segment_filter: dict | None = None,
    rate_limit: float = 1.0,
    on_progress: callable = None,
) -> dict:
    """Execute an SMS campaign. Returns summary stats."""
    leads = get_eligible_leads(session, "sms", segment_filter)

    recipients = []
    for lead in leads:
        recipients.append({
            "phone": lead.contact_phone,
            "name": lead.contact_name or "",
            "team_name": lead.team_name,
            "contact_name": lead.contact_name or "there",
        })

    campaign.status = "active"
    session.commit()

    results = send_sms_batch(
        recipients=recipients,
        body_template=campaign.template_body or "",
        rate_limit=rate_limit,
        on_progress=on_progress,
    )

    sent = sum(1 for r in results if r.success)
    failed = sum(1 for r in results if not r.success)

    campaign.sent_count = sent
    campaign.bounce_count = failed
    campaign.status = "completed"

    for lead, result in zip(leads, results):
        if result.success:
            lead.status = "contacted"
            lead.updated_at = datetime.now(timezone.utc)

    session.commit()

    return {
        "total": len(recipients),
        "sent": sent,
        "failed": failed,
        "results": results,
    }
