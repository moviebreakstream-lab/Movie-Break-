import httpx
import re
import json
import base64

class VidPlayResolver:
    """
    محرك حل VidPlay/VidCloud المتطور.
    يعتمد على استخراج مفاتيح الـ "futoken" وتجاوز حماية التحقق من النطاق.
    """
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Referer": "https://vidplay.online/"
        }

    async def resolve(self, embed_url):
        try:
            async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=15) as client:
                # 1. جلب صفحة الـ embed
                resp = await client.get(embed_url)
                if resp.status_code != 200: return None

                # 2. استخراج الـ futoken (تحديث 2026)
                # المواقع تستخدم الآن سكريبت خارجي لتوليد توكن ديناميكي
                token_match = re.search(r'src=["\']([^"\']+/futoken[^"\']*)["\']', resp.text)
                if token_match:
                    token_url = token_match.group(1)
                    if token_url.startswith('//'): token_url = "https:" + token_url
                    
                    # جلب التوكن (يحتاج لمحاكاة منطق JS)
                    # ملاحظة: في النسخة النهائية، نقوم بتنفيذ منطق توليد التوكن برمجياً
                    # هنا سنقوم بمحاولة جلب الروابط مباشرة إذا كانت متاحة
                    
                # 3. البحث عن روابط m3u8 المشفرة بـ Base64
                m3u8_patterns = [
                    r'["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
                    r'["\']([a-zA-Z0-9+/]{100,}={0,2})["\']' # البحث عن كتل Base64 كبيرة
                ]
                
                for pattern in m3u8_patterns:
                    matches = re.findall(pattern, resp.text)
                    for match in matches:
                        if ".m3u8" in match:
                            return {"source": "VidPlay", "m3u8_url": match.replace("\\/", "/")}
                        try:
                            decoded = base64.b64decode(match).decode('utf-8', errors='ignore')
                            if ".m3u8" in decoded:
                                m_url = re.search(r'(https?://[^\s"\'<>]+playlist\.m3u8[^\s"\'<>]*)', decoded)
                                if m_url: return {"source": "VidPlay (Decoded)", "m3u8_url": m_url.group(1)}
                        except: continue

            return None
        except Exception as e:
            print(f"VidPlay Resolve Error: {e}")
            return None
