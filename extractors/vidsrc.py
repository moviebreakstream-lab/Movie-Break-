import httpx
import re
from bs4 import BeautifulSoup

class VidsrcExtractor:
    def __init__(self):
        self.domains = ["https://vidsrc.to", "https://vidsrc.me", "https://vidsrc.net", "https://vidsrc.xyz"]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Referer": "https://vidsrc.to/"
        }

    async def get_m3u8(self, media_id, is_tv=False, season=1, episode=1):
        for base_url in self.domains:
            try:
                if is_tv:
                    url = f"{base_url}/embed/tv/{media_id}/{season}/{episode}"
                else:
                    url = f"{base_url}/embed/movie/{media_id}"
                
                async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=10) as client:
                    response = await client.get(url)
                    if response.status_code != 200:
                        continue
                    
                    # محاولة استخراج رابط البث المباشر من السورس
                    m3u8_patterns = [
                        r'(https?://[^\s"\'<>]+playlist\.m3u8[^\s"\'<>]*)',
                        r'(https?://[^\s"\'<>]+master\.m3u8[^\s"\'<>]*)',
                        r'file:\s*["\'](https?://[^"\']+\.m3u8[^"\']*)["\']'
                    ]
                    
                    for pattern in m3u8_patterns:
                        match = re.search(pattern, response.text)
                        if match:
                            return {
                                "source": f"Vidsrc ({base_url.split('//')[1]})",
                                "m3u8_url": match.group(1).replace("\\/", "/"),
                                "subtitles": self.extract_subtitles(response.text),
                                "quality": "Auto"
                            }
                    
                    # إذا لم نجد رابط m3u8 مباشر، نعيد رابط الـ embed ليعمل في المشغلات المتطورة
                    return {
                        "source": f"Vidsrc ({base_url.split('//')[1]})",
                        "m3u8_url": url,
                        "subtitles": self.extract_subtitles(response.text),
                        "quality": "Embed"
                    }
            except Exception as e:
                print(f"Vidsrc Error ({base_url}): {e}")
                continue
        return None

    def extract_subtitles(self, html):
        subs = []
        matches = re.findall(r'["\']?file["\']?:\s*["\']([^"\']+\.vtt[^"\']*)["\']\s*,\s*["\']?label["\']?:\s*["\']([^"\']+)["\']', html)
        for file, label in matches:
            subs.append({"url": file.replace("\\/", "/"), "lang": label})
        return subs
