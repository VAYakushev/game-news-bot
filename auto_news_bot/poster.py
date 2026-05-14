import telebot
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID, PROXY
import logging
import time
import requests
import re
from io import BytesIO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if PROXY:
    import telebot.apihelper
    telebot.apihelper.PROXY = PROXY

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


def download_image(url: str) -> bytes | None:
    urls_to_try = []
    
    url_clean = re.sub(r'/\d+_\d+x\d+', '', url)
    url_clean = re.sub(r'[?&].*$', '', url_clean)
    
    if "_top_pics" in url_clean or "/media/" in url_clean:
        urls_to_try.append(url_clean.replace("/top_pics/", "/top_pics/media/").replace(".jpeg", "_1280x720.jpeg").replace(".jpg", "_1280x720.jpg").replace(".png", "_1280x720.png"))
        urls_to_try.append(url_clean.replace("/top_pics/", "/top_pics/resize/").replace(".jpeg", "_1280.jpeg").replace(".jpg", "_1280.jpg").replace(".png", "_1280.png"))
    
    urls_to_try.append(url_clean)
    urls_to_try.append(url)
    
    for img_url in urls_to_try:
        try:
            resp = requests.get(img_url, timeout=25, headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "image/webp,image/apng,image/*,*/*"
            })
            if resp.status_code == 200 and len(resp.content) > 15000:
                logger.info(f"Image: {img_url[:60]}... ({len(resp.content)} bytes)")
                return resp.content
        except Exception as e:
            logger.warning(f"Download failed: {img_url[:40]}")
    
    return None


def highlight_key_facts(description: str) -> str:
    positive_keywords = [
        "РїСЂРµРјСЊРµСЂР°", "РІРїРµСЂРІС‹Рµ", "РЅРѕРІС‹Р№", "Р·Р°РїСѓСЃРє", "РґРµР±СЋС‚", "РїСЂРµРґСЃС‚Р°РІР»РµРЅ",
        "СЌР»РµРєС‚СЂРѕ", "РіРёР±СЂРёРґ", "Р°РІС‚РѕРЅРѕРјРЅС‹Р№", "СЂРµРєРѕСЂРґ", "РїРѕР±РµРґРёР»", "СѓРЅРёРєР°Р»СЊРЅС‹Р№",
        "РјРѕС‰РЅРѕСЃС‚СЊ", "Р·Р°РїР°СЃ С…РѕРґР°", "Р±С‹СЃС‚СЂР°СЏ Р·Р°СЂСЏРґРєР°", "Р±РµР·РѕРїР°СЃРЅРѕСЃС‚СЊ"
    ]
    
    sentences = description.split(".")
    highlighted = []
    for sent in sentences[:10]:
        sent = sent.strip()
        if not sent:
            continue
        if not sent.endswith("."):
            sent += "."
        for kw in positive_keywords:
            if kw.lower() in sent.lower():
                highlighted.append(f"вњ… {sent}")
                break
        else:
            if len(highlighted) < 3:
                highlighted.append(sent)
    
    return "\n".join(highlighted) if highlighted else description[:600]


def format_single_news(news_item: dict) -> str:
    title = news_item.get("title", "Р‘РµР· РЅР°Р·РІР°РЅРёСЏ")
    description = news_item.get("description", "")
    source = news_item.get("source", "")
    url = news_item.get("url", "")
    
    text = highlight_key_facts(description)
    
    msg = f"рџљ— *{title}*\n\n"
    msg += f"{text}\n\n"
    msg += f"рџ“Ќ {source} | [РџРѕРґСЂРѕР±РЅРµРµ]({url})"
    
    return msg


def post_single_news(news_item: dict) -> bool:
    try:
        image_url = news_item.get("image", "")
        
        if not image_url or len(image_url) < 10:
            logger.info(f"Skipped (no image): {news_item.get('title', '')[:50]}")
            return False
        
        img_data = download_image(image_url)
        if not img_data:
            logger.info(f"Skipped (img download failed): {news_item.get('title', '')[:50]}")
            return False
        
        message = format_single_news(news_item)
        bot.send_photo(TELEGRAM_CHANNEL_ID, img_data, caption=message, parse_mode="Markdown")
        logger.info(f"Posted with image: {news_item.get('title', '')[:50]}")
        
        time.sleep(5)
        return True
    
    except Exception as e:
        logger.error(f"Error posting: {e}")
        return False


def post_news_batch(news_list: list) -> int:
    posted = 0
    for news_item in news_list:
        if post_single_news(news_item):
            posted += 1
    return posted