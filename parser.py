import feedparser
import re
import requests
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
            "image_url": _get_image(entry),
        }
        if article["title"] and article["link"]:
            articles.append(article)

    # Try to enrich articles with images and longer descriptions from the page
    for article in articles:
        need_desc = len(article["description"]) < 80
        need_image = not article["image_url"]
        if need_desc or need_image:
            page_img, page_desc = _fetch_article_details(article["link"])
            if page_img and need_image:
                article["image_url"] = page_img
            if page_desc and need_desc and len(page_desc) > len(article["description"]):
                article["description"] = page_desc

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
        headers = {"User-Agent": USER_AGENT}
        resp = requests.get(url, timeout=8, headers=headers)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        meta = soup.find("meta", property="og:image")
        if meta and meta.get("content"):
            return meta["content"]

        # Try any large image on the page
        img = soup.find("img", {"class": re.compile(r"(hero|cover|main|poster|featured)", re.I)})
        if img and img.get("src"):
            src = img["src"]
            if src.startswith("//"):
                src = "https:" + src
            return src

        # Last resort: first img in article content
        article = soup.find(["article", "main", "div"], class_=re.compile(r"(content|article|post|body)", re.I))
        if article:
            img = article.find("img")
            if img and img.get("src"):
                src = img["src"]
                if src.startswith("//"):
                    src = "https:" + src
                return src
    except Exception:
        pass
    return None


def _fetch_article_details(url):
    """Fetch og:image AND meta description from the article page in one pass."""
    if not url:
        return None, None
    try:
        headers = {"User-Agent": USER_AGENT}
        resp = requests.get(url, timeout=8, headers=headers)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # Image
        img_url = None
        meta = soup.find("meta", property="og:image")
        if meta and meta.get("content"):
            img_url = meta["content"]

        if not img_url:
            img = soup.find("img", class_=re.compile(r"(hero|cover|main|poster|featured)", re.I))
            if img and img.get("src"):
                img_url = img["src"]
                if img_url.startswith("//"):
                    img_url = "https:" + img_url

        if not img_url:
            container = soup.find(["article", "main", "div"], class_=re.compile(r"(content|article|post|body)", re.I))
            if container:
                img = container.find("img")
                if img and img.get("src"):
                    img_url = img["src"]
                    if img_url.startswith("//"):
                        img_url = "https:" + img_url

        # Description
        desc = None
        meta = soup.find("meta", attrs={"name": "description"})
        if meta and meta.get("content"):
            desc = _clean_desc(meta["content"])
        if not desc:
            meta = soup.find("meta", property="og:description")
            if meta and meta.get("content"):
                desc = _clean_desc(meta["content"])

        return img_url, desc
    except Exception:
        return None, None
