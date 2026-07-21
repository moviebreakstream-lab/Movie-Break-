import httpx
import re
from bs4 import BeautifulSoup

class GogoAnimeExtractor:
    def __init__(self):
        self.domains = ["https://gogoanime3.co", "https://gogoanime.hu", "https://gogoanime.run"]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }

    async def get_m3u8(self, anime_id, episode_num=1):
        for base_url in self.domains:
            try:
                episode_url = f"{base_url}/{anime_id}-episode-{episode_num}"
                async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=15) as client:
                    response = await client.get(episode_url)
                    if response.status_code != 200:
                        continue
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # البحث عن روابط المشغلات (GogoPlay, Vidstreaming)
                    iframe = soup.find('iframe')
                    if iframe and iframe.get('src'):
                        iframe_url = iframe['src']
                        if iframe_url.startswith('//'):
                            iframe_url = "https:" + iframe_url
                        
                        # استخراج الرابط المباشر إذا كان موجوداً في الصفحة
                        m3u8_match = re.search(r'(https?://[^\s"\'<>]+playlist\.m3u8[^\s"\'<>]*)', response.text)
                        if m3u8_match:
                            return {
                                "source": "GogoAnime (Direct)",
                                "m3u8_url": m3u8_match.group(1),
                                "subtitles": [],
                                "quality": "Auto"
                            }
                        
                        return {
                            "source": "GogoAnime (Embed)",
                            "m3u8_url": iframe_url,
                            "subtitles": [],
                            "quality": "Direct Embed"
                        }
            except Exception as e:
                print(f"Error with {base_url}: {e}")
                continue
        return None
