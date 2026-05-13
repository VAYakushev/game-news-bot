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
        img_resp = requests.get(image_url, timeout=10)
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
                    att = f"photo{photo['owner_id']}_{photo['id']}"
                    attachments.append(att)
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
        hashtags = "#игровыеновости #гейминг"
        source = f"Источник: {article['link']}"
        author_line = f"Автор: {article['author']} | {article['site']}"
        title_line = f"\U0001f3ae {article['title']}"

        overhead = (
            len(title_line) + 1 + len(author_line) + 1
            + len(source) + 1 + len(hashtags) + 6
        )
        max_desc = MAX_TEXT_LENGTH - overhead
        if max_desc < 50:
            max_desc = 50

        desc = article["description"]
        if len(desc) > max_desc:
            desc = desc[: max_desc - 3]
            space = desc.rfind(" ")
            if space > 0:
                desc = desc[:space]
            desc += "..."

        return f"{title_line}\n\n{desc}\n\n{author_line}\n{source}\n\n{hashtags}"
