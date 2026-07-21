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
        يستخرج الروابط لعدة وسائط بشكل متوازٍ.
        media_list: قائمة من القواميس تحتوي على (id, type, etc.)
        """
        tasks = []
        for media in media_list:
            if media['type'] == 'movie' or media['type'] == 'tv':
                tasks.append(self.vidsrc.get_m3u8(
                    media['id'], 
                    is_tv=(media['type'] == 'tv'),
                    season=media.get('season', 1),
                    episode=media.get('episode', 1)
                ))
            elif media['type'] == 'anime':
                tasks.append(self.gogo.get_m3u8(
                    media['id'],
                    episode_num=media.get('episode', 1)
                ))
        
        results = []
        for media in media_list:
            extractor_task = None
            if media["type"] == "movie" or media["type"] == "tv":
                extractor_task = self.vidsrc.get_m3u8(
                    media["id"],
                    is_tv=(media["type"] == "tv"),
                    season=media.get("season", 1),
                    episode=media.get("episode", 1)
                )
            elif media["type"] == "anime":
                extractor_task = self.gogo.get_m3u8(
                    media["id"],
                    episode_num=media.get("episode", 1)
                )

            tmdb_task = None
            if media["type"] == "movie":
                tmdb_task = self.tmdb.get_movie_details(media["id"])
            elif media["type"] == "tv":
                tmdb_task = self.tmdb.get_tv_details(media["id"])
            elif media["type"] == "anime":
                tmdb_task = self.tmdb.get_anime_details(media["id"])

            if extractor_task and tmdb_task:
                extractor_result, tmdb_data = await asyncio.gather(extractor_task, tmdb_task, return_exceptions=True)
                if extractor_result and not isinstance(extractor_result, Exception):
                    extractor_result["tmdb_data"] = tmdb_data if not isinstance(tmdb_data, Exception) else None
                    extractor_result["type"] = media["type"]
                    extractor_result["id"] = media["id"]
                    results.append(extractor_result)
                else:
                    print(f"فشل الاستخراج لـ {media.get(\'id\')}")
            elif extractor_task:
                extractor_result = await extractor_task
                if not isinstance(extractor_result, Exception):
                    extractor_result["type"] = media["type"]
                    extractor_result["id"] = media["id"]
                    results.append(extractor_result)
                else:
                    print(f"Error extracting from {media.get(\'source\')}: {extractor_result}")

        return results
        return results

    def generate_iptv_playlist(self, extracted_data):
        """
        توليد قائمة IPTV بصيغة M3U.
        """
        playlist = "#EXTM3U\n"
        for item in extracted_data:
            if not item or isinstance(item, Exception):
                continue
            
            title = "غير معروف"
            if item.get("tmdb_data"):
                if item["type"] == "movie":
                    title = item["tmdb_data"].get("title", "غير معروف")
                elif item["type"] == "tv":
                    title = item["tmdb_data"].get("name", "غير معروف")
                elif item["type"] == "anime":
                    title = item["tmdb_data"].get("name", "غير معروف")

            playlist += f"#EXTINF:-1 tvg-id=\"{item.get(\'id\')}\" tvg-name=\"{title}\" group-title=\"{item.get(\'type\')}\",{title} - {item.get(\'source\')} - {item.get(\'quality\')}\n"
            playlist += f"{item.get('m3u8_url')}\n"
        
        return playlist
