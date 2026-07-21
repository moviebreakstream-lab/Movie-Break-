import asyncio
import os
from fastapi import FastAPI, Response, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from dotenv import load_dotenv
from core.engine import MovieBreakEngine
import uvicorn

load_dotenv()

app = FastAPI(title="Movie Break Pro - Real M3U8 Extractor")
engine = MovieBreakEngine()

@app.get("/")
async def root():
    return {"status": "Online", "service": "Real M3U8 Extraction"}

@app.get("/movie/{movie_id}")
async def get_movie(movie_id: str):
    results = await engine.extract_parallel([{"id": movie_id, "type": "movie"}])
    if results and results[0].get("m3u8_url"):
        # إعادة توجيه مباشرة لرابط m3u8 أو إعادته في JSON
        return JSONResponse(content={"m3u8": results[0]["m3u8_url"], "subtitles": results[0].get("subtitles", [])})
    raise HTTPException(status_code=404, detail="M3U8 not found")

@app.get("/tv/{tv_id}/{season}/{episode}")
async def get_tv(tv_id: str, season: int, episode: int):
    results = await engine.extract_parallel([{"id": tv_id, "type": "tv", "season": season, "episode": episode}])
    if results and results[0].get("m3u8_url"):
        return JSONResponse(content={"m3u8": results[0]["m3u8_url"], "subtitles": results[0].get("subtitles", [])})
    raise HTTPException(status_code=404, detail="M3U8 not found")

@app.get("/anime/{anime_id}/{episode}")
async def get_anime(anime_id: str, episode: int):
    results = await engine.extract_parallel([{"id": anime_id, "type": "anime", "episode": episode}])
    if results and results[0].get("m3u8_url"):
        return JSONResponse(content={"m3u8": results[0]["m3u8_url"]})
    raise HTTPException(status_code=404, detail="M3U8 not found")

@app.get("/playlist.m3u")
async def get_playlist(ids: str):
    id_list = ids.split(",")
    media_list = [{"id": mid.strip(), "type": "tv" if "tv" in mid else "movie"} for mid in id_list]
    results = await engine.extract_parallel(media_list)
    playlist = engine.generate_iptv_playlist(results)
    return Response(content=playlist, media_type="application/x-mpegurl")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
