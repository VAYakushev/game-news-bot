import os
import requests
from config import MAX_TEXT_LENGTH

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

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
        try:
            img_resp = requests.get(image_url, timeout=15, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/120.0.0.0 Safari/537.36"
            })
            img_resp.raise_for_status()
        except Exception as e:
            print(f"    Download failed: {e}")
            return None

        try:
            server = self._api("photos.getWallUploadServer", {
                "group_id": self.group_id
            })
            files = {"photo": ("image.jpg", img_resp.content, "image/jpeg")}
            upload_resp = requests.post(server["upload_url"], files=files)
            upload = upload_resp.json()

            photo = self._api("photos.saveWallPhoto", {
                "group_id": self.group_id,
                "photo": upload["photo"],
                "hash": upload["hash"],
                "server": upload["server"],
            })
            return photo[0] if photo else None
        except Exception as e:
            print(f"    Upload failed: {e}")
            return None

    def rewrite_with_llm(self, article):
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            print("  OPENROUTER_API_KEY not set, skipping LLM rewrite")
            return article["description"]

        title = article["title"]
        desc = article["description"]
        if len(desc) < 100:
            print(f"  Description too short ({len(desc)} chars), skipping LLM")
            return desc

        prompt = (
            "Convert these facts into a flowing Russian paragraph about gaming news.\n"
            f"Title: {title}\n"
            f"Facts: {desc}\n\n"
            "Write 3-4 connected sentences in Russian. "
            "Use natural Russian transitions between sentences. "
            "Do NOT list facts separated by commas. Do NOT use bullet points. "
            "Do NOT include the title in your response - it will be added separately. "
            "Output ONLY the paragraph text in Russian, nothing else."
        )

        for attempt in range(3):
            try:
                resp = requests.post(
                    OPENROUTER_API_URL,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "HTTP-Referer": "https://github.com/VAYakushev/game-news-bot",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "meta-llama/llama-3.1-8b-instruct:free",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 1500,
                        "temperature": 0.7,
                    },
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()
                choice = data["choices"][0]
                message = choice["message"]
                finish = choice.get("finish_reason", "")
                content = message.get("content") or ""
                content = content.strip()
                if content:
                    print(f"  LLM rewrite done (finish={finish}, {len(content)} chars)")
                    return content
                else:
                    print(f"  LLM returned empty (finish={finish}), retrying...")
            except Exception as e:
                print(f"  LLM attempt {attempt+1} failed: {e}")

        print("  LLM rewrite failed, using original description")
        return desc

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
        author = f"РђРІС‚РѕСЂ: {article['author']} | {article['site']}"
        link = article["link"]
        tags = "#РёРіСЂРѕРІС‹РµРЅРѕРІРѕСЃС‚Рё #РіРµР№РјРёРЅРі"

        lines = [title, "", desc, "", author, "", link, "", tags]

        if article.get("video_url"):
            lines.append(f"Р’РёРґРµРѕ: {article['video_url']}")

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
