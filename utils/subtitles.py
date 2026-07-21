class SubtitleManager:
    @staticmethod
    def format_subtitle_line(lang, url):
        """
        تنسيق سطر الترجمة لقائمة IPTV.
        """
        return f'#EXTVLCOPT:sub-file={url}\n'

    @staticmethod
    def get_vlc_sub_headers(subtitles):
        """
        توليد رؤوس VLC للترجمات المتعددة.
        """
        header = ""
        for sub in subtitles:
            header += f"#EXTVLCOPT:sub-file={sub['url']}\n"
        return header
