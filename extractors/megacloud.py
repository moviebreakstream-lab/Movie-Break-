import httpx
import re
import base64
import json
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

class MegaCloudResolver:
    """
    محرك حل MegaCloud المتقدم لفك تشفير روابط M3U8 الحقيقية.
    يعتمد على خوارزمية AES-256-CBC مع اشتقاق المفتاح عبر OpenSSL EVP_BytesToKey.
    """
    def __init__(self):
        self.client = httpx.AsyncClient(headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Referer": "https://megacloud.tv/",
            "X-Requested-With": "XMLHttpRequest"
        }, timeout=15)
        # مفاتيح مجتمعية محدثة لعام 2026 (يتم جلبها ديناميكياً في النسخ الأكثر تطوراً)
        self.key_url = "https://raw.githubusercontent.com/megacloud-dev/keys/main/keys.json"

    async def resolve(self, embed_url):
        try:
            # 1. استخراج الـ ID من رابط الـ embed
            match = re.search(r'/embed-2/([^?]+)', embed_url)
            if not match: return None
            video_id = match.group(1)

            # 2. جلب المصادر المشفرة من الـ API
            api_url = f"https://megacloud.tv/embed-2/ajax/e-1/getSources?id={video_id}"
            resp = await self.client.get(api_url)
            if resp.status_code != 200: return None
            
            data = resp.json()
            sources_enc = data.get("sources")
            if not sources_enc or not isinstance(sources_enc, str):
                # إذا لم تكن مشفرة، نعيدها مباشرة
                return data.get("sources", [])

            # 3. جلب مفاتيح فك التشفير (تحديث 2026)
            # ملاحظة: في بيئة الإنتاج، يفضل تخزين هذه المفاتيح محلياً وتحديثها دورياً
            keys = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9] # قيم افتراضية للتوضيح
            
            # 4. فك تشفير الـ AES
            decrypted_text = self._decrypt_aes(sources_enc, keys)
            if decrypted_text:
                return json.loads(decrypted_text)
            
            return None
        except Exception as e:
            print(f"MegaCloud Resolve Error: {e}")
            return None

    def _decrypt_aes(self, ciphertext, keys):
        """
        تنفيذ فك تشفير AES-256-CBC المتوافق مع OpenSSL
        """
        try:
            raw_data = base64.b64decode(ciphertext)
            if raw_data[:8] != b"Salted__":
                return None
            
            salt = raw_data[8:16]
            encrypted = raw_data[16:]
            
            # اشتقاق المفتاح والـ IV (يحتاج للمفتاح السري الحقيقي المستخرج من لاعب JS)
            # هذا الجزء يحاكي EVP_BytesToKey
            secret = b"some_secret_key_extracted_from_js" # هذا يجب أن يكون ديناميكياً
            key_iv = self._evp_bytes_to_key(secret, salt, 32, 16)
            key = key_iv[:32]
            iv = key_iv[32:]
            
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            decrypted_padded = decryptor.update(encrypted) + decryptor.finalize()
            
            unpadder = padding.PKCS7(128).unpadder()
            decrypted = unpadder.update(decrypted_padded) + unpadder.finalize()
            
            return decrypted.decode('utf-8')
        except Exception as e:
            print(f"AES Decrypt Error: {e}")
            return None

    def _evp_bytes_to_key(self, password, salt, key_len, iv_len):
        """محاكاة OpenSSL EVP_BytesToKey لاستخراج المفتاح والـ IV"""
        m = []
        i = 0
        while len(b"".join(m)) < (key_len + iv_len):
            data = (m[i-1] if i > 0 else b"") + password + salt
            m.append(hashlib.md5(data).digest())
            i += 1
        return b"".join(m)
