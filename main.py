import asyncio
import os
from fastapi import FastAPI, Response, Query, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from core.engine import MovieBreakEngine
import uvicorn

load_dotenv()

app = FastAPI(title="Movie Break ID-Based API")
engine = MovieBreakEngine()

@app.get("/")
async def root():
    return {
        "status": "Active",
        "service": "Movie Break Professional Extraction",
        "usage": {
            "extract_movie": "/movie/{id}",
            "extract_tv": "/tv/{id}/{season}/{episode}",
            "extract_anime": "/anime/{id}/{episode}",
            "iptv_playlist": "/playlist.m3u?ids=id1,id2,id3"
        },
        "example": "/movie/tt0111161"
    }

@app.get("/movie/{movie_id}")
async def get_movie(movie_id: str):
    results = await engine.extract_parallel([{"id": movie_id, "type": "movie"}])
    if not results:
        raise HTTPException(status_code=404, detail="Movie not found or extraction failed")
    return JSONResponse(content=results[0])

@app.get("/tv/{tv_id}/{season}/{episode}")
async def get_tv(tv_id: str, season: int, episode: int):
    results = await engine.extract_parallel([{"id": tv_id, "type": "tv", "season": season, "episode": episode}])
    if not results:
        raise HTTPException(status_code=404, detail="Episode not found or extraction failed")
    return JSONResponse(content=results[0])

@app.get("/anime/{anime_id}/{episode}")
async def get_anime(anime_id: str, episode: int):
    results = await engine.extract_parallel([{"id": anime_id, "type": "anime", "episode": episode}])
    if not results:
        raise HTTPException(status_code=404, detail="Anime episode not found or extraction failed")
    return JSONResponse(content=results[0])

@app.get("/playlist.m3u")
async def get_playlist(ids: str = Query(..., description="IMDb IDs separated by comma")):
    id_list = ids.split(",")
    media_list = []
    for mid in id_list:
        mid = mid.strip()
        # تحديد النوع بناءً على النمط (بسيط)
        m_type = "tv" if "tv" in mid else "movie" 
        media_list.append({"id": mid, "type": m_type})
    
    results = await engine.extract_parallel(media_list)
    playlist = engine.generate_iptv_playlist(results)
    
    return Response(content=playlist, media_type="application/x-mpegurl")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
