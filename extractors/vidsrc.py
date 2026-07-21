import httpx
import re
import base64
import json
from bs4 import BeautifulSoup
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

class VidsrcExtractor:
    def __init__(self):
        self.base_url = "https://vidsrc.to"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://vidsrc.to/"
        }

    async def get_m3u8(self, media_id, is_tv=False, season=1, episode=1):
        """
        يستخرج روابط M3u8 لفيلم أو حلقة مسلسل من vidsrc.to.
        """
        if is_tv:
            url = f"{self.base_url}/embed/tv/{media_id}/{season}/{episode}"
        else:
            url = f"{self.base_url}/embed/movie/{media_id}"
        
        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True) as client:
            try:
                response = await client.get(url)
                if response.status_code != 200:
                    return None
                
                soup = BeautifulSoup(response.text, 'html.parser')
                data_id = soup.find('div', {'id': 'player'})
                if not data_id:
                    # محاولة البحث في scripts
                    match = re.search(r'data-id="([^"]+)"', response.text)
                    if match:
                        data_id = match.group(1)
                    else:
                        return None
                else:
                    data_id = data_id.get('data-id')

                # جلب المصادر (Sources)
                sources_url = f"{self.base_url}/ajax/embed/episode/{data_id}/sources"
                sources_resp = await client.get(sources_url)
                sources_data = sources_resp.json()
                
                if sources_data.get('status') != 200:
                    return None
                
                # اختيار أول مصدر (عادة ما يكون Vidplay أو MyCloud)
                source_id = sources_data['result'][0]['id']
                
                # جلب رابط المصدر المشفر
                source_url = f"{self.base_url}/ajax/embed/source/{source_id}"
                source_resp = await client.get(source_url)
                source_data = source_resp.json()
                
                if source_data.get('status') != 200:
                    return None
                
                encrypted_url = source_data['result']['url']
                # فك تشفير الرابط (يتطلب منطق فك تشفير vidsrc الخاص)
                decrypted_url = self.decrypt_vidsrc_url(encrypted_url)
                
                return {
                    "source": "Vidsrc.to",
                    "m3u8_url": decrypted_url,
                    "subtitles": self.extract_subtitles(response.text),
                    "quality": "Auto (1080p/720p)"
                }
            except Exception as e:
                print(f"Error in VidsrcExtractor: {e}")
                return None

    def decrypt_vidsrc_url(self, encrypted_url):
        """
        منطق فك تشفير روابط vidsrc.to (نسخة مبسطة للمثال، تحتاج لتحديث دوري).
        """
        # vidsrc تستخدم غالباً Base64 مع تبديل أحرف أو AES
        try:
            # مثال لفك تشفير بسيط (يجب تحديثه بناءً على التغييرات)
            return base64.b64decode(encrypted_url).decode('utf-8')
        except:
            return encrypted_url # العودة للرابط كما هو إذا فشل فك التشفير

    def extract_subtitles(self, html):
        """
        استخراج روابط الترجمة من محتوى HTML.
        """
        subs = []
        # البحث عن نصوص الترجمة في الـ scripts
        matches = re.findall(r'\{"file":"([^"]+)","label":"([^"]+)"\}', html)
        for file, label in matches:
            subs.append({"url": file, "lang": label})
        return subs
