import feedparser
import re
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


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
            "image_url": _get_image_from_rss(entry),
            "video_url": "",
        }
        if article["title"] and article["link"]:
            articles.append(article)

    # Enrich articles: one HTTP request per article for image + desc + video
    for article in articles:
        need_image = not article["image_url"]
        need_desc = len(article["description"]) < 80
        if need_image or need_desc:
            img, desc, video = _fetch_article_page(article["link"])
            if img and need_image:
                article["image_url"] = img
            if desc and len(desc) > len(article["description"]):
                article["description"] = desc
            if video:
                article["video_url"] = video

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


def _abs_url(src, base=""):
    if not src:
        return None
    src = src.strip()
    if src.startswith("//"):
        src = "https:" + src
    elif src.startswith("/") and base:
        src = urljoin(base, src)
    if not src.startswith(("http://", "https://")):
        return None
    return src


def _get_image_from_rss(entry):
    if hasattr(entry, "enclosures") and entry.enclosures:
        for enc in entry.enclosures:
            kind = enc.get("type", "")
            if kind.startswith("image/"):
                url = _abs_url(enc.get("href") or enc.get("url"))
                if url:
                    return url

    for attr in ("media_content", "media_thumbnail"):
        items = getattr(entry, attr, None)
        if items:
            url = _abs_url(items[0].get("url"))
            if url:
                return url

    return None


def _fetch_article_page(url):
    """One request to get image, description, and video link."""
    if not url:
        return None, None, None
    try:
        headers = {"User-Agent": USER_AGENT}
        resp = requests.get(url, timeout=8, headers=headers)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        base_tag = soup.find("base", href=True)
        base = base_tag["href"] if base_tag else url

        img = _find_image(soup, base)
        desc = _find_description(soup)
        video = _find_video(soup, url)

        return img, desc, video
    except Exception as e:
        print(f"  Page fetch failed ({url[:60]}...): {e}")
        return None, None, None


def _find_image(soup, base):
    meta = soup.find("meta", property="og:image")
    if meta and meta.get("content"):
        return _abs_url(meta["content"], base)

    for cls in ("hero", "cover", "main", "poster", "featured"):
        img = soup.find("img", class_=re.compile(re.escape(cls), re.I))
        if img and img.get("src"):
            return _abs_url(img["src"], base)

    container = soup.find(["article", "main"],
                          class_=re.compile(r"(content|article|post|body)", re.I))
    if container:
        img = container.find("img")
        if img and img.get("src"):
            return _abs_url(img["src"], base)

    img = soup.find("img")
    if img and img.get("src"):
        src = img["src"]
        if "logo" not in src.lower() and "icon" not in src.lower():
            return _abs_url(src, base)

    return None


def _find_description(soup):
    for attr in ({"name": "description"}, {"property": "og:description"}):
        meta = soup.find("meta", attrs=attr)
        if meta and meta.get("content"):
            return _clean_desc(meta["content"])
    return None


def _find_video(soup, page_url):
    text = str(soup)
    patterns = [
        r"(https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+)",
        r"(https?://youtu\.be/[\w-]+)",
        r"(https?://(?:www\.)?youtube\.com/embed/[\w-]+)",
        r"(https?://vk\.com/video-?\d+_\d+)",
        r"(https?://(?:www\.)?rutube\.ru/video/[\w-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            url = match.group(1)
            page_domain = re.search(r"https?://([^/]+)", page_url)
            video_domain = re.search(r"https?://([^/]+)", url)
            if page_domain and video_domain and page_domain.group(1) == video_domain.group(1):
                continue
            return url
    return None
