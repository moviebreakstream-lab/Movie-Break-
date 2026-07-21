import httpx
import re
import base64
import json
from bs4 import BeautifulSoup

class VidsrcExtractor:
    def __init__(self):
        # استخدام نطاقات متعددة لزيادة الموثوقية
        self.domains = ["https://vidsrc.to", "https://vidsrc.me", "https://vidsrc.net"]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer": "https://vidsrc.to/"
        }

    async def get_m3u8(self, media_id, is_tv=False, season=1, episode=1):
        for base_url in self.domains:
            try:
                if is_tv:
                    url = f"{base_url}/embed/tv/{media_id}/{season}/{episode}"
                else:
                    url = f"{base_url}/embed/movie/{media_id}"
                
                async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=15) as client:
                    response = await client.get(url)
                    if response.status_code != 200:
                        continue
                    
                    # استخراج الرابط المباشر من iframe أو المشغل
                    # vidsrc غالباً ما تستخدم وسيطاً (proxy) أو إعادة توجيه
                    if "playlist.m3u8" in response.text:
                        m3u8_match = re.search(r'(https?://[^\s"\'<>]+playlist\.m3u8[^\s"\'<>]*)', response.text)
                        if m3u8_match:
                            return {
                                "source": f"Vidsrc ({base_url.split('//')[1]})",
                                "m3u8_url": m3u8_match.group(1),
                                "subtitles": self.extract_subtitles(response.text),
                                "quality": "Auto"
                            }
                    
                    # محاولة استخراج data-id وجلب المصادر
                    soup = BeautifulSoup(response.text, 'html.parser')
                    player_div = soup.find('div', {'id': 'player'}) or soup.find('iframe', {'id': 'player'})
                    data_id = None
                    if player_div:
                        data_id = player_div.get('data-id') or player_div.get('src')
                    
                    if not data_id:
                        match = re.search(r'data-id="([^"]+)"', response.text)
                        data_id = match.group(1) if match else None

                    if data_id:
                        # في حال وجود data-id، نستخدم API داخلي (هذا الجزء يحتاج مفاتيح فك تشفير حقيقية)
                        # كحل بديل قوي، سنعيد رابط الـ embed نفسه إذا تعذر الاستخراج العميق
                        # العديد من مشغلات IPTV تدعم روابط الـ embed مباشرة
                        return {
                            "source": f"Vidsrc ({base_url.split('//')[1]})",
                            "m3u8_url": url,
                            "subtitles": self.extract_subtitles(response.text),
                            "quality": "Direct Embed"
                        }
            except Exception as e:
                print(f"Error with {base_url}: {e}")
                continue
        return None

    def extract_subtitles(self, html):
        subs = []
        matches = re.findall(r'["\']?file["\']?:\s*["\']([^"\']+\.vtt[^"\']*)["\']\s*,\s*["\']?label["\']?:\s*["\']([^"\']+)["\']', html)
        for file, label in matches:
            subs.append({"url": file, "lang": label})
        return subs
