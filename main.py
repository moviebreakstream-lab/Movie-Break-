import asyncio
import os
from fastapi import FastAPI, Response, HTTPException, Query
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from extractors.vidsrc_sniff import VidsrcSniffer
from core.tmdb_client import TMDBClient
import uvicorn

load_dotenv()

app = FastAPI(title="Movie Break Pro - Network Sniffer Edition")
sniffer = VidsrcSniffer()
tmdb = TMDBClient()

@app.get("/")
async def root():
    return {"status": "Online", "mode": "Dynamic Network Sniffing"}

@app.get("/movie/{movie_id}")
async def get_movie(movie_id: str):
    m3u8_url = await sniffer.get_real_m3u8(movie_id)
    tmdb_data = await tmdb.get_movie_details(movie_id)
    
    if m3u8_url:
        return JSONResponse(content={
            "id": movie_id,
            "source": "Vidsrc Sniffer",
            "m3u8_url": m3u8_url,
            "tmdb_data": tmdb_data
        })
    
    return JSONResponse(content={
        "id": movie_id,
        "source": "Fallback",
        "m3u8_url": f"https://vidsrc.to/embed/movie/{movie_id}",
        "message": "Real M3U8 could not be sniffed, returning stable embed"
    })

@app.get("/tv/{tv_id}/{season}/{episode}")
async def get_tv(tv_id: str, season: int, episode: int):
    m3u8_url = await sniffer.get_real_m3u8(tv_id, is_tv=True, season=season, episode=episode)
    tmdb_data = await tmdb.get_tv_details(tv_id)
    
    if m3u8_url:
        return JSONResponse(content={
            "id": tv_id,
            "source": "Vidsrc Sniffer",
            "m3u8_url": m3u8_url,
            "tmdb_data": tmdb_data
        })
    
    return JSONResponse(content={
        "id": tv_id,
        "source": "Fallback",
        "m3u8_url": f"https://vidsrc.to/embed/tv/{tv_id}/{season}/{episode}",
        "message": "Real M3U8 could not be sniffed"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
