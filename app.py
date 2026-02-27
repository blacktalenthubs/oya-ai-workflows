import streamlit as st

from src.database.db import init_db

st.set_page_config(
    page_title="OYA AI Workflows",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize database on first load
init_db()

st.title("⚽ OYA AI Workflows")
st.caption("Scalable growth systems for outreach, customization, and marketing.")
st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🔍 Lead Engine")
    st.write("Scrape team data from league sites, Google Maps, and directories. "
             "Clean, validate, segment, and automate outreach.")
    st.page_link("pages/2_Lead_Scraper.py", label="Open Scraper", icon="🔍")
    st.page_link("pages/3_Lead_Manager.py", label="Open CRM", icon="📋")

with col2:
    st.subheader("🎨 Jersey Designer")
    st.write("AI-assisted custom kit design. Input your team identity, "
             "choose templates, and generate professional jersey designs.")
    st.page_link("pages/4_Jersey_Designer.py", label="Open Designer", icon="🎨")

with col3:
    st.subheader("🎬 Content Studio")
    st.write("Generate cinematic marketing videos from jersey designs. "
             "Stadium scenes, lifestyle shots, matchday visuals.")
    st.page_link("pages/5_Content_Studio.py", label="Open Studio", icon="🎬")

st.markdown("---")

st.markdown("""
**Getting started:**
1. Go to **Settings** to configure your API keys
2. Use the **Lead Scraper** to find team contacts
3. Design custom kits in the **Jersey Designer**
4. Create marketing content in the **Content Studio**
""")

st.page_link("pages/1_Dashboard.py", label="View Dashboard", icon="📊")
st.page_link("pages/6_Settings.py", label="Configure Settings", icon="⚙️")
