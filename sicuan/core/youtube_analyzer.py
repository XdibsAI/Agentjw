"""
YouTube Analyzer - Gunakan YouTube Data API untuk analisis channel
"""
import os
import time
import requests
from typing import Dict, Optional


class YouTubeAnalyzer:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY")
        self.base_url = "https://www.googleapis.com/youtube/v3"

    def extract_channel_id(self, url: str) -> Optional[str]:
        """Extract channel ID from YouTube URL"""
        import re
        
        # Handle @username format
        if "@" in url:
            # https://youtube.com/@mr.speedvgr
            match = re.search(r'@([^/?]+)', url)
            if match:
                username = match.group(1)
                # Coba langsung dengan username (tanpa API search dulu)
                channel_id = self._get_channel_id_from_username(username)
                if channel_id:
                    return channel_id
        
        # Handle channel ID format
        if "/channel/" in url:
            match = re.search(r'/channel/([^/?]+)', url)
            if match:
                return match.group(1)
        
        # Handle youtube.com/c/ format
        if "/c/" in url:
            match = re.search(r'/c/([^/?]+)', url)
            if match:
                username = match.group(1)
                return self._get_channel_id_from_username(username)
        
        # Handle youtu.be format (biasanya video, bukan channel)
        if "youtu.be" in url:
            return None
        
        # Fallback: coba dari URL parameter
        if "?" in url:
            import urllib.parse
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)
            if "channel" in params:
                return params["channel"][0]
        
        return None

    def _get_channel_id_from_username(self, username: str) -> Optional[str]:
        print(f"[YouTube] Getting channel ID for username: {username}")
        """Get channel ID from username using search API"""
        if not self.api_key:
            return None
        
        url = f"{self.base_url}/search"
        params = {
            "part": "snippet",
            "q": username,
            "type": "channel",
            "key": self.api_key,
            "maxResults": 1
        }
        
        try:
            time.sleep(0.5)
            print(f"[YouTube] Requesting: {url}")
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            if data.get("error", {}).get("code") == 429:
                return {"error": "Rate limit exceeded. Coba lagi nanti."}
            print(f"[YouTube] Response: {data.keys() if isinstance(data, dict) else type(data)}")
            if data.get("items"):
                return data["items"][0]["snippet"]["channelId"]
        except Exception as e:
            print(f"[YouTube] Error: {e}")
        
        return None

    def get_channel_info(self, channel_id: str) -> Dict:
        """Get channel info using channel ID"""
        if not self.api_key:
            return {"error": "YouTube API key not configured"}
        
        url = f"{self.base_url}/channels"
        params = {
            "part": "snippet,statistics",
            "id": channel_id,
            "key": self.api_key
        }
        
        try:
            time.sleep(0.5)
            print(f"[YouTube] Requesting: {url}")
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            if data.get("error", {}).get("code") == 429:
                return {"error": "Rate limit exceeded. Coba lagi nanti."}
            print(f"[YouTube] Response: {data.keys() if isinstance(data, dict) else type(data)}")
            if data.get("items"):
                item = data["items"][0]
                snippet = item.get("snippet", {})
                stats = item.get("statistics", {})
                return {
                    "name": snippet.get("title", "Unknown"),
                    "description": snippet.get("description", "")[:500],
                    "subscribers": stats.get("subscriberCount", "0"),
                    "total_views": stats.get("viewCount", "0"),
                    "total_videos": stats.get("videoCount", "0"),
                    "channel_id": channel_id
                }
        except Exception as e:
            return {"error": str(e)}
        
        return {"error": "Channel not found"}

    def get_recent_videos(self, channel_id: str, max_results: int = 5) -> list:
        """Get recent videos from channel"""
        if not self.api_key:
            return []
        
        url = f"{self.base_url}/search"
        params = {
            "part": "snippet",
            "channelId": channel_id,
            "order": "date",
            "type": "video",
            "key": self.api_key,
            "maxResults": max_results
        }
        
        try:
            time.sleep(0.5)
            print(f"[YouTube] Requesting: {url}")
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            videos = []
            for item in data.get("items", []):
                snippet = item.get("snippet", {})
                videos.append({
                    "title": snippet.get("title", "Unknown"),
                    "published_at": snippet.get("publishedAt", ""),
                    "thumbnail": snippet.get("thumbnails", {}).get("default", {}).get("url", "")
                })
            return videos
        except Exception as e:
            print(f"[YouTube] Error: {e}")
        
        return []

    def analyze_channel(self, url: str) -> Dict:
        """Main method: analyze YouTube channel from URL"""
        # Extract channel ID
        channel_id = self.extract_channel_id(url)
        if not channel_id:
            return {"error": "Could not extract channel ID from URL"}
        
        # Get channel info
        info = self.get_channel_info(channel_id)
        if "error" in info:
            return info
        
        # Get recent videos
        videos = self.get_recent_videos(channel_id)
        info["recent_videos"] = videos
        
        # Generate analysis
        analysis = self._generate_analysis(info)
        info["analysis"] = analysis
        
        return info

    def _generate_analysis(self, info: Dict) -> str:
        """Generate analysis based on channel data"""
        name = info.get("name", "Unknown")
        subscribers = int(info.get("subscribers", "0").replace(",", ""))
        total_views = int(info.get("total_views", "0").replace(",", ""))
        total_videos = int(info.get("total_videos", "0").replace(",", ""))
        
        avg_views = total_views // max(total_videos, 1)
        
        lines = []
        lines.append(f"📊 **Channel:** {name}")
        lines.append(f"📊 **Subscribers:** {subscribers:,}")
        lines.append(f"📊 **Total Views:** {total_views:,}")
        lines.append(f"📊 **Total Videos:** {total_videos:,}")
        lines.append(f"📊 **Avg Views/Video:** {avg_views:,}")
        lines.append("")
        
        if subscribers > 100000:
            lines.append("🔥 **Ini channel besar!** ")
        elif subscribers > 10000:
            lines.append("📈 **Channel berkembang dengan baik!** ")
        elif subscribers > 1000:
            lines.append("🌱 **Channel masih growing, ada potensi besar!** ")
        else:
            lines.append("🌱 **Channel masih baru, tapi punya potensi!** ")
        
        lines.append("")
        lines.append("💡 **Saran:**")
        
        if avg_views < 100:
            lines.append("- Fokus ke kualitas thumbnail dan judul")
        elif avg_views < 500:
            lines.append("- Upload konsisten (minimal 1x/minggu)")
        elif avg_views < 2000:
            lines.append("- Interaksi dengan viewers di komentar")
        else:
            lines.append("- Pertahankan konsistensi dan kualitas konten")
        
        if total_videos < 10:
            lines.append("- Buat lebih banyak konten untuk algoritma")
        elif total_videos < 50:
            lines.append("- Eksperimen dengan format konten baru")
        
        return "\n".join(lines)


_analyzer = None


def get_youtube_analyzer() -> YouTubeAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = YouTubeAnalyzer()
    return _analyzer
