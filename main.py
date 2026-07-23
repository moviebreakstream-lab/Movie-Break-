import asyncio
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from extractors.vidsrc import VidsrcExtractor
from core.tmdb_client import TMDBClient
import uvicorn

load_dotenv()

app = FastAPI(title="Movie Break Pro - Final Resolver Edition")
extractor = VidsrcExtractor()
tmdb = TMDBClient()

@app.get("/")
async def root():
    return {"status": "Online", "engine": "MegaCloud/VidPlay Resolver v2026"}

@app.get("/movie/{movie_id}")
async def get_movie(movie_id: str):
    res = await extractor.get_m3u8(movie_id)
    tmdb_data = await tmdb.get_movie_details(movie_id)
    
    if res and res.get("m3u8_url"):
        return JSONResponse(content={
            "id": movie_id,
            "source": res.get("source"),
            "m3u8_url": res.get("m3u8_url"),
            "quality": res.get("quality", "Auto"),
            "tmdb_data": tmdb_data
        })
    
    raise HTTPException(status_code=404, detail="M3U8 link not found for this movie. The source might be protected or down.")

@app.get("/tv/{tv_id}/{season}/{episode}")
async def get_tv(tv_id: str, season: int, episode: int):
    res = await extractor.get_m3u8(tv_id, is_tv=True, season=season, episode=episode)
    tmdb_data = await tmdb.get_tv_details(tv_id)
    
    if res and res.get("m3u8_url"):
        return JSONResponse(content={
            "id": tv_id,
            "source": res.get("source"),
            "m3u8_url": res.get("m3u8_url"),
            "quality": res.get("quality", "Auto"),
            "tmdb_data": tmdb_data
        })
    
    raise HTTPException(status_code=404, detail="M3U8 link not found for this episode.")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
