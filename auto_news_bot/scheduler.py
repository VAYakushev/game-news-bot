import schedule
import time
import logging
from parser import fetch_all_news, enrich_news, score_news
from filter import filter_new_news, deduplicate
from poster import post_news_batch
from db import mark_as_published
from config import POST_INTERVAL_HOURS, NEWS_PER_SESSION

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def job():
    logger.info("Р—Р°РїСѓСЃРє СЃР±РѕСЂР° РЅРѕРІРѕСЃС‚РµР№...")
    
    raw_news = fetch_all_news()
    raw_news = deduplicate(raw_news)
    raw_news = filter_new_news(raw_news)
    
    if not raw_news:
        logger.info("РќРѕРІС‹С… РЅРѕРІРѕСЃС‚РµР№ РЅРµ РЅР°Р№РґРµРЅРѕ")
        return
    
    logger.info(f"РќР°Р№РґРµРЅРѕ {len(raw_news)} РЅРѕРІРѕСЃС‚РµР№, Р·Р°РіСЂСѓР¶Р°СЋ РєРѕРЅС‚РµРЅС‚...")
    enriched = enrich_news(raw_news, limit=15)
    
    scored = score_news(enriched)
    top_news = scored[:NEWS_PER_SESSION]
    
    if top_news:
        logger.info(f"РџСѓР±Р»РёРєСѓСЋ {len(top_news)} Р»СѓС‡С€РёС… РЅРѕРІРѕСЃС‚РµР№")
        posted = post_news_batch(top_news)
        logger.info(f"РћРїСѓР±Р»РёРєРѕРІР°РЅРѕ {posted} РЅРѕРІРѕСЃС‚РµР№")
        
        for item in top_news:
            mark_as_published(item["url"], item.get("title", ""), item.get("source", ""))
    else:
        logger.info("РќРµС‚ РїРѕРґС…РѕРґСЏС‰РёС… РЅРѕРІРѕСЃС‚РµР№ РґР»СЏ РїСѓР±Р»РёРєР°С†РёРё")


def run_scheduler():
    schedule.every(POST_INTERVAL_HOURS).hours.do(job)
    
    logger.info(f"РџР»Р°РЅРёСЂРѕРІС‰РёРє РЅР°СЃС‚СЂРѕРµРЅ: РєР°Р¶РґС‹Рµ {POST_INTERVAL_HOURS} С‡Р°СЃР°")
    job()
    
    while True:
        schedule.run_pending()
        time.sleep(60)