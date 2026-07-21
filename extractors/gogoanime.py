import httpx
import re
import asyncio
from bs4 import BeautifulSoup

class GogoAnimeExtractor:
    def __init__(self):
        self.domains = [
            "https://gogoanime3.co", 
            "https://gogoanime.hu", 
            "https://gogoanime.run",
            "https://gogoanime.so",
            "https://anitaku.to"
        ]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        }

    async def get_m3u8(self, anime_id, episode_num=1):
        tasks = []
        for domain in self.domains:
            tasks.append(self._try_extract(domain, anime_id, episode_num))
        
        results = await asyncio.gather(*tasks)
        valid_results = [r for r in results if r is not None]
        return valid_results[0] if valid_results else None

    async def _try_extract(self, base_url, anime_id, episode_num):
        try:
            url = f"{base_url}/{anime_id}-episode-{episode_num}"
            async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=12) as client:
                response = await client.get(url)
                if response.status_code != 200:
                    return None
                
                soup = BeautifulSoup(response.text, 'html.parser')
                iframe = soup.find('iframe')
                if iframe and iframe.get('src'):
                    iframe_url = iframe['src']
                    if iframe_url.startswith('//'):
                        iframe_url = "https:" + iframe_url
                    
                    # البحث عن روابط M3U8 مباشرة في محتوى الصفحة أو الـ iframe
                    m3u8_match = re.search(r'["\'](https?://[^"\']+\.m3u8[^"\']*)["\']', response.text)
                    if m3u8_match:
                        return {
                            "source": "GogoAnime (Direct)",
                            "m3u8_url": m3u8_match.group(1).replace("\\/", "/"),
                            "subtitles": [],
                            "quality": "Auto"
                        }
                    
                    return {
                        "source": "GogoAnime (Stream)",
                        "m3u8_url": iframe_url,
                        "subtitles": [],
                        "quality": "720p/1080p"
                    }
        except:
            return None
