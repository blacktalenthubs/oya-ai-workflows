import streamlit as st

st.set_page_config(
    page_title="OYA AI Workflows",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("OYA AI Workflows")
st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Lead Engine")
    st.write("Scrape team data, clean, segment, and automate outreach.")
    st.page_link("pages/2_Lead_Scraper.py", label="Open Scraper", icon="🔍")
    st.page_link("pages/3_Lead_Manager.py", label="Open CRM", icon="📋")

with col2:
    st.subheader("Jersey Designer")
    st.write("AI-assisted custom kit design with OYA templates.")
    st.page_link("pages/4_Jersey_Designer.py", label="Open Designer", icon="🎨")

with col3:
    st.subheader("Content Studio")
    st.write("Generate marketing videos and content from designs.")
    st.page_link("pages/5_Content_Studio.py", label="Open Studio", icon="🎬")
