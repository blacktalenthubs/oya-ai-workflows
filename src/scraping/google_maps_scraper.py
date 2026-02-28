"""Google Maps / Places API scraper for finding soccer teams and clubs."""

import re

import requests

from src.config import GOOGLE_PLACES_API_KEY
from src.scraping.base_scraper import BaseScraper, ScrapedTeam

PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"


class GoogleMapsScraper(BaseScraper):
    """Scrape team data from Google Places API (New)."""

    source_type = "google_maps"

    def __init__(self, api_key: str = "", **kwargs):
        super().__init__(requests_per_second=2.0, **kwargs)
        self.api_key = api_key or GOOGLE_PLACES_API_KEY

    def scrape(
        self,
        query: str,
        location: str = "",
        max_results: int = 20,
        **kwargs,
    ) -> list[ScrapedTeam]:
        if not self.api_key:
            raise ValueError("Google Places API key not configured. Set it in Settings.")

        search_query = query
        if location:
            search_query = f"{query} in {location}"

        results = self._text_search(search_query, max_results)
        return results

    def _text_search(self, query: str, max_results: int) -> list[ScrapedTeam]:
        """Use Places API v1 Text Search."""
        teams = []
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": (
                "places.displayName,places.formattedAddress,places.nationalPhoneNumber,"
                "places.websiteUri,places.googleMapsUri,places.types"
            ),
        }
        body = {
            "textQuery": query,
            "maxResultCount": min(max_results, 20),
        }

        self._rate_limit()
        try:
            resp = requests.post(PLACES_TEXT_SEARCH_URL, json=body, headers=headers, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            raise RuntimeError(f"Google Places API error: {e}") from e

        for place in data.get("places", []):
            display_name = place.get("displayName", {}).get("text", "")
            if not display_name:
                continue

            address = place.get("formattedAddress", "")
            phone = place.get("nationalPhoneNumber", "")
            website = place.get("websiteUri", "")

            teams.append(ScrapedTeam(
                name=display_name,
                location=address,
                phone=phone,
                website=website,
                source_url=place.get("googleMapsUri", ""),
                source_type=self.source_type,
                raw_data=place,
            ))

            if len(teams) >= max_results:
                break

        return teams

    def enrich_from_website(self, team: ScrapedTeam) -> ScrapedTeam:
        """Try to extract email and social links from team website."""
        if not team.website:
            return team

        try:
            resp = self.get(team.website)
            html = resp.text

            # Extract emails
            emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", html)
            if emails:
                team.email = emails[0]

            # Extract social links
            fb = re.findall(r"https?://(?:www\.)?facebook\.com/[^\s\"'<>]+", html)
            ig = re.findall(r"https?://(?:www\.)?instagram\.com/[^\s\"'<>]+", html)
            tw = re.findall(r"https?://(?:www\.)?(?:twitter|x)\.com/[^\s\"'<>]+", html)

            if fb:
                team.social_facebook = fb[0]
            if ig:
                team.social_instagram = ig[0]
            if tw:
                team.social_twitter = tw[0]

        except requests.RequestException:
            pass  # Website unreachable, skip enrichment

        return team
