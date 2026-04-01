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

    def _get_text(self):
        pass

    def _abs_url(self):
        pass

class ScrapeSchedule(ScraperAction):
    def parse_day_wise_schedule(self, soup: BeautifulSoup):
        records = []

        ul = soup.find("ul", id="agenda")
        lis = ul.find_all("li")

        logger.info(f'List item count : {len(lis)}')

        session_date = lis[0].get_text(strip=True)
        
        for li in lis:
            parent_div = li.find("div")

            if not parent_div:
                continue

            child_divs = parent_div.find_all("div", recursive=False)

            if len(child_divs) < 2:
                continue

            span1 = child_divs[0].find("span")
            span2 = child_divs[1].find("span")
            div = child_divs[1].find("div")
            section = child_divs[1].find("section")
            section_div = section.find("div") if section else []
            section_child_divs = section_div.find_all("div") if section_div else []

            session_time = span1.get_text(strip=True) if span1 else None
            session_title = span2.get_text(strip=True) if span2 else None
            location = div.get_text(strip=True) if div else None
            session_location = location.replace("Location: ", "") if location else None
            
            session_speakers = []

            for d in section_child_divs:
                authors_text = d.get_text(strip=True).replace("Speaker:", "")
                authors_text = authors_text.replace("Moderator:", "")
                authors_text = authors_text.replace("Panelist:", "")
                session_speakers.append(authors_text)

            # logger.info(f'Parsed schedule item: {session_date} | {session_time} | {session_title} | {session_location} | {session_speakers}')

            records.append({
                'session_title': session_title,
                'session_type': 'session',
                'poster_abstract_title': '',
                'authors': session_speakers,
                'affiliations': '',
                'date': session_date,
                'time': session_time,
                'location': session_location,
            })

        return records

    def parse_full_schedule_page(self, url: str):
        soup = self._get(url)
        if not soup:
            return []
    
        all_records = []
        container = soup.find("div", id="sitewrap")
        content = container.find("div", class_="content-wrap container")

        ul = content.find("ul")
        lis = ul.find_all("li")[1:]

        for li in lis:
            a_tag = li.find("a", href=True)
            if a_tag:
                full_url = urljoin(BASE_URL, a_tag["href"])
                logger.info(f'FULL URL : {full_url}')

                # individual schedule page
                page = self._get(full_url)
                records = self.parse_day_wise_schedule(page)
                all_records.append(records)

        return all_records

    def execute(self):
        homepage = self._get(INDEX_URL)
        
        scripts = homepage.find_all("script")
        tile_json = None

        for script in scripts:
            if script.string and "TileScreen" in script.string:
                match = re.search(r'TileScreen\([^,]+,\s*(\{.*?\})\s*,', script.string, re.DOTALL)
                if match:
                    tile_json = match.group(1)
                    break

        print("TILE JSON:", tile_json)  # Log first 500 chars of the JSON
        # data = json.loads(tile_json)
        # tiles = data.get("tiles", [])

        # for tile in tiles:
            # print(tile.get("accessibilityLabel"), "->", tile.get("href"))
        
        schedule_url = "https://sgo2026annualmeeting.eventscribe.net/agenda.asp?BCFO=&pfp=Browse%20by%20Day&fa=&fb=&fc=&fd=&all=1"
        all_records = self.parse_full_schedule_page(schedule_url)

        return all_records

class ScrapePoster(ScraperAction):
    def parse_poster_detail(self, soup: BeautifulSoup):
        records = []

        ul = soup.find("ul", id="agenda")
        lis = ul.find_all("li")[1:]

        for li in lis:
            div = li.find("div", class_="prestitle")
            anchor = div.find("a", href=True)
            
            if anchor:
                poster_detail_url = urljoin(BASE_URL, anchor["href"])
                parsed_url = urlparse(poster_detail_url)
                query_params = parse_qs(parsed_url.query)
                poster_id = query_params.get("PosterID", [None])[0]
                poster_detail_page = self._get(poster_detail_url)

                div = poster_detail_page.find("div", id=f"poster-info-{poster_id}")

                h1 = div.find("h1") if div else None
                poster_title = h1.get_text(strip=True) if h1 else None
                location = div.find("div", class_="pres-tidbit") if div else None
                location_text = location.get_text(strip=True) if location else None
                location = location_text.replace("Location: ", "") if location_text else None

                ul = div.find("ul", class_="speakers-wrap") if div else None
                li_items = ul.find_all("li") if ul else []

                speakers = []
                for li_item in li_items:
                    anchor = li_item.find("a", href=True)
                    speaker = anchor.get_text(strip=True) if anchor else None
                    if speaker:
                        speakers.append(speaker)
            
                # logger.info(f'Parsed poster detail for {poster_id}: {poster_title} | {location} | {speakers}')

                records.append({
                    'session_title': poster_title,
                    'session_type': 'poster',
                    'poster_abstract_title': '',
                    'authors': speakers,
                    'affiliations': '',
                    'date': '',
                    'time': '',
                    'location': location,
                })

        return records
    
    def parse_full_poster_page(self, url: str):
        soup = self._get(url)

        all_records = []
        container = soup.find("div", id="sitewrap")
        content = container.find("div", class_="content-wrap container")

        ul = content.find("ul", class_="list-group alphaList clearfix")
        lis = ul.find_all("li")[1:]

        for li in lis[:2]:
            a_tag = li.find("a", href=True)
            if a_tag:
                full_url = urljoin(BASE_URL + "/posters/", a_tag["href"])

                # individual schedule page
                page = self._get(full_url)
                records = self.parse_poster_detail(page)
                all_records.append(records)
                
        return all_records

    def execute(self):
        homepage = self._get(INDEX_URL)

        poster_url = "https://sgo2026annualmeeting.eventscribe.net/posters/browseByPosterTitle.asp?pfp=BrowsebyTitle"
        all_records = self.parse_full_poster_page(poster_url)

        return all_records