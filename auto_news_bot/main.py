from scheduler import run_scheduler
from config import TELEGRAM_BOT_TOKEN

if not TELEGRAM_BOT_TOKEN:
    print("вљ пёЏ Р’РЅРёРјР°РЅРёРµ: TELEGRAM_BOT_TOKEN РЅРµ РЅР°СЃС‚СЂРѕРµРЅ РІ .env С„Р°Р№Р»Рµ")
    print("РЎРѕР·РґР°Р№С‚Рµ .env С„Р°Р№Р» СЃ РІР°С€РёРј С‚РѕРєРµРЅРѕРј Р±РѕС‚Р°")
    exit(1)

if __name__ == "__main__":
    print("Р—Р°РїСѓСЃРє Р±РѕС‚Р° Р°РІС‚РѕРјРѕР±РёР»СЊРЅС‹С… РЅРѕРІРѕСЃС‚РµР№...")
    run_scheduler()