import asyncio
from playwright.async_api import async_playwright
import re

class VidsrcSniffer:
    def __init__(self):
        self.domains = ["https://vidsrc.to", "https://vidsrc.me", "https://vidsrc.net"]

    async def get_real_m3u8(self, media_id, is_tv=False, season=1, episode=1):
        try:
            async with async_playwright() as p:
                # إضافة خيارات لضمان التشغيل داخل Docker
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
                )
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
                )
                page = await context.new_page()

                m3u8_url = None
                
                async def handle_request(request):
                    nonlocal m3u8_url
                    url = request.url
                    if ".m3u8" in url and ("playlist" in url or "master" in url):
                        m3u8_url = url

                page.on("request", handle_request)

                for base_url in self.domains:
                    try:
                        url = f"{base_url}/embed/tv/{media_id}/{season}/{episode}" if is_tv else f"{base_url}/embed/movie/{media_id}"
                        print(f"Sniffing: {url}")
                        
                        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                        await asyncio.sleep(2) # انتظار قصير لبدء الطلبات
                        
                        if m3u8_url: break
                    except Exception as e:
                        print(f"Attempt failed for {base_url}: {e}")
                        continue

                await browser.close()
                return m3u8_url
        except Exception as e:
            print(f"Global Sniffing Error: {e}")
            return None
