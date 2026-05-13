from config import HIGH_PRIORITY_KEYWORDS, MEDIUM_PRIORITY_KEYWORDS


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
