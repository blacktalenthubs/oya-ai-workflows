import streamlit as st

from src.config import DATABASE_URL, ENV_FILE_PATH, get_key, save_env_file
from src.database.db import init_db

st.set_page_config(page_title="Settings - OYA", page_icon="⚙️", layout="wide")
st.title("⚙️ Settings")

# --- Database ---
st.header("Database")
col_db1, col_db2 = st.columns([3, 1])
with col_db1:
    st.code(DATABASE_URL, language=None)
with col_db2:
    if st.button("Initialize DB", type="primary"):
        init_db()
        st.success("Database tables created.")

st.markdown("---")

# --- API Keys ---
st.header("API Keys")
st.caption(f"Keys are saved to `{ENV_FILE_PATH}` and take effect immediately.")

KEY_CONFIG = [
    ("OPENAI_API_KEY", "OpenAI", "Text generation, image generation (DALL-E)", "sk-..."),
    ("GOOGLE_PLACES_API_KEY", "Google Places", "Team data scraping from Google Maps", "AIza..."),
    ("SENDGRID_API_KEY", "SendGrid", "Email outreach", "SG...."),
    ("TWILIO_ACCOUNT_SID", "Twilio Account SID", "SMS outreach (Account SID)", "AC..."),
    ("TWILIO_AUTH_TOKEN", "Twilio Auth Token", "SMS outreach (Auth Token)", ""),
    ("TWILIO_PHONE_NUMBER", "Twilio Phone Number", "SMS sender number", "+1..."),
    ("REPLICATE_API_TOKEN", "Replicate", "AI video generation", "r8_..."),
]

with st.form("api_keys_form"):
    values = {}
    for env_name, label, description, placeholder in KEY_CONFIG:
        current = get_key(env_name)
        col1, col2 = st.columns([1, 3])
        with col1:
            if current:
                st.success(f"**{label}**", icon="✅")
            else:
                st.warning(f"**{label}**", icon="⚠️")
            st.caption(description)
        with col2:
            values[env_name] = st.text_input(
                label,
                value=current,
                type="password",
                placeholder=placeholder,
                key=f"input_{env_name}",
                label_visibility="collapsed",
            )

    submitted = st.form_submit_button("Save All Keys", type="primary")
    if submitted:
        # Only save non-empty values
        to_save = {k: v for k, v in values.items() if v}
        if to_save:
            save_env_file(to_save)
            st.success(f"Saved {len(to_save)} keys to `.env`. They are active now.")
            st.rerun()
        else:
            st.warning("No keys to save. Enter at least one API key above.")

st.markdown("---")

# --- How to get keys ---
st.header("Where to get API keys")
st.markdown("""
| Service | Get your key | Free tier |
|---------|-------------|-----------|
| **OpenAI** | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) | $5 credit |
| **Google Places** | [console.cloud.google.com](https://console.cloud.google.com/apis/credentials) | $200/mo credit |
| **SendGrid** | [app.sendgrid.com/settings/api_keys](https://app.sendgrid.com/settings/api_keys) | 100 emails/day |
| **Twilio** | [console.twilio.com](https://console.twilio.com/) | Trial credit |
| **Replicate** | [replicate.com/account/api-tokens](https://replicate.com/account/api-tokens) | Pay per use |

**Google Places setup:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project (or select existing)
3. Enable **Places API (New)**
4. Go to **Credentials** → **Create Credentials** → **API Key**
5. Paste the key above
""")
