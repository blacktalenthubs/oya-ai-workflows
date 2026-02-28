"""Base scraper with rate limiting, retries, and shared HTTP session."""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


@dataclass
class ScrapedTeam:
    """Raw team data from any scraper source."""
    name: str
    league: str = ""
    location: str = ""
    email: str = ""
    phone: str = ""
    website: str = ""
    social_facebook: str = ""
    social_instagram: str = ""
    social_twitter: str = ""
    contact_name: str = ""
    contact_role: str = ""
    source_url: str = ""
    source_type: str = ""  # "google_maps", "web", "league_directory"
    raw_data: dict = field(default_factory=dict)


class BaseScraper(ABC):
    """Abstract base scraper with built-in rate limiting and retries."""

    def __init__(
        self,
        requests_per_second: float = 1.0,
        max_retries: int = 3,
        timeout: int = 15,
    ):
        self.min_interval = 1.0 / requests_per_second
        self.timeout = timeout
        self._last_request_time = 0.0

        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        })

    def _rate_limit(self):
        """Enforce minimum interval between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_request_time = time.time()

    def get(self, url: str, **kwargs) -> requests.Response:
        """Rate-limited GET request."""
        self._rate_limit()
        kwargs.setdefault("timeout", self.timeout)
        return self.session.get(url, **kwargs)

    @abstractmethod
    def scrape(self, query: str, **kwargs) -> list[ScrapedTeam]:
        """Run a scrape job and return list of teams found."""
        ...

    @property
    @abstractmethod
    def source_type(self) -> str:
        """Identifier for this scraper source."""
        ...
