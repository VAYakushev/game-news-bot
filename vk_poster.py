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

    def _upload_image(self, image_url):
        img_resp = requests.get(image_url, timeout=15)
        img_resp.raise_for_status()
        img_data = img_resp.content

        server = self._api("photos.getWallUploadServer", {
            "group_id": self.group_id
        })

        files = {"photo": ("image.jpg", img_data, "image/jpeg")}
        upload = requests.post(server["upload_url"], files=files).json()

        photo = self._api("photos.saveWallPhoto", {
            "group_id": self.group_id,
            "photo": upload["photo"],
            "hash": upload["hash"],
            "server": upload["server"],
        })
        return photo[0] if photo else None

    def post_article(self, article):
        text = self._build_text(article)
        attachments = []

        if article.get("image_url"):
            try:
                photo = self._upload_image(article["image_url"])
                if photo:
                    attachments.append(
                        f"photo{photo['owner_id']}_{photo['id']}"
                    )
            except Exception as e:
                print(f"  Image upload failed: {e}")

        self._api("wall.post", {
            "owner_id": self.owner_id,
            "from_group": 1,
            "message": text,
            "attachments": ",".join(attachments) if attachments else "",
        })
        print(f"  Posted: {article['title']}")

    def _build_text(self, article):
        title = f"\U0001f3ae {article['title']}"
        desc = article["description"]
        author = f"Автор: {article['author']} | {article['site']}"
        source = f"Источник: {article['link']}"
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
