import streamlit as st

from src.config import (
    DATABASE_URL,
    GOOGLE_PLACES_API_KEY,
    OPENAI_API_KEY,
    REPLICATE_API_TOKEN,
    SENDGRID_API_KEY,
    TWILIO_ACCOUNT_SID,
)
from src.database.db import init_db

st.set_page_config(page_title="Settings - OYA", page_icon="⚙️", layout="wide")
st.title("⚙️ Settings")

# --- Database Initialization ---
st.header("Database")
col_db1, col_db2 = st.columns([3, 1])
with col_db1:
    st.code(DATABASE_URL, language=None)
with col_db2:
    if st.button("Initialize DB", type="primary"):
        init_db()
        st.success("Database tables created.")

st.markdown("---")

# --- API Key Status ---
st.header("API Keys")
st.caption("Configure API keys in your `.env` file. Status shown below.")

keys = [
    ("OpenAI", OPENAI_API_KEY, "Text generation, image generation (DALL-E)"),
    ("Google Places", GOOGLE_PLACES_API_KEY, "Team data scraping"),
    ("SendGrid", SENDGRID_API_KEY, "Email outreach"),
    ("Twilio", TWILIO_ACCOUNT_SID, "SMS outreach"),
    ("Replicate", REPLICATE_API_TOKEN, "Video generation"),
]

for name, value, purpose in keys:
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        st.write(f"**{name}**")
    with col2:
        if value:
            st.success("Connected", icon="✅")
        else:
            st.warning("Not set", icon="⚠️")
    with col3:
        st.caption(purpose)

st.markdown("---")

# --- .env Helper ---
st.header("Quick Setup")
st.markdown("""
Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Then restart the Streamlit app to pick up the changes.
""")
