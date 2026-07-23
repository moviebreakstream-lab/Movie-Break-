import httpx
import re
import base64
import urllib.parse
from bs4 import BeautifulSoup

class VidsrcExtractor:
    def __init__(self):
        # قائمة بمصادر الـ Embed الأكثر استقراراً لعام 2026
        self.sources = [
            {"name": "Vidsrc.to", "url": "https://vidsrc.to/embed/movie/{id}", "tv_url": "https://vidsrc.to/embed/tv/{id}/{s}/{e}"},
            {"name": "Vidsrc.me", "url": "https://vidsrc.me/embed/movie/{id}", "tv_url": "https://vidsrc.me/embed/tv/{id}/{s}/{e}"},
            {"name": "SuperEmbed", "url": "https://multiembed.mov/?video_id={id}&tmdb=1", "tv_url": "https://multiembed.mov/?video_id={id}&tmdb=1&s={s}&e={e}"},
            {"name": "2Embed", "url": "https://www.2embed.cc/embed/{id}", "tv_url": "https://www.2embed.cc/embedtv/{id}&s={s}&e={e}"},
            {"name": "AutoEmbed", "url": "https://autoembed.to/movie/tmdb/{id}", "tv_url": "https://autoembed.to/tv/tmdb/{id}/{s}/{e}"}
        ]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Referer": "https://google.com"
        }

    async def get_m3u8(self, media_id, is_tv=False, season=1, episode=1):
        """
        محرك استخراج ذكي يجرب مصادر متعددة بالتوازي
        """
        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=10) as client:
            for src in self.sources:
                try:
                    # تجهيز الرابط بناءً على نوع المحتوى
                    if is_tv:
                        url = src["tv_url"].format(id=media_id, s=season, e=episode)
                    else:
                        url = src["url"].format(id=media_id)
                    
                    print(f"Trying source: {src['name']} -> {url}")
                    resp = await client.get(url)
                    if resp.status_code != 200: continue

                    # البحث عن روابط m3u8 في محتوى الصفحة (بما في ذلك النصوص المشفرة بـ Base64)
                    m3u8_url = self._find_m3u8_in_text(resp.text)
                    if m3u8_url:
                        return {"source": src["name"], "m3u8_url": m3u8_url, "quality": "Auto"}

                    # البحث في الـ iframes الموجودة في الصفحة (Recursive Search)
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    iframes = soup.find_all('iframe')
                    for iframe in iframes:
                        iframe_src = iframe.get('src')
                        if not iframe_src: continue
                        if iframe_src.startswith('//'): iframe_src = "https:" + iframe_src
                        
                        # طلب الـ iframe والبحث فيه
                        try:
                            if_resp = await client.get(iframe_src)
                            m3u8_url = self._find_m3u8_in_text(if_resp.text)
                            if m3u8_url:
                                return {"source": f"{src['name']} (Internal)", "m3u8_url": m3u8_url, "quality": "Auto"}
                        except: continue

                except Exception as e:
                    print(f"Error with {src['name']}: {e}")
                    continue
        
        return None

    def _find_m3u8_in_text(self, text):
        # 1. البحث المباشر عن روابط m3u8
        patterns = [
            r'["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
            r'(https?://[^\s"\'<>]+playlist\.m3u8[^\s"\'<>]*)',
            r'(https?://[^\s"\'<>]+master\.m3u8[^\s"\'<>]*)'
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                url = match.group(1).replace("\\/", "/")
                if "playlist.m3u8" in url or "master.m3u8" in url:
                    return url

        # 2. البحث عن روابط مشفرة بـ Base64 قد تحتوي على m3u8
        base64_patterns = r'["\']([a-zA-Z0-9+/]{50,}={0,2})["\']'
        for b64_match in re.finditer(base64_patterns, text):
            try:
                decoded = base64.b64decode(b64_match.group(1)).decode('utf-8', errors='ignore')
                if ".m3u8" in decoded:
                    inner_match = re.search(r'(https?://[^\s"\'<>]+playlist\.m3u8[^\s"\'<>]*)', decoded)
                    if inner_match: return inner_match.group(1)
            except: continue
            
        return None
