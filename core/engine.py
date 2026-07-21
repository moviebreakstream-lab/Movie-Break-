import asyncio
from extractors.vidsrc import VidsrcExtractor
from extractors.gogoanime import GogoAnimeExtractor

class MovieBreakEngine:
    def __init__(self):
        self.vidsrc = VidsrcExtractor()
        self.gogo = GogoAnimeExtractor()

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
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

    def generate_iptv_playlist(self, extracted_data):
        """
        توليد قائمة IPTV بصيغة M3U.
        """
        playlist = "#EXTM3U\n"
        for item in extracted_data:
            if not item or isinstance(item, Exception):
                continue
            
            playlist += f"#EXTINF:-1, {item.get('source')} - {item.get('quality')}\n"
            playlist += f"{item.get('m3u8_url')}\n"
        
        return playlist
