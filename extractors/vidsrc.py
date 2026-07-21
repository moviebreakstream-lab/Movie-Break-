import httpx
import re
from bs4 import BeautifulSoup
import asyncio

class VidsrcExtractor:
    def __init__(self):
        self.domains = [
            "https://vidsrc.to", 
            "https://vidsrc.me", 
            "https://vidsrc.net", 
            "https://vidsrc.xyz",
            "https://vidsrc.in",
            "https://vidsrc.pm"
        ]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Referer": "https://vidsrc.to/"
        }

    async def get_m3u8(self, media_id, is_tv=False, season=1, episode=1):
        """
        محاولة الاستخراج من نطاقات متعددة بالتوازي لضمان السرعة والنجاح.
        """
        tasks = []
        for domain in self.domains:
            tasks.append(self._try_extract(domain, media_id, is_tv, season, episode))
        
        results = await asyncio.gather(*tasks)
        # تصفية النتائج الناجحة
        valid_results = [r for r in results if r is not None]
        return valid_results[0] if valid_results else None

    async def _try_extract(self, base_url, media_id, is_tv, season, episode):
        try:
            url = f"{base_url}/embed/tv/{media_id}/{season}/{episode}" if is_tv else f"{base_url}/embed/movie/{media_id}"
            
            async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=12) as client:
                response = await client.get(url)
                if response.status_code != 200:
                    return None
                
                # البحث عن أنماط M3U8 المباشرة
                m3u8_patterns = [
                    r'["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
                    r'(https?://[^\s"\'<>]+playlist\.m3u8[^\s"\'<>]*)',
                    r'(https?://[^\s"\'<>]+master\.m3u8[^\s"\'<>]*)'
                ]
                
                for pattern in m3u8_patterns:
                    match = re.search(pattern, response.text)
                    if match:
                        m3u8_url = match.group(1).replace("\\/", "/")
                        return {
                            "source": f"Vidsrc ({base_url.split('//')[1]})",
                            "m3u8_url": m3u8_url,
                            "subtitles": self.extract_subtitles(response.text),
                            "quality": "Auto"
                        }
                
                # كخيار أخير: استخدام رابط الـ embed نفسه كمصدر فيديو (يدعمه VLC ومعظم مشغلات IPTV)
                return {
                    "source": f"Vidsrc ({base_url.split('//')[1]})",
                    "m3u8_url": url,
                    "subtitles": self.extract_subtitles(response.text),
                    "quality": "Stream-Link"
                }
        except:
            return None

    def extract_subtitles(self, html):
        subs = []
        # استخراج الترجمات بصيغة VTT
        matches = re.findall(r'["\']?file["\']?:\s*["\']([^"\']+\.vtt[^"\']*)["\']\s*,\s*["\']?label["\']?:\s*["\']([^"\']+)["\']', html)
        for file, label in matches:
            subs.append({"url": file.replace("\\/", "/"), "lang": label})
        return subs
