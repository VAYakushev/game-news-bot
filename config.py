SITES = [
    {
        "name": "StopGame",
        "rss_url": "https://stopgame.ru/rss/news.xml",
    },
    {
        "name": "DTF",
        "rss_url": "https://dtf.ru/rss",
    },
    {
        "name": "Igromania",
        "rss_url": "https://www.igromania.ru/rss/",
    },
    {
        "name": "Cybersport",
        "rss_url": "https://www.cybersport.ru/rss/",
    },
    {
        "name": "Kanobu",
        "rss_url": "https://kanobu.ru/rss/",
    },
]

BLOCKED_KEYWORDS = [
    "фильм", "сериал", "кино", "кинотеатр", "кинематограф", "кинопремьера",
    "movie", "series", "tv series", "tv show", "netflix",
    "hbo", "disney+", "kinopoisk", "кдп", "кпоп",
]

HIGH_PRIORITY_KEYWORDS = [
    "релиз", "вышел", "доступен", "запуск",
    "анонс", "анонсировал", "анонсировала", "представила",
    "скидка", "раздача", "бесплатно", "халява",
    "playstation", "xbox", "nintendo", "steam",
    "gta", "cyberpunk", "elden ring", "god of war",
    "the witcher", "call of duty", "battlefield",
    "starfield", "zelda", "mario", "halo",
    "серия", "сиквел", "продолжение",
]

MEDIUM_PRIORITY_KEYWORDS = [
    "трейлер", "геймплей", "gameplay",
    "обновление", "патч", "update",
    "дата выхода", "выйдет",
    "киберспорт", "major", "турнир",
    "dlc", "дополнение", "сезон",
    "скин", "кроссовер", "коллаборация",
    "steam deck", "switch", "ps5", "xbox series",
    "unreal engine", "движок",
    "шутер", "rpg", "экшен", "стратегия",
    "инди", "независимая",
]

OWNER_ID = -238677682
MAX_POSTS_PER_RUN = 1
MAX_TEXT_LENGTH = 1000
