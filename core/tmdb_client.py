import httpx
import os

class TMDBClient:
    def __init__(self):
        self.api_key = os.getenv("TMDB_API_KEY")
        self.base_url = "https://api.themoviedb.org/3"
        self.headers = {"Accept": "application/json"}

    async def _safe_get(self, url, params):
        if not self.api_key:
            return None
        try:
            params["api_key"] = self.api_key
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            print(f"TMDB Error: {e}")
        return None

    async def get_movie_details(self, movie_id):
        url = f"{self.base_url}/movie/{movie_id}"
        return await self._safe_get(url, {"language": "ar"})

    async def get_tv_details(self, tv_id):
        url = f"{self.base_url}/tv/{tv_id}"
        return await self._safe_get(url, {"language": "ar"})

    async def get_anime_details(self, query):
        url = f"{self.base_url}/search/tv"
        data = await self._safe_get(url, {"query": query, "language": "ar"})
        return data["results"][0] if data and data.get("results") else None
