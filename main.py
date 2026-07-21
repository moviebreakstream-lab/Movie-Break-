import asyncio
import os
import re
from fastapi import FastAPI, Response, Query, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from core.engine import MovieBreakEngine
import uvicorn

load_dotenv()

app = FastAPI(title="Movie Break Professional API")
engine = MovieBreakEngine()

def parse_url(url: str):
    """
    تحليل رابط الفيلم أو المسلسل لاستخراج النوع والـ ID.
    يدعم روابط IMDb و روابط مشهورة أخرى.
    """
    # IMDb Pattern: tt1234567
    imdb_match = re.search(r'tt\d+', url)
    if imdb_match:
        media_id = imdb_match.group(0)
        if "/tv/" in url or "episodes" in url:
            return media_id, "tv"
        return media_id, "movie"
    
    # GogoAnime Pattern
    if "gogoanime" in url:
        anime_id = url.split("/")[-1].replace("-episode-", "").split("?")[0]
        # محاولة استخراج رقم الحلقة إذا وجد
        ep_match = re.search(r'episode-(\d+)', url)
        episode = int(ep_match.group(1)) if ep_match else 1
        return anime_id, "anime", episode

    return None, None

@app.get("/")
async def root():
    return {
        "status": "Movie Break API is Active",
        "endpoints": {
            "/extract": "استخراج روابط M3u8 من رابط URL مباشر",
            "/playlist.m3u": "توليد قائمة IPTV مخصصة",
            "/search": "البحث عن فيلم أو مسلسل وجلب روابطه"
        },
        "usage": {
            "extract_example": "/extract?url=https://www.imdb.com/title/tt0111161/",
            "playlist_example": "/playlist.m3u?ids=tt0111161,tt0903747"
        }
    }

@app.get("/extract")
async def extract(url: str = Query(..., description="رابط الفيلم أو المسلسل أو الأنمي")):
    media_id, media_type, *extra = parse_url(url)
    if not media_id:
        # إذا لم يكن رابطاً معروفاً، نفترض أنه ID مباشر
        media_id = url
        media_type = "movie" # افتراضي

    episode = extra[0] if extra else 1
    
    media_item = {"id": media_id, "type": media_type, "episode": episode}
    results = await engine.extract_parallel([media_item])
    
    if not results:
        raise HTTPException(status_code=404, detail="تعذر استخراج الروابط من هذا المصدر")
    
    return JSONResponse(content=results[0])

@app.get("/playlist.m3u")
async def get_playlist(ids: str = Query(None, description="قائمة IMDb IDs مفصولة بفاصلة")):
    media_list = []
    if ids:
        id_list = ids.split(",")
        for mid in id_list:
            media_list.append({"id": mid.strip(), "type": "tv" if "tv" in mid else "movie"})
    else:
        # وسائط افتراضية إذا لم يتم تحديد IDs
        media_list = [
            {"id": "tt0111161", "type": "movie"},
            {"id": "tt0903747", "type": "tv", "season": 1, "episode": 1}
        ]
    
    results = await engine.extract_parallel(media_list)
    playlist = engine.generate_iptv_playlist(results)
    
    return Response(content=playlist, media_type="application/x-mpegurl")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
