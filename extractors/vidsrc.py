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
            "https://vidsrc.cc",
            "https://vidsrc.pm",
            "https://vidsrc.in"
        ]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

    async def get_m3u8(self, media_id, is_tv=False, season=1, episode=1):
        """
        محاولة الاستخراج عبر طلبات HTTP المباشرة مع تتبع الـ iframes
        """
        for base_url in self.domains:
            try:
                url = f"{base_url}/embed/tv/{media_id}/{season}/{episode}" if is_tv else f"{base_url}/embed/movie/{media_id}"
                
                async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=15) as client:
                    # 1. طلب الصفحة الرئيسية للمشغل
                    resp = await client.get(url)
                    if resp.status_code != 200:
                        continue
                    
                    # 2. البحث عن روابط M3U8 صريحة في الصفحة
                    m3u8_patterns = [
                        r'["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
                        r'(https?://[^\s"\'<>]+playlist\.m3u8[^\s"\'<>]*)'
                    ]
                    for pattern in m3u8_patterns:
                        match = re.search(pattern, resp.text)
                        if match:
                            m3u8_url = match.group(1).replace("\\/", "/")
                            return {"source": f"Vidsrc ({base_url.split('//')[1]})", "m3u8_url": m3u8_url, "subtitles": self.extract_subtitles(resp.text)}

                    # 3. محاكاة طلبات AJAX لفك تشفير Vidsrc (المنطق الجديد)
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    rcp_iframe = soup.find('iframe', id='player_iframe')
                    if rcp_iframe and rcp_iframe.get('src'):
                        iframe_src = rcp_iframe.get('src')
                        if iframe_src.startswith('//'): iframe_src = "https:" + iframe_src
                        
                        # تتبع الـ iframe الداخلي
                        client.headers.update({"Referer": url})
                        iframe_resp = await client.get(iframe_src)
                        
                        for pattern in m3u8_patterns:
                            match = re.search(pattern, iframe_resp.text)
                            if match:
                                return {"source": "Vidsrc Stream", "m3u8_url": match.group(1).replace("\\/", "/"), "subtitles": self.extract_subtitles(iframe_resp.text)}

            except Exception as e:
                print(f"Error extracting from {base_url}: {e}")
                continue
        
        return None

    def extract_subtitles(self, html):
        subs = []
        matches = re.findall(r'["\']?file["\']?:\s*["\']([^"\']+\.vtt[^"\']*)["\']\s*,\s*["\']?label["\']?:\s*["\']([^"\']+)["\']', html)
        for file, label in matches:
            subs.append({"url": file.replace("\\/", "/"), "lang": label})
        return subs
