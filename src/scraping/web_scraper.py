"""Generic web scraper for extracting team info from any URL."""

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from src.scraping.base_scraper import BaseScraper, ScrapedTeam


class WebScraper(BaseScraper):
    """Scrape team contact info from a given URL."""

    source_type = "web"

    def scrape(self, query: str, **kwargs) -> list[ScrapedTeam]:
        """query is a URL to scrape."""
        url = query
        try:
            resp = self.get(url)
            resp.raise_for_status()
        except Exception as e:
            raise RuntimeError(f"Failed to fetch {url}: {e}") from e

        soup = BeautifulSoup(resp.text, "lxml")
        teams = self._extract_teams(soup, url)
        return teams

    def _extract_teams(self, soup: BeautifulSoup, source_url: str) -> list[ScrapedTeam]:
        """Extract team-like data from a page."""
        teams = []
        text = soup.get_text(separator=" ", strip=True)

        # Extract all emails on the page
        emails = list(set(re.findall(
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text
        )))

        # Extract all phone numbers
        phones = list(set(re.findall(
            r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}", text
        )))

        # Extract social links
        all_links = [a.get("href", "") for a in soup.find_all("a", href=True)]
        facebook = [l for l in all_links if "facebook.com" in l]
        instagram = [l for l in all_links if "instagram.com" in l]
        twitter = [l for l in all_links if "twitter.com" in l or "x.com" in l]

        # Try to find team/org name from page title or headings
        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        h1 = soup.find("h1")
        name = h1.get_text(strip=True) if h1 else title

        if not name:
            name = urlparse(source_url).netloc

        team = ScrapedTeam(
            name=name,
            email=emails[0] if emails else "",
            phone=phones[0] if phones else "",
            website=source_url,
            social_facebook=facebook[0] if facebook else "",
            social_instagram=instagram[0] if instagram else "",
            social_twitter=twitter[0] if twitter else "",
            source_url=source_url,
            source_type=self.source_type,
            raw_data={
                "all_emails": emails,
                "all_phones": phones,
                "all_links_count": len(all_links),
            },
        )
        teams.append(team)

        # Also look for sub-pages with team listings (tables, lists)
        teams.extend(self._extract_from_tables(soup, source_url))

        return teams

    def _extract_from_tables(self, soup: BeautifulSoup, source_url: str) -> list[ScrapedTeam]:
        """Extract team data from HTML tables on the page."""
        teams = []
        tables = soup.find_all("table")

        for table in tables:
            rows = table.find_all("tr")
            if len(rows) < 2:
                continue

            # Try to identify header row
            headers = [th.get_text(strip=True).lower() for th in rows[0].find_all(["th", "td"])]

            # Look for name-like columns
            name_col = None
            for i, h in enumerate(headers):
                if any(kw in h for kw in ["team", "club", "name", "organization"]):
                    name_col = i
                    break

            if name_col is None:
                continue

            for row in rows[1:]:
                cells = row.find_all(["td", "th"])
                if len(cells) <= name_col:
                    continue

                team_name = cells[name_col].get_text(strip=True)
                if not team_name:
                    continue

                # Try to find link in the cell
                link = cells[name_col].find("a", href=True)
                team_url = ""
                if link:
                    team_url = urljoin(source_url, link["href"])

                # Extract email from row text
                row_text = row.get_text(separator=" ", strip=True)
                row_emails = re.findall(
                    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", row_text
                )

                teams.append(ScrapedTeam(
                    name=team_name,
                    email=row_emails[0] if row_emails else "",
                    website=team_url,
                    source_url=source_url,
                    source_type=self.source_type,
                ))

        return teams
