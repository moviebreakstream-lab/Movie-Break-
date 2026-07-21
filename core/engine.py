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
        results = []
        for media in media_list:
            m_type = media.get("type", "movie")
            m_id = media.get("id")
            
            # تحديد المستخرج المناسب
            extractor_task = None
            if m_type in ["movie", "tv"]:
                extractor_task = self.vidsrc.get_m3u8(
                    m_id,
                    is_tv=(m_type == "tv"),
                    season=media.get("season", 1),
                    episode=media.get("episode", 1)
                )
            elif m_type == "anime":
                extractor_task = self.gogo.get_m3u8(
                    m_id,
                    episode_num=media.get("episode", 1)
                )

            # جلب البيانات الوصفية من TMDB بالتوازي
            tmdb_task = None
            if m_type == "movie":
                tmdb_task = self.tmdb.get_movie_details(m_id)
            elif m_type == "tv":
                tmdb_task = self.tmdb.get_tv_details(m_id)
            elif m_type == "anime":
                tmdb_task = self.tmdb.get_anime_details(m_id)

            if extractor_task:
                try:
                    if tmdb_task:
                        ext_res, tmdb_data = await asyncio.gather(extractor_task, tmdb_task, return_exceptions=True)
                    else:
                        ext_res = await extractor_task
                        tmdb_data = None

                    if ext_res and not isinstance(ext_res, Exception):
                        ext_res["tmdb_data"] = tmdb_data if tmdb_data and not isinstance(tmdb_data, Exception) else None
                        ext_res["type"] = m_type
                        ext_res["id"] = m_id
                        results.append(ext_res)
                except Exception as e:
                    print(f"Engine Error for {m_id}: {e}")

        return results

    def generate_iptv_playlist(self, extracted_data):
        playlist = "#EXTM3U\n"
        for item in extracted_data:
            if not item or not item.get("m3u8_url"):
                continue
            
            title = "Unknown"
            if item.get("tmdb_data"):
                title = item["tmdb_data"].get("title") or item["tmdb_data"].get("name") or "Unknown"
            
            # إضافة معلومات إضافية للقائمة
            info = f'#EXTINF:-1 tvg-id="{item.get("id")}" tvg-logo="{item.get("tmdb_data", {}).get("poster_path") if item.get("tmdb_data") else ""}" group-title="{item.get("type")}",{title} ({item.get("source")})'
            playlist += f"{info}\n{item.get('m3u8_url')}\n"
        return playlist
