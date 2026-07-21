import asyncio
import os
from fastapi import FastAPI, Response
from dotenv import load_dotenv
from core.engine import MovieBreakEngine
import uvicorn

load_dotenv()

app = FastAPI(title="Movie Break API")
engine = MovieBreakEngine()

# قائمة وسائط افتراضية للتوليد الدوري
DEFAULT_MEDIA = [
    {"id": "tt0111161", "type": "movie"}, # The Shawshank Redemption
    {"id": "one-piece", "type": "anime", "episode": 1100},
    {"id": "tt0903747", "type": "tv", "season": 1, "episode": 1}, # Breaking Bad
    {"id": "tt14715170", "type": "movie"}, # John Wick: Chapter 4
    {"id": "tt0460681", "type": "tv", "season": 1, "episode": 1} # Supernatural
]

@app.get("/")
async def root():
    return {"message": "Movie Break Service is running", "endpoints": ["/playlist.m3u"]}

@app.get("/playlist.m3u")
async def get_playlist():
    if not os.getenv("TMDB_API_KEY"):
        return {"error": "TMDB_API_KEY not set"}
    
    print("Extracting links...")
    results = await engine.extract_parallel(DEFAULT_MEDIA)
    playlist = engine.generate_iptv_playlist(results)
    
    return Response(content=playlist, media_type="application/x-mpegurl")

if __name__ == "__main__":
    # تشغيل السيرفر على البورت المحدد من Render أو 10000 افتراضياً
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
