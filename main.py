import asyncio
import os
from fastapi import FastAPI, Response, HTTPException, Query
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from core.engine import MovieBreakEngine
import uvicorn

load_dotenv()

app = FastAPI(title="Movie Break Pro - Reliable Extractor")
engine = MovieBreakEngine()

@app.get("/")
async def root():
    return {"status": "Online", "message": "Service is ready for extraction"}

@app.get("/movie/{movie_id}")
async def get_movie(movie_id: str):
    results = await engine.extract_parallel([{"id": movie_id, "type": "movie"}])
    if results:
        return JSONResponse(content=results[0])
    # بدلاً من 404، نعيد رابط الـ embed كخيار أخير لضمان العمل
    return JSONResponse(content={
        "source": "Fallback",
        "m3u8_url": f"https://vidsrc.to/embed/movie/{movie_id}",
        "message": "Direct M3U8 not found, returning stable embed link"
    })

@app.get("/tv/{tv_id}/{season}/{episode}")
async def get_tv(tv_id: str, season: int, episode: int):
    results = await engine.extract_parallel([{"id": tv_id, "type": "tv", "season": season, "episode": episode}])
    if results:
        return JSONResponse(content=results[0])
    return JSONResponse(content={
        "source": "Fallback",
        "m3u8_url": f"https://vidsrc.to/embed/tv/{tv_id}/{season}/{episode}",
        "message": "Direct M3U8 not found, returning stable embed link"
    })

@app.get("/anime/{anime_id}/{episode}")
async def get_anime(anime_id: str, episode: int):
    results = await engine.extract_parallel([{"id": anime_id, "type": "anime", "episode": episode}])
    if results:
        return JSONResponse(content=results[0])
    return JSONResponse(content={
        "source": "Fallback",
        "m3u8_url": f"https://gogoanime3.co/{anime_id}-episode-{episode}",
        "message": "Direct M3U8 not found, returning stable stream link"
    })

@app.get("/playlist.m3u")
async def get_playlist(ids: str = Query(..., description="IDs separated by comma")):
    id_list = ids.split(",")
    media_list = []
    for mid in id_list:
        mid = mid.strip()
        media_list.append({"id": mid, "type": "tv" if "tv" in mid else "movie"})
    
    results = await engine.extract_parallel(media_list)
    playlist = engine.generate_iptv_playlist(results)
    return Response(content=playlist, media_type="application/x-mpegurl")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
