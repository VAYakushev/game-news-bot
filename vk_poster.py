import requests
import os
import json as json_lib
import re
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
        
        # Clean description from HTML
        desc = article.get("description", "")
        desc = re.sub(r"<[^>]+>", "", desc)
        desc = re.sub(r"\s+", " ", desc).strip()
        
        # Add intro
        intro = ""
        if not desc:
            desc = "Подробности читайте по ссылке."
        
        author = f"Автор: {article['author']} | {article['site']}"
        source = article["link"]
        tags = "#игровыеновости #гейминг"

        lines = [title, "", desc, "", author, "", source, "", tags]

        if article.get("video_url"):
            video_line = f"Видео: {article['video_url']}"
            lines.insert(-1, video_line)

        text = "\n".join(lines)

        if len(text) <= MAX_TEXT_LENGTH:
            return text

        # Cut at sentence end for better readability
        max_desc = len(desc) - (len(text) - MAX_TEXT_LENGTH) - 3
        if max_desc < 100:
            max_desc = 100

        desc = desc[:max_desc]
        for punct in [". ", "! ", "? "]:
            last_punct = desc.rfind(punct)
            if last_punct > max_desc * 0.7:
                desc = desc[:last_punct + 1]
                break
        else:
            space = desc.rfind(" ")
            if space > 0:
                desc = desc[:space]
        desc += "..."
        lines[3] = desc
        return "\n".join(lines)


    def rewrite_with_llm(self, title, description):
        """Rewrite description using LLM via OpenRouter API"""
        api_key = os.environ.get("OPENROUTER_API_KEY")
        print(f"    API key exists: {bool(api_key)}")
        if not api_key:
            print("    No API key, skipping LLM")
            return description

        prompt = f"Convert these facts into a flowing Russian paragraph about gaming news. Title: {title}. Facts: {description}. Write 3-4 connected sentences, use transitions, do NOT list facts with commas."

        try:
            print(f"    Calling OpenRouter API...")
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/VAYakushev/game-news-bot",
                    "X-Title": "Game News Bot"
                },
                json={
                    "model": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
                    "messages": [
                        {"role": "system", "content": "Write flowing paragraphs, not bullet points."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 1000
                },
                timeout=30
            )
            print(f"    API status: {resp.status_code}")
            result = resp.json()
            print(f"    API response keys: {list(result.keys())}")
            choices = result.get("choices", [])
            if choices and len(choices) > 0:
                message = choices[0].get("message", {})
                llm_text = message.get("content") or message.get("reasoning") or ""
                if llm_text:
                    llm_text = str(llm_text).strip()
                    print(f"    LLM response: {len(llm_text)} chars")
                    print(f"    LLM text: {llm_text[:200]}")
                    if len(llm_text) > 20:
                        return llm_text
                else:
                    print(f"    No content or reasoning in response")
            else:
                print(f"    No choices in response")
            return description
        except Exception as e:
            print(f"    LLM FAILED: {type(e).__name__}: {e}")
            return description
        
        prompt = f"""Перепиши описание новости для VK-поста. Заголовок: {title}. Описание: {description}. Напиши 3-4 предложения связным текстом с переходами (например, также, при этом, кроме того). НЕ перечисляй факты через запятую. Без эмодзи, на русском."""
        
        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/VAYakushev/game-news-bot",
                    "X-Title": "Game News Bot"
                },
                json={
                    "model": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
                    "messages": [
                        {"role": "system", "content": "Ты — редактор новостного канала про игры. Пишешь тексты на русском языке."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 1000
                },
                timeout=30
            )
            result = resp.json()
            llm_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"    LLM response length: {len(llm_text)} chars")
            print(f"    LLM first 150: {llm_text[:150]}")
            if llm_text and len(llm_text) > 30:
                return llm_text
            print("    LLM returned empty, using original")
            return description
        except Exception as e:
            print(f"    LLM rewrite failed: {e}")
            return description
