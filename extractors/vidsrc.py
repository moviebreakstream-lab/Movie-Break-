import httpx
import re
import json
import base64
from bs4 import BeautifulSoup

class VidsrcExtractor:
    def __init__(self):
        self.domains = [
            "https://vidsrc.to", 
            "https://vidsrc.me", 
            "https://vidsrc.net", 
            "https://vidsrc.xyz",
            "https://vidsrc.cc",
            "https://vidsrc.pm"
        ]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Referer": "https://vidsrc.to/"
        }

    async def get_m3u8(self, media_id, is_tv=False, season=1, episode=1):
        for base_url in self.domains:
            try:
                url = f"{base_url}/embed/tv/{media_id}/{season}/{episode}" if is_tv else f"{base_url}/embed/movie/{media_id}"
                
                async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=15) as client:
                    resp = await client.get(url)
                    if resp.status_code != 200:
                        continue
                    
                    # 1. البحث عن روابط m3u8 مباشرة (أحياناً تكون موجودة في سكريبتات الصفحة)
                    m3u8_patterns = [
                        r'["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
                        r'(https?://[^\s"\'<>]+playlist\.m3u8[^\s"\'<>]*)',
                        r'(https?://[^\s"\'<>]+master\.m3u8[^\s"\'<>]*)'
                    ]
                    
                    for pattern in m3u8_patterns:
                        match = re.search(pattern, resp.text)
                        if match:
                            m3u8_url = match.group(1).replace("\\/", "/")
                            # التحقق من أن الرابط ليس مجرد placeholder
                            if "playlist.m3u8" in m3u8_url or "master.m3u8" in m3u8_url:
                                return {
                                    "source": f"Vidsrc ({base_url.split('//')[1]})",
                                    "m3u8_url": m3u8_url,
                                    "subtitles": self.extract_subtitles(resp.text)
                                }

                    # 2. محاولة فك تشفير الـ data-hash لـ Vidsrc.me/Vidsrc.to
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    hidden_div = soup.find('div', {'id': 'hidden'})
                    if hidden_div and hidden_div.get('data-h'):
                        encoded_h = hidden_div.get('data-h')
                        seed = soup.find('body').get('data-i', 'tt')
                        decoded_url = self._decode_xor(encoded_h, seed)
                        if decoded_url:
                            # تتبع الرابط لفك التشفير النهائي
                            if decoded_url.startswith("//"): decoded_url = "https:" + decoded_url
                            return await self._deep_resolve(decoded_url, client)

                    # 3. إذا فشل كل شيء، نعيد رابط الـ embed نفسه كملاذ أخير
                    # معظم مشغلات IPTV الحديثة يمكنها التعامل مع روابط الـ embed واستخراج الفيديو منها
                    return {
                        "source": f"Vidsrc Embed ({base_url.split('//')[1]})",
                        "m3u8_url": url,
                        "subtitles": self.extract_subtitles(resp.text),
                        "is_embed": True
                    }
            except Exception as e:
                print(f"Error with {base_url}: {e}")
                continue
        return None

    def _decode_xor(self, encoded, seed):
        try:
            encoded_buffer = bytes.fromhex(encoded)
            decoded = ""
            for i in range(len(encoded_buffer)):
                decoded += chr(encoded_buffer[i] ^ ord(seed[i % len(seed)]))
            return decoded
        except: return None

    async def _deep_resolve(self, url, client):
        try:
            resp = await client.get(url)
            m3u8_match = re.search(r'["\'](https?://[^"\']+\.m3u8[^"\']*)["\']', resp.text)
            if m3u8_match:
                return {
                    "source": "Vidsrc Deep",
                    "m3u8_url": m3u8_match.group(1).replace("\\/", "/"),
                    "subtitles": self.extract_subtitles(resp.text)
                }
            return {"source": "Vidsrc Resolved", "m3u8_url": url, "subtitles": []}
        except:
            return {"source": "Vidsrc Fallback", "m3u8_url": url, "subtitles": []}

    def extract_subtitles(self, html):
        subs = []
        matches = re.findall(r'["\']?file["\']?:\s*["\']([^"\']+\.vtt[^"\']*)["\']\s*,\s*["\']?label["\']?:\s*["\']([^"\']+)["\']', html)
        for file, label in matches:
            subs.append({"url": file.replace("\\/", "/"), "lang": label})
        return subs
