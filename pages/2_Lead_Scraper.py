import io
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from src.data.cleaner import clean_and_deduplicate
from src.data.email_validator import validate_email
from src.database.db import get_session, init_db
from src.database.repositories import create_lead, create_scrape_job, create_team
from src.scraping.base_scraper import ScrapedTeam

init_db()

st.set_page_config(page_title="Lead Scraper - OYA", page_icon="🔍", layout="wide")
st.title("🔍 Lead Scraper")
st.caption("Find soccer teams, clubs, and academies from multiple sources.")

# --- Session State ---
if "scraped_results" not in st.session_state:
    st.session_state.scraped_results = []
if "scrape_status" not in st.session_state:
    st.session_state.scrape_status = ""

# --- Source Selection ---
tab_google, tab_web, tab_league, tab_manual = st.tabs([
    "Google Maps", "Website URL", "League Directory", "Manual Entry"
])

# ---------- TAB: Google Maps ----------
with tab_google:
    st.subheader("Search Google Maps")
    col1, col2 = st.columns(2)
    with col1:
        gm_query = st.text_input(
            "Search query",
            value="youth soccer clubs",
            key="gm_query",
            placeholder="e.g. soccer teams, football academies",
        )
    with col2:
        gm_location = st.text_input(
            "Location",
            value="London, UK",
            key="gm_location",
            placeholder="e.g. London, UK or New York",
        )
    gm_max = st.slider("Max results", 5, 20, 10, key="gm_max")

    if st.button("Search Google Maps", type="primary", key="btn_gm"):
        try:
            from src.scraping.google_maps_scraper import GoogleMapsScraper
            scraper = GoogleMapsScraper()
            with st.spinner(f"Searching Google Maps for '{gm_query}' in {gm_location}..."):
                results = scraper.scrape(gm_query, location=gm_location, max_results=gm_max)
                cleaned = clean_and_deduplicate(results)
                st.session_state.scraped_results = cleaned
                st.session_state.scrape_status = f"Found {len(cleaned)} teams from Google Maps"
        except ValueError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"Scraping failed: {e}")

# ---------- TAB: Website URL ----------
with tab_web:
    st.subheader("Scrape a Website")
    web_url = st.text_input(
        "Website URL",
        key="web_url",
        placeholder="https://example-league.com/teams",
    )

    if st.button("Scrape Website", type="primary", key="btn_web"):
        if not web_url:
            st.warning("Enter a URL to scrape.")
        else:
            try:
                from src.scraping.web_scraper import WebScraper
                scraper = WebScraper()
                with st.spinner(f"Scraping {web_url}..."):
                    results = scraper.scrape(web_url)
                    cleaned = clean_and_deduplicate(results)
                    st.session_state.scraped_results = cleaned
                    st.session_state.scrape_status = f"Found {len(cleaned)} teams from website"
            except Exception as e:
                st.error(f"Scraping failed: {e}")

# ---------- TAB: League Directory ----------
with tab_league:
    st.subheader("Parse League Directory")
    league_url = st.text_input(
        "League directory URL",
        key="league_url",
        placeholder="https://example-league.com/clubs",
    )

    if st.button("Parse Directory", type="primary", key="btn_league"):
        if not league_url:
            st.warning("Enter a league directory URL.")
        else:
            try:
                from src.scraping.league_scraper import LeagueScraper
                scraper = LeagueScraper()
                with st.spinner(f"Parsing {league_url}..."):
                    results = scraper.scrape(league_url)
                    cleaned = clean_and_deduplicate(results)
                    st.session_state.scraped_results = cleaned
                    st.session_state.scrape_status = f"Found {len(cleaned)} teams from directory"
            except Exception as e:
                st.error(f"Scraping failed: {e}")

# ---------- TAB: Manual Entry ----------
with tab_manual:
    st.subheader("Add Team Manually")
    with st.form("manual_team_form"):
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            m_name = st.text_input("Team name *")
            m_league = st.text_input("League")
            m_location = st.text_input("Location")
            m_website = st.text_input("Website")
        with m_col2:
            m_email = st.text_input("Contact email")
            m_phone = st.text_input("Phone number")
            m_contact = st.text_input("Contact person name")
            m_role = st.text_input("Contact role (e.g. Manager, Coach)")

        submitted = st.form_submit_button("Add Team", type="primary")
        if submitted and m_name:
            manual_team = ScrapedTeam(
                name=m_name,
                league=m_league,
                location=m_location,
                website=m_website,
                email=m_email,
                phone=m_phone,
                contact_name=m_contact,
                contact_role=m_role,
                source_type="manual",
            )
            st.session_state.scraped_results.append(manual_team)
            st.session_state.scrape_status = f"Added '{m_name}' manually"
        elif submitted:
            st.warning("Team name is required.")

# --- Results Section ---
st.markdown("---")
results = st.session_state.scraped_results

if st.session_state.scrape_status:
    st.success(st.session_state.scrape_status)

if results:
    st.subheader(f"Results ({len(results)} teams)")

    # Build dataframe for display
    df_data = []
    for t in results:
        email_status = ""
        if t.email:
            ev = validate_email(t.email)
            email_status = "Valid" if ev.is_valid_format and ev.bounce_risk < 0.5 else "Risky"

        df_data.append({
            "Name": t.name,
            "League": t.league or "-",
            "Location": t.location or "-",
            "Email": t.email or "-",
            "Email Status": email_status or "-",
            "Phone": t.phone or "-",
            "Website": t.website or "-",
            "Source": t.source_type,
        })

    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # --- Actions ---
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        if st.button("Save All to CRM", type="primary"):
            session = get_session()
            try:
                saved = 0
                source = results[0].source_type if results else "unknown"
                job = create_scrape_job(
                    session,
                    source=source,
                    query=st.session_state.get("gm_query", "manual"),
                    status="completed",
                    total_found=len(results),
                    started_at=datetime.now(timezone.utc),
                    completed_at=datetime.now(timezone.utc),
                )

                for t in results:
                    team = create_team(
                        session,
                        name=t.name,
                        league=t.league or None,
                        location=t.location or None,
                        website=t.website or None,
                        social_facebook=t.social_facebook or None,
                        social_instagram=t.social_instagram or None,
                        social_twitter=t.social_twitter or None,
                        source_url=t.source_url or None,
                    )
                    create_lead(
                        session,
                        team_id=team.id,
                        team_name=t.name,
                        league=t.league or None,
                        location=t.location or None,
                        contact_name=t.contact_name or None,
                        contact_email=t.email or None,
                        contact_phone=t.phone or None,
                        contact_role=t.contact_role or None,
                        status="new",
                    )
                    saved += 1

                job.total_valid = saved
                session.commit()
                st.success(f"Saved {saved} leads to CRM!")
            except Exception as e:
                st.error(f"Failed to save: {e}")
            finally:
                session.close()

    with col_b:
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        st.download_button(
            "Export CSV",
            data=csv_buffer.getvalue(),
            file_name="oya_scraped_teams.csv",
            mime="text/csv",
        )

    with col_c:
        if st.button("Clear Results"):
            st.session_state.scraped_results = []
            st.session_state.scrape_status = ""
            st.rerun()

else:
    st.info("Choose a source above and run a search to find teams.")
