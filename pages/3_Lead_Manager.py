import io
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from src.database.db import get_session, init_db
from src.database.models import LeadRecord
from src.database.repositories import get_lead_count, get_leads, update_lead_status
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

    # --- Query leads ---
    status_filter = None if filter_status == "All" else filter_status
    type_filter = None if filter_type == "All" else filter_type

    leads = get_leads(session, status=status_filter, team_type=type_filter, limit=200)

    # Apply buying potential filter in-memory
    if filter_potential != "All":
        leads = [l for l in leads if l.buying_potential == filter_potential]

    st.markdown("---")

    # --- Leads Table ---
    st.subheader(f"Leads ({len(leads)})")

    if not leads:
        st.warning("No leads match the current filters.")
        st.stop()

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
            "Level": l.competitive_level or "-",
            "Potential": l.buying_potential or "-",
            "Kit %": f"{l.custom_kit_likelihood:.0%}" if l.custom_kit_likelihood else "-",
            "Status": l.status,
        })

    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # --- Bulk Actions ---
    st.markdown("---")
    st.subheader("Actions")

    acol1, acol2, acol3, acol4 = st.columns(4)

    # Segment selected leads with AI
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

                    # Update lead in DB
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

    # Validate emails
    with acol2:
        if st.button("Validate Emails"):
            from src.data.email_validator import validate_email as ve

            validated_count = 0
            with_email = [l for l in leads if l.contact_email]

            if not with_email:
                st.info("No leads with email addresses to validate.")
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

    # Export CSV
    with acol3:
        csv_buf = io.StringIO()
        df.to_csv(csv_buf, index=False)
        st.download_button(
            "Export CSV",
            data=csv_buf.getvalue(),
            file_name="oya_leads.csv",
            mime="text/csv",
        )

    # Mark as contacted
    with acol4:
        if st.button("Mark All as Contacted"):
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

    # --- Lead Detail Expander ---
    st.markdown("---")
    st.subheader("Lead Details")

    lead_names = {l.id: l.team_name for l in leads}
    selected_id = st.selectbox(
        "Select a lead to view details",
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
                st.write(f"**Created**: {lead.created_at}")
            with dcol2:
                st.write(f"**Contact**: {lead.contact_name or '-'}")
                st.write(f"**Email**: {lead.contact_email or '-'}")
                st.write(f"**Phone**: {lead.contact_phone or '-'}")
                st.write(f"**Role**: {lead.contact_role or '-'}")
                st.write(f"**Email Valid**: {lead.email_valid}")
                st.write(f"**Bounce Risk**: {lead.email_bounce_risk or '-'}")

            st.write(f"**Type**: {lead.team_type or '-'} | "
                     f"**Level**: {lead.competitive_level or '-'} | "
                     f"**Buying Potential**: {lead.buying_potential or '-'} | "
                     f"**Kit Likelihood**: {lead.custom_kit_likelihood or '-'}")

            if lead.notes:
                st.write(f"**AI Notes**: {lead.notes}")

finally:
    session.close()
