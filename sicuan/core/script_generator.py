"""
Script Generator - Buat script konten YouTube
"""
from typing import Dict, Optional


class ScriptGenerator:
    """Generate script untuk konten YouTube"""

    def generate_script(self, channel_info: Dict, topic: str, duration: int = 180) -> str:
        """Generate script berdasarkan channel dan topic"""
        
        name = channel_info.get("name", "Channel")
        subscribers = channel_info.get("subscribers", "0")
        niche = self._detect_niche(channel_info)
        
        script = f"""
# 📹 SCRIPT VIDEO: {topic.upper()}
# Channel: {name} ({subscribers} subscribers)
# Durasi: ±{duration//60} menit
# Niche: {niche}

---

## 🎬 OPENING (0:00 - 0:15)

**Visual:** Logo channel + animasi cepat

**Voiceover:**
"Halo guys, welcome back ke channel {name}! Hari ini kita bakal bahas tentang {topic}!"

---

## 🎯 INTRO (0:15 - 0:45)

**Voiceover:**
"Sebelum mulai, jangan lupa subscribe ya! Kita udah punya {subscribers} subscribers."

"Jadi, apa sih sebenarnya {topic}?"

---

## 📖 BODY (0:45 - {duration//2})

**Voiceover:**
"Oke, jadi begini ceritanya..."

"Poin pertama yang perlu kamu tahu adalah..."

"Selain itu, ada juga fakta menarik lainnya..."

---

## 🔥 CLIMAX ({duration//2} - {duration - 30})

**Voiceover:**
"Nah, ini yang paling penting!..."

"Jadi, kalau kamu mau [action], ini yang harus kamu lakukan..."

---

## ✅ OUTRO ({duration - 30} - {duration})

**Voiceover:**
"Gimana? Keren kan!"

"Jangan lupa like, subscribe, dan komen di bawah ya!"

"See you di video selanjutnya! Bye!"

---

## 🎵 MUSIK & SFX

- Opening: upbeat
- Body: background
- Climax: dramatis
- Outro: ending

---

## 📝 CATATAN PRODUKSI

1. **Durasi:** {duration} detik (±{duration//60} menit)
2. **Thumbnail:** Capture momen ekspresif
3. **Hashtags:** #{topic.replace(' ', '').lower()} #{niche} #shorts

---
"""
        return script

    def _detect_niche(self, channel_info: Dict) -> str:
        """Detect niche dari channel"""
        name = channel_info.get("name", "").lower()
        description = channel_info.get("description", "").lower()
        videos = channel_info.get("recent_videos", [])
        
        video_text = " ".join([v.get("title", "").lower() for v in videos])
        
        niches = {
            "gaming": ["game", "gaming", "speedrun", "minecraft", "gta", "fortnite"],
            "food": ["food", "makanan", "recipe", "resep", "lotis", "buah"],
            "education": ["fakta", "knowledge", "belajar", "tips", "trick"],
            "entertainment": ["viral", "funny", "lucu", "crazy", "shorts"],
            "nature": ["nature", "waterfall", "relax", "scenery"]
        }
        
        scores = {niche: 0 for niche in niches}
        for niche, keywords in niches.items():
            for keyword in keywords:
                if keyword in name or keyword in description or keyword in video_text:
                    scores[niche] += 1
        
        best_niche = max(scores, key=scores.get) if scores else "general"
        return best_niche if scores.get(best_niche, 0) > 0 else "general"


_generator = None


def get_script_generator() -> ScriptGenerator:
    global _generator
    if _generator is None:
        _generator = ScriptGenerator()
    return _generator
