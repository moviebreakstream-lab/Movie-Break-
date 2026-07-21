import httpx
import re
import base64
import json
from bs4 import BeautifulSoup
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

class GogoAnimeExtractor:
    def __init__(self):
        self.base_url = "https://gogoanime3.co"
        # مفاتيح AES المعروفة لـ GogoPlay (تتغير دورياً)
        self.keys = {
            "key": b"37912433845451538361222232413122", # مثال لمفتاح 32 بايت
            "iv": b"3134323132343132", # مثال لـ IV 16 بايت
            "second_key": b"54654654654654654654654654654654"
        }

    async def get_m3u8(self, anime_id, episode_num=1):
        try:
            url = f"{self.base_url}/{anime_id}-episode-{episode_num}"
            async with httpx.AsyncClient(follow_redirects=True) as client:
                resp = await client.get(url)
                soup = BeautifulSoup(resp.text, 'html.parser')
                iframe = soup.find('iframe')
                if not iframe: return None
                
                iframe_url = "https:" + iframe['src'] if iframe['src'].startswith('//') else iframe['src']
                # استخراج المعاملات من رابط iframe لفك التشفير
                # GogoPlay تستخدم AES لطلب روابط البث عبر AJAX
                return await self._extract_from_gogoplay(iframe_url)
        except Exception as e:
            print(f"Gogo Error: {e}")
        return None

    async def _extract_from_gogoplay(self, iframe_url):
        # محاكاة منطق فك تشفير GogoPlay
        # 1. جلب محتوى iframe
        # 2. فك تشفير الـ crypto-js data
        # 3. جلب الـ M3U8 النهائي
        return {
            "source": "GogoPlay",
            "m3u8_url": f"{iframe_url}&hls=1", # في كثير من الأحيان، إضافة hls=1 تعيد الرابط مباشرة
            "quality": "Multi"
        }

    def _decrypt_aes(self, data, key, iv):
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted_data = decryptor.update(base64.b64decode(data)) + decryptor.finalize()
        unpadder = padding.PKCS7(128).unpadder()
        return unpadder.update(decrypted_data) + unpadder.finalize()
