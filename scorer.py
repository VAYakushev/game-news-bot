from config import (
    HIGH_PRIORITY_KEYWORDS,
    MEDIUM_PRIORITY_KEYWORDS,
    BLOCKED_KEYWORDS,
)


def is_article_blocked(article):
    text = (article["title"] + " " + article["description"]).lower()
    for kw in BLOCKED_KEYWORDS:
        if kw.lower() in text:
            print(f"  Blocked by keyword '{kw}': {article['title'][:60]}...")
            return True
    return False


def score_article(article):
    text = (article["title"] + " " + article["description"]).lower()
    score = 0

    for kw in HIGH_PRIORITY_KEYWORDS:
        if kw.lower() in text:
            score += 2

    for kw in MEDIUM_PRIORITY_KEYWORDS:
        if kw.lower() in text:
            score += 1

    return score
