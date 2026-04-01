from email.mime import text
import json
import logging
import re
import sys
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

BASE_URL = 'https://sgo2026annualmeeting.eventscribe.net/'
INDEX_URL = f'{BASE_URL}index.asp'


HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/122.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': BASE_URL,
}

class ScraperAction:
    def __init__(self):
        pass

    def _get(self, url: str, params: dict = None):
        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=300)
            logger.info(f'Fetched {url} with status code {response.status_code}')
            logger.debug(f'Response content for {url}: {response.text[:500]}')  # Log first 500 chars
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except requests.RequestException as exc:
            logger.warning(f'Attempt failed for {url}: {exc}')

        return None

    def _clean(self, text: str):
        if not text:
            return ''
        
        return re.sub(r'\s+', ' ', text.strip())

    def _safe_text(self, tag):
            return tag.get_text(strip=True) if tag else None
    
    def _abs_url(self):
        pass

    def _extract_content(self, soup):
        container = soup.find("div", id="sitewrap")
        if not container:
            return None

        return container.find("div", class_="content-wrap container")

    def _extract_location(self, container):
        div = container.find("div")
        if not div:
            return None

        text = div.get_text(strip=True)
        return text.replace("Location: ", "")

class ScrapeSchedule(ScraperAction):
    def parse_day_wise_schedule(self, soup: BeautifulSoup):
        if not soup:
            return []

        ul = soup.find("ul", id="agenda")
        if not ul:
            return []

        lis = ul.find_all("li")
        if not lis:
            return []

        records = []
        session_date = lis[0].get_text(strip=True)
        
        for li in lis:
            item = self._parse_schedule_item(li, session_date)
            if item:
                records.append(item)

        return records

    def parse_full_schedule_page(self, url: str):
        soup = self._get(url)
        if not soup:
            return []
    
        all_records = []
        content = self._extract_content(soup)
        if not content:
            return []

        schedule_links = self._extract_schedule_links(content)

        return [
            self.parse_day_wise_schedule(self._get(link))
            for link in schedule_links
            if link
        ]

        return all_records

    def _parse_schedule_item(self, li, session_date):
        parent_div = li.find("div")
        if not parent_div:
            return None

        child_divs = parent_div.find_all("div", recursive=False)
        if len(child_divs) < 2:
            return None

        # Extract basic fields
        session_time = self._safe_text(child_divs[0].find("span"))
        session_title = self._safe_text(child_divs[1].find("span"))
        session_location = self._extract_location(child_divs[1])
        session_speakers = self._extract_speakers(child_divs[1])

        return {
            'session_title': session_title,
            'session_type': 'session',
            'poster_abstract_title': '',
            'authors': session_speakers,
            'affiliations': '',
            'date': session_date,
            'time': session_time,
            'location': session_location,
        }

    def _extract_speakers(self, container):
        section = container.find("section")
        if not section:
            return []

        section_div = section.find("div")
        if not section_div:
            return []

        speakers = []
        for d in section_div.find_all("div"):
            text = self._clean_speaker_text(d.get_text(strip=True))
            if text:
                speakers.append(text)

        return speakers

    def _clean_speaker_text(self, text: str) -> str:
        prefixes = ("Speaker:", "Moderator:", "Panelist:")
        for prefix in prefixes:
            text = text.replace(prefix, "")
        return text.strip()

    def _extract_schedule_links(self, content):
        ul = content.find("ul")
        if not ul:
            return []

        links = []
        for li in ul.find_all("li")[1:]:  # skip first
            a_tag = li.find("a", href=True)
            if not a_tag:
                continue

            full_url = urljoin(BASE_URL, a_tag["href"])
            logger.info(f"FULL URL : {full_url}")
            links.append(full_url)

        return links

    def execute(self):
        schedule_url = "https://sgo2026annualmeeting.eventscribe.net/agenda.asp?BCFO=&pfp=Browse%20by%20Day&fa=&fb=&fc=&fd=&all=1"
        all_records = self.parse_full_schedule_page(schedule_url)

        return all_records

class ScrapePoster(ScraperAction):
    def parse_poster_detail(self, soup: BeautifulSoup):
        if not soup:
            return []

        ul = soup.find("ul", id="agenda")
        if not ul:
            return []

        records = []
        for li in ul.find_all("li")[1:]:
            item = self._parse_poster_item(li)
            if item:
                records.append(item)

        return records

    def _parse_poster_item(self, li):
        title_div = li.find("div", class_="prestitle")
        if not title_div:
            return None

        anchor = title_div.find("a", href=True)
        if not anchor:
            return None

        poster_url = urljoin(BASE_URL, anchor["href"])
        poster_id = self._extract_poster_id(poster_url)

        poster_soup = self._get(poster_url)
        if not poster_soup:
            return None

        return self._extract_poster_details(poster_soup, poster_id)

    def _extract_poster_id(self, url: str):
        parsed = urlparse(url)
        return parse_qs(parsed.query).get("PosterID", [None])[0]

    def _extract_poster_details(self, soup, poster_id):
        container = soup.find("div", id=f"poster-info-{poster_id}")
        if not container:
            return None

        title = self._safe_text(container.find("h1"))
        location = self._extract_location(container)
        speakers = self._extract_speakers_from_ul(container)

        return {
            'session_title': title,
            'session_type': 'poster',
            'poster_abstract_title': '',
            'authors': speakers,
            'affiliations': '',
            'date': '',
            'time': '',
            'location': location,
        }

    def _extract_speakers_from_ul(self, container):
        ul = container.find("ul", class_="speakers-wrap")
        if not ul:
            return []

        speakers = []
        for li in ul.find_all("li"):
            anchor = li.find("a", href=True)
            name = self._safe_text(anchor)
            if name:
                speakers.append(name)

        return speakers
    
    def parse_full_poster_page(self, url: str):
        soup = self._get(url)
        if not soup:
            return []

        content = self._extract_content(soup)
        if not content:
            return []

        ul = content.find("ul", class_="list-group alphaList clearfix")
        if not ul:
            return []

        poster_links = [
            urljoin(BASE_URL + "/posters/", a["href"])
            for li in ul.find_all("li")[1:]
            if (a := li.find("a", href=True))
        ]

        records = []
        for link in poster_links:
            page = self._get(link)
            if not page:
                continue

            records.extend(self.parse_poster_detail(page))

        return records
        return all_records

    def execute(self):
        poster_url = "https://sgo2026annualmeeting.eventscribe.net/posters/browseByPosterTitle.asp?pfp=BrowsebyTitle"
        all_records = self.parse_full_poster_page(poster_url)

        return all_records