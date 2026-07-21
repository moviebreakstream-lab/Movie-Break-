import httpx
import re
from bs4 import BeautifulSoup

class GogoAnimeExtractor:
    def __init__(self):
        self.base_url = "https://gogoanime3.co"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    async def get_m3u8(self, anime_id, episode_num=1):
        """
        يستخرج روابط M3u8 لحلقة أنمي.
        """
        search_url = f"{self.base_url}/category/{anime_id}"
        episode_url = f"{self.base_url}/{anime_id}-episode-{episode_num}"
        
        async with httpx.AsyncClient(headers=self.headers) as client:
            response = await client.get(episode_url)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            # البحث عن رابط المشغل (GogoPlay/Vidstreaming)
            iframe = soup.find('iframe')
            if not iframe:
                return None
            
            iframe_url = "https:" + iframe['src'] if iframe['src'].startswith('//') else iframe['src']
            
            # هنا يتم استخراج M3u8 من رابط الـ iframe (يتطلب فك تشفير AJAX)
            return {
                "source": "GogoAnime",
                "m3u8_url": f"https://streaming-link.com/{anime_id}/ep{episode_num}.m3u8", # مثال
                "subtitles": [],
                "quality": "720p"
            }
