import feedparser
import re
import requests
from bs4 import BeautifulSoup


def parse_site(site_config):
    try:
        feed = feedparser.parse(site_config["rss_url"])
    except Exception as e:
        print(f"  Error parsing {site_config['name']}: {e}")
        return []

    articles = []
    for entry in feed.entries[:15]:
        article = {
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "description": _clean_desc(
                entry.get("description", "") or entry.get("summary", "")
            ),
            "author": _get_author(entry),
            "site": site_config["name"],
            "image_url": _get_image(entry),
        }
        if article["title"] and article["link"]:
            articles.append(article)

    return articles


def _clean_desc(text):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _get_author(entry):
    for field in ("author", "dc_creator"):
        val = getattr(entry, field, None)
        if val:
            return val
    return "Редакция"


def _get_image(entry):
    if hasattr(entry, "enclosures") and entry.enclosures:
        for enc in entry.enclosures:
            kind = enc.get("type", "")
            if kind.startswith("image/"):
                return enc.get("href") or enc.get("url")

    for attr in ("media_content", "media_thumbnail"):
        items = getattr(entry, attr, None)
        if items:
            url = items[0].get("url")
            if url:
                return url

    return _fetch_og_image(entry.get("link", ""))


def _fetch_og_image(url):
    if not url:
        return None
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; GameNewsBot/1.0)"}
        resp = requests.get(url, timeout=5, headers=headers)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        meta = soup.find("meta", property="og:image")
        if meta and meta.get("content"):
            return meta["content"]
    except Exception:
        pass
    return None
