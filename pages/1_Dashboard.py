import streamlit as st

from src.database.db import get_session, init_db
from src.database.repositories import (
    get_campaign_count,
    get_design_count,
    get_lead_count,
    get_leads,
    get_video_job_count,
)

st.set_page_config(page_title="Dashboard - OYA", page_icon="📊", layout="wide")

# Ensure DB exists
init_db()

st.title("📊 Dashboard")
st.caption("OYA AI Workflows overview")

session = get_session()

try:
    # --- KPI Cards ---
    col1, col2, col3, col4 = st.columns(4)

    total_leads = get_lead_count(session)
    contacted_leads = get_lead_count(session, status="contacted")
    total_designs = get_design_count(session)
    total_videos = get_video_job_count(session)

    with col1:
        st.metric("Total Leads", total_leads)
    with col2:
        st.metric("Contacted", contacted_leads)
    with col3:
        st.metric("Designs", total_designs)
    with col4:
        st.metric("Videos", total_videos)

    st.markdown("---")

    # --- Workflow Status ---
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.subheader("Lead Engine")
        new_leads = get_lead_count(session, status="new")
        validated = get_lead_count(session, status="validated")
        campaigns = get_campaign_count(session)
        st.write(f"- **New leads**: {new_leads}")
        st.write(f"- **Validated**: {validated}")
        st.write(f"- **Campaigns**: {campaigns}")
        st.page_link("pages/2_Lead_Scraper.py", label="Go to Scraper →")

    with col_b:
        st.subheader("Jersey Designer")
        draft_designs = get_design_count(session, status="draft")
        exported = get_design_count(session, status="exported")
        st.write(f"- **Drafts**: {draft_designs}")
        st.write(f"- **Exported**: {exported}")
        st.page_link("pages/4_Jersey_Designer.py", label="Go to Designer →")

    with col_c:
        st.subheader("Content Studio")
        queued = get_video_job_count(session, status="queued")
        completed = get_video_job_count(session, status="completed")
        st.write(f"- **Queued**: {queued}")
        st.write(f"- **Completed**: {completed}")
        st.page_link("pages/5_Content_Studio.py", label="Go to Studio →")

    st.markdown("---")

    # --- Recent Leads ---
    st.subheader("Recent Leads")
    recent_leads = get_leads(session, limit=10)
    if recent_leads:
        lead_data = [
            {
                "Team": l.team_name,
                "League": l.league or "-",
                "Location": l.location or "-",
                "Status": l.status,
                "Type": l.team_type or "-",
            }
            for l in recent_leads
        ]
        st.dataframe(lead_data, use_container_width=True)
    else:
        st.info("No leads yet. Start by running the Lead Scraper.")

finally:
    session.close()
