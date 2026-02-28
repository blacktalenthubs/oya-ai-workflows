import io
import json
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from src.database.db import get_session, init_db
from src.database.models import CampaignRecord, LeadRecord
from src.database.repositories import (
    get_campaigns,
    get_lead_count,
    get_leads,
    update_lead_status,
)
from src.outreach.campaign_manager import create_campaign, get_eligible_leads
from src.outreach.template_engine import generate_message, get_default_template
from src.segmentation.classifier import classify_lead

init_db()

st.set_page_config(page_title="Lead Manager - OYA", page_icon="📋", layout="wide")
st.title("📋 Lead Manager")
st.caption("View, filter, segment, and manage your team leads.")

session = get_session()

try:
    # --- KPI Bar ---
    total = get_lead_count(session)
    new = get_lead_count(session, status="new")
    validated = get_lead_count(session, status="validated")
    segmented = get_lead_count(session, status="segmented")
    contacted = get_lead_count(session, status="contacted")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total", total)
    col2.metric("New", new)
    col3.metric("Validated", validated)
    col4.metric("Segmented", segmented)
    col5.metric("Contacted", contacted)

    st.markdown("---")

    if total == 0:
        st.info("No leads yet. Go to the **Lead Scraper** to find teams.")
        st.stop()

    # === TABS: CRM | Outreach | Campaigns ===
    tab_crm, tab_outreach, tab_campaigns = st.tabs(["CRM", "Outreach", "Campaigns"])

    # ==================== TAB: CRM ====================
    with tab_crm:
        # --- Filters ---
        st.subheader("Filters")
        fcol1, fcol2, fcol3 = st.columns(3)

        with fcol1:
            filter_status = st.selectbox(
                "Status",
                ["All", "new", "validated", "enriched", "segmented", "contacted", "responded", "converted"],
                key="filter_status",
            )
        with fcol2:
            filter_type = st.selectbox(
                "Team Type",
                ["All", "youth", "amateur", "adult", "academy", "semi_pro", "sunday_league"],
                key="filter_type",
            )
        with fcol3:
            filter_potential = st.selectbox(
                "Buying Potential",
                ["All", "high", "medium", "low"],
                key="filter_potential",
            )

        status_filter = None if filter_status == "All" else filter_status
        type_filter = None if filter_type == "All" else filter_type
        leads = get_leads(session, status=status_filter, team_type=type_filter, limit=200)

        if filter_potential != "All":
            leads = [l for l in leads if l.buying_potential == filter_potential]

        st.markdown("---")
        st.subheader(f"Leads ({len(leads)})")

        if not leads:
            st.warning("No leads match the current filters.")
        else:
            df_data = []
            for l in leads:
                df_data.append({
                    "ID": l.id,
                    "Team": l.team_name,
                    "League": l.league or "-",
                    "Location": l.location or "-",
                    "Email": l.contact_email or "-",
                    "Phone": l.contact_phone or "-",
                    "Type": l.team_type or "-",
                    "Potential": l.buying_potential or "-",
                    "Status": l.status,
                })

            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

            # --- Bulk Actions ---
            st.markdown("---")
            st.subheader("Actions")
            acol1, acol2, acol3, acol4 = st.columns(4)

            with acol1:
                if st.button("AI Segment All", type="primary"):
                    progress = st.progress(0, text="Segmenting leads...")
                    segmented_count = 0
                    unsegmented = [l for l in leads if l.status in ("new", "validated")]

                    if not unsegmented:
                        st.info("No unsegmented leads to classify.")
                    else:
                        for i, lead in enumerate(unsegmented):
                            result = classify_lead(
                                team_name=lead.team_name,
                                league=lead.league or "",
                                location=lead.location or "",
                                website="",
                            )
                            db_lead = session.query(LeadRecord).filter(LeadRecord.id == lead.id).first()
                            if db_lead:
                                db_lead.team_type = result.get("team_type")
                                db_lead.competitive_level = result.get("competitive_level")
                                db_lead.buying_potential = result.get("buying_potential")
                                db_lead.custom_kit_likelihood = result.get("custom_kit_likelihood")
                                db_lead.status = "segmented"
                                db_lead.notes = result.get("reasoning", "")
                                db_lead.updated_at = datetime.now(timezone.utc)
                                segmented_count += 1
                            progress.progress((i + 1) / len(unsegmented), text=f"Segmenting {i+1}/{len(unsegmented)}...")

                        session.commit()
                        progress.empty()
                        st.success(f"Segmented {segmented_count} leads!")
                        st.rerun()

            with acol2:
                if st.button("Validate Emails"):
                    from src.data.email_validator import validate_email as ve
                    validated_count = 0
                    with_email = [l for l in leads if l.contact_email]
                    if not with_email:
                        st.info("No leads with email addresses.")
                    else:
                        for lead in with_email:
                            result = ve(lead.contact_email)
                            db_lead = session.query(LeadRecord).filter(LeadRecord.id == lead.id).first()
                            if db_lead:
                                db_lead.email_valid = result.is_valid_format and result.has_mx_record
                                db_lead.email_bounce_risk = result.bounce_risk
                                if db_lead.status == "new":
                                    db_lead.status = "validated"
                                validated_count += 1
                        session.commit()
                        st.success(f"Validated {validated_count} emails!")
                        st.rerun()

            with acol3:
                csv_buf = io.StringIO()
                df.to_csv(csv_buf, index=False)
                st.download_button("Export CSV", data=csv_buf.getvalue(), file_name="oya_leads.csv", mime="text/csv")

            with acol4:
                if st.button("Mark All Contacted"):
                    count = 0
                    for lead in leads:
                        if lead.status in ("segmented", "validated", "enriched"):
                            update_lead_status(session, lead.id, "contacted")
                            count += 1
                    if count:
                        st.success(f"Marked {count} leads as contacted!")
                        st.rerun()
                    else:
                        st.info("No eligible leads to mark.")

            # --- Lead Detail ---
            st.markdown("---")
            st.subheader("Lead Details")
            lead_names = {l.id: l.team_name for l in leads}
            selected_id = st.selectbox(
                "Select a lead",
                options=list(lead_names.keys()),
                format_func=lambda x: f"#{x} - {lead_names[x]}",
            )
            if selected_id:
                lead = session.query(LeadRecord).filter(LeadRecord.id == selected_id).first()
                if lead:
                    dcol1, dcol2 = st.columns(2)
                    with dcol1:
                        st.write(f"**Team**: {lead.team_name}")
                        st.write(f"**League**: {lead.league or '-'}")
                        st.write(f"**Location**: {lead.location or '-'}")
                        st.write(f"**Status**: {lead.status}")
                    with dcol2:
                        st.write(f"**Contact**: {lead.contact_name or '-'}")
                        st.write(f"**Email**: {lead.contact_email or '-'}")
                        st.write(f"**Phone**: {lead.contact_phone or '-'}")
                        st.write(f"**Role**: {lead.contact_role or '-'}")

                    st.write(f"**Type**: {lead.team_type or '-'} | "
                             f"**Level**: {lead.competitive_level or '-'} | "
                             f"**Potential**: {lead.buying_potential or '-'} | "
                             f"**Kit %**: {lead.custom_kit_likelihood or '-'}")
                    if lead.notes:
                        st.write(f"**AI Notes**: {lead.notes}")

    # ==================== TAB: OUTREACH ====================
    with tab_outreach:
        st.subheader("Create Outreach Campaign")

        with st.form("outreach_form"):
            oc1, oc2 = st.columns(2)
            with oc1:
                campaign_name = st.text_input("Campaign Name", placeholder="e.g. London Youth Teams - March 2026")
                channel = st.selectbox("Channel", ["email", "sms"])
            with oc2:
                target_type = st.selectbox("Target Team Type", ["All", "youth", "amateur", "adult", "academy", "semi_pro", "sunday_league"])
                target_potential = st.selectbox("Target Buying Potential", ["All", "high", "medium", "low"])

            st.markdown("---")

            # Message composition
            st.markdown("**Message**")
            msg_mode = st.radio("Compose mode", ["Use template", "AI generate", "Write custom"], horizontal=True)

            # Determine team type for templates
            ttype = target_type if target_type != "All" else "default"

            if msg_mode == "Use template":
                template = get_default_template(channel, ttype)
                subject = st.text_input("Subject", value=template["subject"]) if channel == "email" else ""
                body = st.text_area("Message body", value=template["body"], height=250)
                st.caption("Variables: {team_name}, {contact_name}, {league}, {location}")
            elif msg_mode == "AI generate":
                ai_instructions = st.text_area("Special instructions for AI (optional)", placeholder="e.g. Mention upcoming season, be casual")
                subject = ""
                body = ""
                st.info("Message will be AI-generated when you click Preview below.")
            else:
                subject = st.text_input("Subject") if channel == "email" else ""
                body = st.text_area("Message body", height=250, placeholder="Write your message here. Use {team_name}, {contact_name} for personalization.")

            submitted = st.form_submit_button("Preview Campaign", type="primary")

        if submitted and campaign_name:
            # Build segment filter
            seg_filter = {}
            if target_type != "All":
                seg_filter["team_type"] = target_type
            if target_potential != "All":
                seg_filter["buying_potential"] = target_potential

            eligible = get_eligible_leads(session, channel, seg_filter or None)
            st.session_state["campaign_preview"] = {
                "name": campaign_name,
                "channel": channel,
                "segment_filter": seg_filter,
                "eligible_count": len(eligible),
                "msg_mode": msg_mode,
                "subject": subject,
                "body": body,
                "ai_instructions": ai_instructions if msg_mode == "AI generate" else "",
            }

        # --- Preview Section ---
        if "campaign_preview" in st.session_state:
            preview = st.session_state["campaign_preview"]
            st.markdown("---")
            st.subheader("Campaign Preview")

            pcol1, pcol2, pcol3 = st.columns(3)
            pcol1.metric("Eligible Recipients", preview["eligible_count"])
            pcol2.write(f"**Channel**: {preview['channel'].upper()}")
            pcol3.write(f"**Segment**: {preview['segment_filter'] or 'All leads'}")

            # Generate AI message if needed
            if preview["msg_mode"] == "AI generate":
                with st.spinner("AI is writing your message..."):
                    msg = generate_message(
                        team_name="{team_name}",
                        contact_name="{contact_name}",
                        team_type=list(preview["segment_filter"].values())[0] if preview["segment_filter"] else "",
                        channel=preview["channel"],
                        custom_instructions=preview.get("ai_instructions", ""),
                    )
                    preview["subject"] = msg["subject"]
                    preview["body"] = msg["body"]

            if preview["channel"] == "email" and preview["subject"]:
                st.write(f"**Subject**: {preview['subject']}")
            st.text_area("Message Preview", value=preview["body"], height=200, disabled=True)

            if preview["eligible_count"] == 0:
                st.warning("No eligible recipients for this segment/channel. Check that your leads have email/phone data.")
            else:
                bcol1, bcol2 = st.columns(2)
                with bcol1:
                    if st.button("Create Campaign (Draft)", type="primary"):
                        campaign = create_campaign(
                            session=session,
                            name=preview["name"],
                            channel=preview["channel"],
                            subject=preview.get("subject", ""),
                            body=preview["body"],
                            segment_filter=preview["segment_filter"] or None,
                        )
                        st.success(f"Campaign '{campaign.name}' created with {campaign.total_recipients} recipients!")
                        del st.session_state["campaign_preview"]
                        st.rerun()
                with bcol2:
                    if st.button("Send Now"):
                        campaign = create_campaign(
                            session=session,
                            name=preview["name"],
                            channel=preview["channel"],
                            subject=preview.get("subject", ""),
                            body=preview["body"],
                            segment_filter=preview["segment_filter"] or None,
                        )

                        progress = st.progress(0, text="Sending...")

                        def on_progress(current, total_count, result):
                            progress.progress(current / total_count, text=f"Sending {current}/{total_count}...")

                        if preview["channel"] == "email":
                            from src.outreach.campaign_manager import run_email_campaign
                            stats = run_email_campaign(
                                session, campaign,
                                segment_filter=preview["segment_filter"] or None,
                                on_progress=on_progress,
                            )
                        else:
                            from src.outreach.campaign_manager import run_sms_campaign
                            stats = run_sms_campaign(
                                session, campaign,
                                segment_filter=preview["segment_filter"] or None,
                                on_progress=on_progress,
                            )

                        progress.empty()
                        st.success(f"Campaign sent! {stats['sent']}/{stats['total']} delivered.")
                        if stats.get("bounced") or stats.get("failed"):
                            st.warning(f"{stats.get('bounced', 0) + stats.get('failed', 0)} failed.")
                        del st.session_state["campaign_preview"]
                        st.rerun()

    # ==================== TAB: CAMPAIGNS ====================
    with tab_campaigns:
        st.subheader("Campaign History")
        campaigns = get_campaigns(session, limit=50)

        if not campaigns:
            st.info("No campaigns yet. Create one in the Outreach tab.")
        else:
            camp_data = []
            for c in campaigns:
                camp_data.append({
                    "ID": c.id,
                    "Name": c.name,
                    "Channel": c.channel.upper(),
                    "Status": c.status,
                    "Recipients": c.total_recipients,
                    "Sent": c.sent_count,
                    "Opens": c.open_count,
                    "Replies": c.reply_count,
                    "Bounced": c.bounce_count,
                    "Created": c.created_at.strftime("%Y-%m-%d %H:%M") if c.created_at else "-",
                })

            camp_df = pd.DataFrame(camp_data)
            st.dataframe(camp_df, use_container_width=True, hide_index=True)

            # Campaign detail
            st.markdown("---")
            camp_names = {c.id: c.name for c in campaigns}
            selected_camp = st.selectbox(
                "View campaign details",
                options=list(camp_names.keys()),
                format_func=lambda x: f"#{x} - {camp_names[x]}",
            )
            if selected_camp:
                camp = session.query(CampaignRecord).filter(CampaignRecord.id == selected_camp).first()
                if camp:
                    ccol1, ccol2 = st.columns(2)
                    with ccol1:
                        st.write(f"**Name**: {camp.name}")
                        st.write(f"**Channel**: {camp.channel}")
                        st.write(f"**Status**: {camp.status}")
                        if camp.segment_filter:
                            st.write(f"**Segment**: {camp.segment_filter}")
                    with ccol2:
                        if camp.total_recipients > 0:
                            delivery_rate = camp.sent_count / camp.total_recipients * 100
                            st.metric("Delivery Rate", f"{delivery_rate:.0f}%")
                        st.write(f"**Sent**: {camp.sent_count} / {camp.total_recipients}")
                        st.write(f"**Bounced**: {camp.bounce_count}")

                    if camp.template_subject:
                        st.write(f"**Subject**: {camp.template_subject}")
                    if camp.template_body:
                        st.text_area("Message template", value=camp.template_body, disabled=True, height=150)

finally:
    session.close()
