import httpx
import re
import base64
import json
from bs4 import BeautifulSoup
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

class VidsrcExtractor:
    def __init__(self):
        self.domains = ["https://vidsrc.to", "https://vidsrc.me", "https://vidsrc.net", "https://vidsrc.xyz"]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Referer": "https://vidsrc.to/"
        }
        # مفاتيح AES المعروفة لـ Vidsrc (قد تحتاج للتحديث دورياً)
        self.keys = {
            "vidsrc.to": {
                "key": b"32bytekey_placeholder_for_vidsrc_to", # سيتم استبداله بمنطق ديناميكي
                "iv": b"16byteiv_placeholder"
            }
        }

    async def get_m3u8(self, media_id, is_tv=False, season=1, episode=1):
        for base_url in self.domains:
            try:
                url = f"{base_url}/embed/tv/{media_id}/{season}/{episode}" if is_tv else f"{base_url}/embed/movie/{media_id}"
                async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=15) as client:
                    resp = await client.get(url)
                    if resp.status_code != 200: continue
                    
                    # استخراج الـ hash المشفر
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    # Vidsrc غالباً ما تضع البيانات المشفرة في div معين أو سكريبت
                    hidden_data = soup.find('div', {'id': 'hidden'})
                    if hidden_data and hidden_data.get('data-h'):
                        encoded_h = hidden_data.get('data-h')
                        seed = soup.find('body').get('data-i', 'tt')
                        # فك التشفير باستخدام منطق XOR أو AES حسب النطاق
                        decoded_url = self._decode_vidsrc_me(encoded_h, seed)
                        if decoded_url:
                            return await self._resolve_final_m3u8(decoded_url)

                    # محاولة استخراج m3u8 مباشرة إذا لم تكن مشفرة (نادر)
                    m3u8_match = re.search(r'(https?://[^\s"\'<>]+playlist\.m3u8[^\s"\'<>]*)', resp.text)
                    if m3u8_match:
                        return {"source": "Vidsrc Direct", "m3u8_url": m3u8_match.group(1), "subtitles": []}

            except Exception as e:
                print(f"Vidsrc Error: {e}")
        return None

    def _decode_vidsrc_me(self, encoded, seed):
        """منطق فك تشفير Vidsrc.me باستخدام XOR"""
        try:
            encoded_buffer = bytes.fromhex(encoded)
            decoded = ""
            for i in range(len(encoded_buffer)):
                decoded += chr(encoded_buffer[i] ^ ord(seed[i % len(seed)]))
            if decoded.startswith("//"): decoded = "https:" + decoded
            return decoded
        except: return None

    async def _resolve_final_m3u8(self, url):
        """الوصول للرابط النهائي من خلال تتبع التحويلات"""
        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True) as client:
            resp = await client.get(url)
            m3u8_match = re.search(r'(https?://[^\s"\'<>]+playlist\.m3u8[^\s"\'<>]*)', resp.text)
            if m3u8_match:
                return {
                    "source": "Vidsrc Decoded",
                    "m3u8_url": m3u8_match.group(1),
                    "subtitles": self._extract_subs(resp.text)
                }
        return {"source": "Vidsrc Embed", "m3u8_url": url, "subtitles": []}

    def _extract_subs(self, html):
        subs = []
        matches = re.findall(r'file:\s*["\']([^"\']+\.vtt[^"\']*)["\']\s*,\s*label:\s*["\']([^"\']+)["\']', html)
        for file, label in matches:
            subs.append({"url": file.replace("\\/", "/"), "lang": label})
        return subs
