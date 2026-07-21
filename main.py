import asyncio
from core.engine import MovieBreakEngine

async def main():
    engine = MovieBreakEngine()
    
    # مثال لبيانات وسائط للاستخراج
    test_media = [
        {"id": "tt0111161", "type": "movie"}, # The Shawshank Redemption
        {"id": "one-piece", "type": "anime", "episode": 1000},
        {"id": "tt0903747", "type": "tv", "season": 1, "episode": 1} # Breaking Bad
    ]
    
    print("جاري استخراج الروابط بالتوازي...")
    results = await engine.extract_parallel(test_media)
    
    playlist = engine.generate_iptv_playlist(results)
    
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write(playlist)
    
    print("تم إنشاء قائمة IPTV بنجاح: playlist.m3u")

if __name__ == "__main__":
    asyncio.run(main())
