import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging
import time
import re
from config import PROXY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_session():
    session = requests.Session()
    if PROXY:
        session.proxies = {
            "http": PROXY,
            "https": PROXY
        }
    return session

session = get_session()


def get_article_content(url: str) -> Dict:
    try:
        resp = session.get(url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(resp.text, "lxml")
        
        title = soup.find("h1") or soup.find("meta", property="og:title")
        if title:
            title = title.get_text(strip=True) if title.name == "h1" else title.get("content", "")
        else:
            title = ""
        
        image = None
        
        og_image = soup.find("meta", property="og:image")
        if og_image:
            image = og_image.get("content", "")
        
        if not image:
            picture = soup.find("picture")
            if picture:
                source = picture.find("source")
                if source:
                    image = source.get("srcset", "").split()[0] if source.get("srcset") else ""
            
        if not image:
            img = soup.find("img", {"class": lambda x: x and "photo" in str(x).lower()})
            if not img:
                img = soup.find("img", {"data-src": lambda x: x and ("/photo" in str(x) or "/news" in str(x))})
            if not img:
                img = soup.find("img", {"width": lambda x: x and int(x or 0) > 400})
            if img:
                image = img.get("data-src") or img.get("src", "")
        
        description = soup.find("meta", property="og:description") or soup.find("meta", {"name": "description"})
        if description:
            description = description.get("content", "")
        
        if not description or len(description) < 80:
            paragraphs = soup.find_all("p")
            text_parts = []
            for p in paragraphs[:15]:
                text = p.get_text(strip=True)
                if len(text) > 50 and not text.startswith("Р§РёС‚Р°Р№С‚Рµ С‚Р°РєР¶Рµ"):
                    text_parts.append(text)
                if len(" ".join(text_parts)) > 600:
                    break
            if text_parts:
                description = " ".join(text_parts)
        
        return {
            "title": title,
            "description": description[:800] if description else "",
            "image": image,
            "url": url
        }
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return {"title": "", "description": "", "image": "", "url": url}


def parse_iz_volkswagen() -> List[Dict]:
    news = []
    try:
        resp = requests.get("https://iz.ru/tag/volkswagen", headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "lxml")
        articles = soup.select("a[href*='/news/']")[:15]
        seen = set()
        for a in articles:
            href = a.get("href", "")
            if href and href not in seen and "/news/" in href:
                seen.add(href)
                if not href.startswith("http"):
                    href = "https://iz.ru" + href
                news.append({"url": href, "source": "iz.ru"})
        time.sleep(1)
    except Exception as e:
        logger.error(f"Error parsing iz.ru: {e}")
    return news


def parse_autonews() -> List[Dict]:
    news = []
    try:
        resp = requests.get("https://www.autonews.ru/", headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "lxml")
        articles = soup.select("a[data-type='article']") or soup.select("a[href*='/news/']")
        seen = set()
        for a in articles[:15]:
            href = a.get("href", "")
            if href and href not in seen and "/news/" in href:
                seen.add(href)
                if not href.startswith("http"):
                    href = "https://www.autonews.ru" + href
                news.append({"url": href, "source": "autonews.ru"})
        time.sleep(1)
    except Exception as e:
        logger.error(f"Error parsing autonews.ru: {e}")
    return news


def parse_drom() -> List[Dict]:
    news = []
    try:
        resp = session.get("https://news.drom.ru/", headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "lxml")
        articles = soup.select("a[href$='.html']")
        seen = set()
        for a in articles[:20]:
            href = a.get("href", "")
            if href and "news.drom.ru/" in href and "/sign" not in href and href not in seen:
                seen.add(href)
                news.append({"url": href, "source": "drom.ru"})
        time.sleep(1)
    except Exception as e:
        logger.error(f"Error parsing drom.ru: {e}")
    return news


def parse_autopilot() -> List[Dict]:
    news = []
    try:
        resp = requests.get("https://www.autopilot.ru/lenta", headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "lxml")
        articles = soup.select("a[href*='/news/']")[:15]
        seen = set()
        for a in articles:
            href = a.get("href", "")
            if href and href not in seen:
                seen.add(href)
                if not href.startswith("http"):
                    href = "https://www.autopilot.ru" + href
                news.append({"url": href, "source": "autopilot.ru"})
        time.sleep(1)
    except Exception as e:
        logger.error(f"Error parsing autopilot.ru: {e}")
    return news


def parse_auto_ru() -> List[Dict]:
    news = []
    try:
        resp = session.get("https://auto.ru/mag/theme/news/", headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "lxml")
        articles = soup.select("a[href*='/news/']")[:15]
        seen = set()
        for a in articles:
            href = a.get("href", "")
            if href and "auto.ru/news/" in href and href not in seen:
                seen.add(href)
                news.append({"url": href, "source": "auto.ru"})
        time.sleep(1)
    except Exception as e:
        logger.error(f"Error parsing auto.ru: {e}")
    return news


def parse_motor() -> List[Dict]:
    news = []
    try:
        resp = session.get("https://motor.ru/", headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "lxml")
        articles = soup.select("a[href*='/news/']")[:15]
        seen = set()
        for a in articles:
            href = a.get("href", "")
            if href and "/news/" in href and href not in seen:
                seen.add(href)
                if not href.startswith("http"):
                    href = "https://motor.ru" + href
                news.append({"url": href, "source": "motor.ru"})
        time.sleep(1)
    except Exception as e:
        logger.error(f"Error parsing motor.ru: {e}")
    return news


def parse_drive() -> List[Dict]:
    news = []
    try:
        resp = session.get("https://www.drive.ru/", headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "lxml")
        articles = soup.select("a[href*='/news/']")[:15]
        seen = set()
        for a in articles:
            href = a.get("href", "")
            if href and "/news/" in href and href not in seen:
                seen.add(href)
                if not href.startswith("http"):
                    href = "https://www.drive.ru" + href
                news.append({"url": href, "source": "drive.ru"})
        time.sleep(1)
    except Exception as e:
        logger.error(f"Error parsing drive.ru: {e}")
    return news


def parse_kolesa() -> List[Dict]:
    news = []
    try:
        resp = session.get("https://www.kolesa.ru/news/", headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "lxml")
        articles = soup.select("a[href*='/news/']")[:15]
        seen = set()
        for a in articles:
            href = a.get("href", "")
            if href and "/news/" in href and href not in seen:
                seen.add(href)
                if not href.startswith("http"):
                    href = "https://www.kolesa.ru" + href
                news.append({"url": href, "source": "kolesa.ru"})
        time.sleep(1)
    except Exception as e:
        logger.error(f"Error parsing kolesa.ru: {e}")
    return news


def fetch_all_news() -> List[Dict]:
    all_news = []
    for parser in [parse_iz_volkswagen, parse_drom, parse_autopilot, parse_motor, parse_drive, parse_kolesa]:
        try:
            all_news.extend(parser())
        except Exception as e:
            logger.error(f"Parser error: {e}")
    return all_news


def enrich_news(news: List[Dict], limit: int = 10) -> List[Dict]:
    enriched = []
    for item in news[:limit]:
        content = get_article_content(item["url"])
        item.update(content)
        if item.get("title") and item.get("description"):
            enriched.append(item)
        time.sleep(1)
    return enriched


def score_news(news: List[Dict]) -> List[Dict]:
    keywords_positive = [
        "РїСЂРµРјСЊРµСЂР°", "РЅРѕРІС‹Р№", "Р·Р°РїСѓСЃРє", "С‚РµСЃС‚-РґСЂР°Р№РІ", "РѕР±Р·РѕСЂ", "СЂС‹РЅРѕРє", 
        "РїСЂРѕРґР°Р¶Рё", "С†РµРЅР°", "СЌР»РµРєС‚СЂРѕ", "РіРёР±СЂРёРґ", "СЂРѕСЃСЃРёСЏ", "РєРёС‚Р°Р№",
        "С‚РµСЃС‚", "СЃСЂР°РІРЅРµРЅРёРµ", "СЂРµР№С‚РёРЅРі", "РїРѕР±РµРґРёР»", "СѓРЅРёРєР°Р»СЊРЅС‹Р№"
    ]
    keywords_negative = ["СЂРµРєР»Р°РјР°", "РїСЂРѕРјРѕ", "СЃРєРёРґРєР°", "Р°РєС†РёСЏ", "РєСѓРїРёС‚СЊ"]
    
    scored = []
    for item in news:
        score = 0
        text = (item.get("title", "") + " " + item.get("description", "")).lower()
        
        for kw in keywords_positive:
            if kw in text:
                score += 2
        
        for kw in keywords_negative:
            if kw in text:
                score -= 1
        
        if item.get("image"):
            score += 1
        
        title_len = len(item.get("title", ""))
        if 30 < title_len < 150:
            score += 1
        
        scored.append((score, item))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored]