import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "")

SOURCES = [
    {"name": "iz_volkswagen", "url": "https://iz.ru/tag/volkswagen", "enabled": True},
    {"name": "motor", "url": "https://motor.ru/", "enabled": True},
    {"name": "drom", "url": "https://news.drom.ru/", "enabled": True},
    {"name": "autopilot", "url": "https://www.autopilot.ru/lenta", "enabled": True},
    {"name": "koreatown", "url": "https://xn----7sbbeeptbfadjdvm5ab9bqj.xn--p1ai/", "enabled": True},
    {"name": "chinatown", "url": "https://chinatownfest.ru/news", "enabled": True},
    {"name": "auto_ru", "url": "https://auto.ru/mag/theme/news/", "enabled": True},
    {"name": "drive", "url": "https://www.drive.ru/", "enabled": True},
    {"name": "kolesa", "url": "https://www.kolesa.ru/news/", "enabled": True},
]

POST_INTERVAL_HOURS = 2

NEWS_PER_SESSION = 3

PROXY = os.getenv("PROXY", "")

DB_PATH = "news.db"