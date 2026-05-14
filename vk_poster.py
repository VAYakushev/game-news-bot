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

    def _upload_image(self, image_url, retries=3):
        for attempt in range(retries):
            try:
                img_resp = requests.get(image_url, timeout=15, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                                  "Chrome/120.0.0.0 Safari/537.36"
                })
                img_resp.raise_for_status()
            except Exception as e:
                print(f"    Download failed (attempt {attempt+1}): {e}")
                if attempt == retries - 1:
                    return None
                continue

            try:
                server = self._api("photos.getWallUploadServer", {
                    "group_id": self.group_id
                })
                files = {"photo": ("image.jpg", img_resp.content, "image/jpeg")}
                upload_resp = requests.post(server["upload_url"], files=files)
                
                # Check for empty response
                if not upload_resp.text or not upload_resp.text.strip():
                    print(f"    Empty response (attempt {attempt+1}), retrying...")
                    if attempt == retries - 1:
                        return None
                    continue
                    
                upload = upload_resp.json()

                photo = self._api("photos.saveWallPhoto", {
                    "group_id": self.group_id,
                    "photo": upload["photo"],
                    "hash": upload["hash"],
                    "server": upload["server"],
                })
                return photo[0] if photo else None
            except Exception as e:
                print(f"    Upload failed (attempt {attempt+1}): {e}")
                if attempt == retries - 1:
                    return None
                continue
        return None

    def post_article(self, article):
        text = self._build_text(article)
        params = {
            "owner_id": self.owner_id,
            "from_group": 1,
            "message": text,
        }
        if article.get("image_url"):
            photo = self._upload_image(article["image_url"])
            if photo:
                params["attachments"] = f"photo{photo['owner_id']}_{photo['id']}"
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
