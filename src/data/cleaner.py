"""Data cleaning: deduplication, normalization, and merging of scraped teams."""

import re

from src.scraping.base_scraper import ScrapedTeam


def normalize_name(name: str) -> str:
    """Normalize team name for dedup matching."""
    name = name.strip()
    name = re.sub(r"\s+", " ", name)
    # Remove common suffixes for matching
    name = re.sub(r"\b(FC|SC|AFC|CF|United|City|Town|Athletic)\b", "", name, flags=re.I)
    return name.strip().lower()


def normalize_phone(phone: str) -> str:
    """Strip non-digit characters from phone number."""
    return re.sub(r"[^\d+]", "", phone.strip())


def normalize_email(email: str) -> str:
    """Lowercase and strip email."""
    return email.strip().lower()


def normalize_url(url: str) -> str:
    """Ensure URL has scheme, strip trailing slash."""
    url = url.strip()
    if url and not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url.rstrip("/")


def clean_team(team: ScrapedTeam) -> ScrapedTeam:
    """Normalize all fields on a single team record."""
    team.name = team.name.strip()
    team.email = normalize_email(team.email) if team.email else ""
    team.phone = normalize_phone(team.phone) if team.phone else ""
    team.website = normalize_url(team.website) if team.website else ""
    team.location = team.location.strip() if team.location else ""
    team.league = team.league.strip() if team.league else ""
    team.contact_name = team.contact_name.strip() if team.contact_name else ""
    return team


def deduplicate_teams(teams: list[ScrapedTeam]) -> list[ScrapedTeam]:
    """Remove duplicate teams, merging data from duplicates into the best record."""
    seen: dict[str, ScrapedTeam] = {}

    for team in teams:
        key = normalize_name(team.name)
        if not key:
            continue

        if key in seen:
            # Merge: fill in missing fields from the duplicate
            existing = seen[key]
            if not existing.email and team.email:
                existing.email = team.email
            if not existing.phone and team.phone:
                existing.phone = team.phone
            if not existing.website and team.website:
                existing.website = team.website
            if not existing.location and team.location:
                existing.location = team.location
            if not existing.league and team.league:
                existing.league = team.league
            if not existing.social_facebook and team.social_facebook:
                existing.social_facebook = team.social_facebook
            if not existing.social_instagram and team.social_instagram:
                existing.social_instagram = team.social_instagram
            if not existing.contact_name and team.contact_name:
                existing.contact_name = team.contact_name
        else:
            seen[key] = team

    return list(seen.values())


def clean_and_deduplicate(teams: list[ScrapedTeam]) -> list[ScrapedTeam]:
    """Full cleaning pipeline: normalize all fields then deduplicate."""
    cleaned = [clean_team(t) for t in teams]
    deduped = deduplicate_teams(cleaned)
    return deduped
