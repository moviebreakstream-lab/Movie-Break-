import asyncio
from extractors.vidsrc import VidsrcExtractor
from extractors.gogoanime import GogoAnimeExtractor
from core.tmdb_client import TMDBClient

class MovieBreakEngine:
    def __init__(self):
        self.vidsrc = VidsrcExtractor()
        self.gogo = GogoAnimeExtractor()
        self.tmdb = TMDBClient()

    async def extract_parallel(self, media_list):
        """
        محرك استخراج متوازي فائق السرعة مع معالجة أخطاء ذكية.
        """
        async def process_item(media):
            m_type = media.get("type", "movie")
            m_id = media.get("id")
            
            try:
                if m_type in ["movie", "tv"]:
                    extractor_task = self.vidsrc.get_m3u8(
                        m_id, 
                        is_tv=(m_type == "tv"),
                        season=media.get("season", 1),
                        episode=media.get("episode", 1)
                    )
                    # محاولة جلب بيانات TMDB ولكن لا تدعها تعطل الاستخراج
                    tmdb_task = self.tmdb.get_movie_details(m_id) if m_type == "movie" else self.tmdb.get_tv_details(m_id)
                else: # anime
                    extractor_task = self.gogo.get_m3u8(m_id, episode_num=media.get("episode", 1))
                    tmdb_task = self.tmdb.get_anime_details(m_id)

                ext_res, tmdb_data = await asyncio.gather(extractor_task, tmdb_task, return_exceptions=True)
                
                if ext_res and not isinstance(ext_res, Exception):
                    ext_res["tmdb_data"] = tmdb_data if tmdb_data and not isinstance(tmdb_data, Exception) else None
                    ext_res["type"] = m_type
                    ext_res["id"] = m_id
                    
                    # إذا كان الرابط هو رابط embed، نحاول استخلاص m3u8 منه إذا كان ممكناً
                    # أو على الأقل نوضح أنه رابط بث
                    return ext_res
            except Exception as e:
                print(f"Critical error processing {m_id}: {e}")
            return None

        tasks = [process_item(m) for m in media_list]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]

    def generate_iptv_playlist(self, extracted_data):
        """
        توليد قائمة IPTV احترافية متوافقة مع جميع التطبيقات (VLC, IPTV Smarters, etc.)
        """
        playlist = "#EXTM3U\n"
        for item in extracted_data:
            if not item or not item.get("m3u8_url"):
                continue
            
            title = "Unknown Content"
            poster = ""
            if item.get("tmdb_data"):
                title = item["tmdb_data"].get("title") or item["tmdb_data"].get("name") or title
                p_path = item["tmdb_data"].get("poster_path")
                if p_path:
                    poster = f"https://image.tmdb.org/t/p/w500{p_path}"
            
            quality = item.get("quality", "HD")
            source = item.get("source", "Unknown")
            info = f'#EXTINF:-1 tvg-id="{item.get("id")}" tvg-name="{title}" tvg-logo="{poster}" group-title="{item.get("type").upper()}",{title} [{quality}] ({source})'
            playlist += f"{info}\n{item.get('m3u8_url')}\n"
        
        return playlist
