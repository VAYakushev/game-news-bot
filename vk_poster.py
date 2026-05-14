import requests
from config import MAX_TEXT_LENGTH

VK_API_URL = "https://api.vk.com/method"
API_VERSION = "5.131"


class VKPoster:
    def __init__(self, token, owner_id):
        self.token = token
        self.owner_id = owner_id
        self.group_id = abs(owner_id)

    def _api(self, method, params=None):
        if params is None:
            params = {}
        params["access_token"] = self.token
        params["v"] = API_VERSION
        resp = requests.post(f"{VK_API_URL}/{method}", data=params)
        data = resp.json()
        if "error" in data:
            raise Exception(
                f"VK API error [{data['error']['error_code']}]: "
                f"{data['error']['error_msg']}"
            )
        return data.get("response")

    def post_article(self, article):
        text = self._build_text(article)
        params = {
            "owner_id": self.owner_id,
            "from_group": 1,
            "message": text,
        }
        if article.get("link"):
            params["attachments"] = article["link"]
        self._api("wall.post", params)
        print(f"  Posted: {article['title']}")

    def _build_text(self, article):
        title = f"\U0001f3ae {article['title']}"
        desc = article["description"]
        author = f"Автор: {article['author']} | {article['site']}"
        source = article["link"]
        tags = "#игровыеновости #гейминг"

        lines = [title, "", desc, "", author, source, "", tags]

        if article.get("video_url"):
            video_line = f"Видео: {article['video_url']}"
            lines.insert(-1, video_line)

        text = "\n".join(lines)

        if len(text) <= MAX_TEXT_LENGTH:
            return text

        max_desc = len(desc) - (len(text) - MAX_TEXT_LENGTH) - 3
        if max_desc < 50:
            max_desc = 50

        desc = desc[:max_desc]
        space = desc.rfind(" ")
        if space > 0:
            desc = desc[:space]
        desc += "..."
        lines[2] = desc
        return "\n".join(lines)
