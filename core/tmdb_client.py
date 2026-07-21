import httpx
import os

class TMDBClient:
    def __init__(self):
        self.api_key = os.getenv("TMDB_API_KEY")
        if not self.api_key:
            raise ValueError("TMDB_API_KEY environment variable not set.")
        self.base_url = "https://api.themoviedb.org/3"
        self.headers = {"Accept": "application/json"}

    async def search_movie(self, query):
        url = f"{self.base_url}/search/movie"
        params = {"api_key": self.api_key, "query": query, "language": "ar"}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return data["results"][0] if data["results"] else None

    async def search_tv(self, query):
        url = f"{self.base_url}/search/tv"
        params = {"api_key": self.api_key, "query": query, "language": "ar"}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return data["results"][0] if data["results"] else None

    async def get_movie_details(self, movie_id):
        url = f"{self.base_url}/movie/{movie_id}"
        params = {"api_key": self.api_key, "language": "ar"}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def get_tv_details(self, tv_id):
        url = f"{self.base_url}/tv/{tv_id}"
        params = {"api_key": self.api_key, "language": "ar"}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def get_anime_details(self, query):
        # TMDB لا يمتلك تصنيفًا مباشرًا للأنمي، لذا سنبحث في المسلسلات التلفزيونية
        # يمكن تحسين هذا لاحقًا باستخدام API مخصص للأنمي إذا لزم الأمر
        url = f"{self.base_url}/search/tv"
        params = {"api_key": self.api_key, "query": query, "language": "ar"}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return data["results"][0] if data["results"] else None
