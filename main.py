import asyncio
import os
from dotenv import load_dotenv

load_dotenv()
from core.engine import MovieBreakEngine

async def main():
    engine = MovieBreakEngine()
    
    # قائمة وسائط حقيقية للاختبار
    test_media = [
        {"id": "tt0111161", "type": "movie"}, # The Shawshank Redemption
        {"id": "one-piece", "type": "anime", "episode": 1100},
        {"id": "tt0903747", "type": "tv", "season": 1, "episode": 1}, # Breaking Bad
        {"id": "tt14715170", "type": "movie"}, # John Wick: Chapter 4
        {"id": "tt0460681", "type": "tv", "season": 1, "episode": 1} # Supernatural
    ]
    
    # تأكد من تعيين TMDB_API_KEY في ملف .env أو كمتغير بيئة
    if not os.getenv("TMDB_API_KEY"):
        print("خطأ: لم يتم تعيين متغير البيئة TMDB_API_KEY. يرجى إضافته.")
        return
    
    print("جاري استخراج الروابط بالتوازي...")
    results = await engine.extract_parallel(test_media)
    
    playlist = engine.generate_iptv_playlist(results)
    
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write(playlist)
    
    print("تم إنشاء قائمة IPTV بنجاح: playlist.m3u")

if __name__ == "__main__":
    asyncio.run(main())
