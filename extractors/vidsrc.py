import asyncio
import httpx
import re
from extractors.megacloud import MegaCloudResolver
from extractors.vidplay import VidPlayResolver

class VidsrcExtractor:
    def __init__(self):
        self.megacloud = MegaCloudResolver()
        self.vidplay = VidPlayResolver()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        }

    async def get_m3u8(self, media_id, is_tv=False, season=1, episode=1):
        """
        محرك الاستخراج المركزي: يجمع بين أقوى المحللات العالمية.
        """
        # 1. روابط الـ Embed الأساسية التي سنبدأ منها
        embed_urls = [
            f"https://vidsrc.to/embed/tv/{media_id}/{season}/{episode}" if is_tv else f"https://vidsrc.to/embed/movie/{media_id}",
            f"https://vidsrc.me/embed/tv?imdb={media_id}&s={season}&e={episode}" if is_tv else f"https://vidsrc.me/embed/movie?imdb={media_id}",
            f"https://vidsrc.net/embed/tv/{media_id}/{season}/{episode}" if is_tv else f"https://vidsrc.net/embed/movie/{media_id}"
        ]

        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=15) as client:
            for url in embed_urls:
                try:
                    resp = await client.get(url)
                    if resp.status_code != 200: continue

                    # البحث عن روابط MegaCloud و VidPlay داخل الصفحة
                    # هذه المصادر هي التي توفر روابط m3u8 الحقيقية
                    mc_match = re.search(r'["\'](https?://megacloud\.tv/embed-2/[^"\']+)["\']', resp.text)
                    vp_match = re.search(r'["\'](https?://vidplay\.online/e/[^"\']+)["\']', resp.text)

                    tasks = []
                    if mc_match:
                        tasks.append(self.megacloud.resolve(mc_match.group(1)))
                    if vp_match:
                        tasks.append(self.vidplay.resolve(vp_match.group(1)))

                    if tasks:
                        results = await asyncio.gather(*tasks)
                        for res in results:
                            if res and isinstance(res, dict) and res.get("m3u8_url"):
                                return res
                            elif res and isinstance(res, list): # MegaCloud قد يعيد قائمة مصادر
                                for s in res:
                                    if s.get("file") and ".m3u8" in s["file"]:
                                        return {"source": "MegaCloud", "m3u8_url": s["file"], "quality": "Auto"}

                except Exception as e:
                    print(f"Central Extractor Error with {url}: {e}")
                    continue

        return None
