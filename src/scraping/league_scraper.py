"""League directory scraper - parses structured league/tournament sites."""

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.scraping.base_scraper import BaseScraper, ScrapedTeam


class LeagueScraper(BaseScraper):
    """Scrape team listings from league directory pages."""

    source_type = "league_directory"

    def scrape(self, query: str, **kwargs) -> list[ScrapedTeam]:
        """query is a league directory URL."""
        url = query
        try:
            resp = self.get(url)
            resp.raise_for_status()
        except Exception as e:
            raise RuntimeError(f"Failed to fetch {url}: {e}") from e

        soup = BeautifulSoup(resp.text, "lxml")
        teams = []

        # Strategy 1: Look for team cards / list items
        teams.extend(self._extract_from_cards(soup, url))

        # Strategy 2: Look for tables
        teams.extend(self._extract_from_tables(soup, url))

        # Strategy 3: Look for structured lists
        if not teams:
            teams.extend(self._extract_from_lists(soup, url))

        # Deduplicate by name
        seen = set()
        unique = []
        for t in teams:
            key = t.name.lower().strip()
            if key not in seen:
                seen.add(key)
                unique.append(t)

        return unique

    def _extract_from_cards(self, soup: BeautifulSoup, source_url: str) -> list[ScrapedTeam]:
        """Extract teams from card-style layouts (divs with class containing 'team', 'club')."""
        teams = []
        team_keywords = ["team", "club", "squad", "roster"]

        for kw in team_keywords:
            cards = soup.find_all(["div", "article", "section"], class_=re.compile(kw, re.I))
            for card in cards:
                name_el = card.find(["h2", "h3", "h4", "a", "strong"])
                if not name_el:
                    continue

                name = name_el.get_text(strip=True)
                if not name or len(name) > 200:
                    continue

                link = card.find("a", href=True)
                team_url = urljoin(source_url, link["href"]) if link else ""

                card_text = card.get_text(separator=" ", strip=True)
                emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", card_text)
                phones = re.findall(
                    r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}",
                    card_text,
                )

                teams.append(ScrapedTeam(
                    name=name,
                    email=emails[0] if emails else "",
                    phone=phones[0] if phones else "",
                    website=team_url,
                    source_url=source_url,
                    source_type=self.source_type,
                ))

        return teams

    def _extract_from_tables(self, soup: BeautifulSoup, source_url: str) -> list[ScrapedTeam]:
        """Extract from standings/roster tables."""
        teams = []

        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            if len(rows) < 2:
                continue

            headers = [th.get_text(strip=True).lower() for th in rows[0].find_all(["th", "td"])]

            name_col = None
            for i, h in enumerate(headers):
                if any(kw in h for kw in ["team", "club", "name"]):
                    name_col = i
                    break

            # If no header match, assume first text column is the team name
            if name_col is None and len(headers) >= 2:
                name_col = 0

            if name_col is None:
                continue

            for row in rows[1:]:
                cells = row.find_all(["td", "th"])
                if len(cells) <= name_col:
                    continue

                team_name = cells[name_col].get_text(strip=True)
                if not team_name or team_name.lower() in ["team", "club", "name", ""]:
                    continue

                link = cells[name_col].find("a", href=True)
                team_url = urljoin(source_url, link["href"]) if link else ""

                teams.append(ScrapedTeam(
                    name=team_name,
                    website=team_url,
                    source_url=source_url,
                    source_type=self.source_type,
                ))

        return teams

    def _extract_from_lists(self, soup: BeautifulSoup, source_url: str) -> list[ScrapedTeam]:
        """Extract from <ul>/<ol> lists that look like team listings."""
        teams = []

        for ul in soup.find_all(["ul", "ol"]):
            items = ul.find_all("li")
            if len(items) < 3:
                continue

            for li in items:
                text = li.get_text(strip=True)
                if not text or len(text) > 200:
                    continue

                link = li.find("a", href=True)
                team_url = urljoin(source_url, link["href"]) if link else ""
                name = link.get_text(strip=True) if link else text

                if name:
                    teams.append(ScrapedTeam(
                        name=name,
                        website=team_url,
                        source_url=source_url,
                        source_type=self.source_type,
                    ))

        return teams
