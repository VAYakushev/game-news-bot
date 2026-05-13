import os
import json
import sys

import config
from parser import parse_site
from scorer import score_article, is_article_blocked
from vk_poster import VKPoster

DB_PATH = "db.json"


def load_db():
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"published_urls": []}


def save_db(db):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def main():
    token = os.environ.get("VK_TOKEN")
    if not token:
        print("Error: VK_TOKEN environment variable not set")
        sys.exit(1)

    db = load_db()
    published = set(db.get("published_urls", []))

    all_articles = []
    for site in config.SITES:
        articles = parse_site(site)
        print(f"{site['name']}: {len(articles)} articles")
        all_articles.extend(articles)

    # Remove already published AND blocked (movies/series) articles
    new_articles = [a for a in all_articles if a["link"] not in published]
    before = len(new_articles)
    new_articles = [a for a in new_articles if not is_article_blocked(a)]
    blocked_count = before - len(new_articles)
    print(f"New articles: {before}, blocked (movies/series): {blocked_count}")

    for a in new_articles:
        a["score"] = score_article(a)
    new_articles.sort(key=lambda x: x["score"], reverse=True)

    top = new_articles[: config.MAX_POSTS_PER_RUN]
    if not top:
        print("No new articles to post")
        return

    print(f"Top {len(top)} articles to post:")
    for a in top:
        print(f"  [{a['score']}] {a['site']}: {a['title']}")

    poster = VKPoster(token, config.OWNER_ID)
    posted = []

    for article in top:
        try:
            poster.post_article(article)
            posted.append(article["link"])
        except Exception as e:
            print(f"  Failed: {e}")

    published.update(posted)
    save_db({"published_urls": list(published)})
    print(f"Done. Posted {len(posted)} articles. DB has {len(published)} entries.")


if __name__ == "__main__":
    main()
