import json
from pathlib import Path

ROOT = Path(__file__).parent.parent

class CapabilityEngine:

    def scan(self):
        caps = {
            "coding": False,
            "debugging": False,
            "filesystem": False,
            "telegram": False,
            "youtube": False,
            "video": False,
            "trading": False,
            "mcp": False
        }

        if (ROOT / "agents").exists():
            caps["coding"] = True
            caps["debugging"] = True

        if (ROOT / "tools").exists():
            caps["filesystem"] = True

        if (ROOT / "sicuan/telegram_bot.py").exists():
            caps["telegram"] = True

        if (ROOT / "tools/youtube").exists():
            caps["youtube"] = True

        if (ROOT / "tools/video").exists():
            caps["video"] = True

        if (ROOT / "projects/godmeme_bot").exists():
            caps["trading"] = True

        if (ROOT / "mcp").exists():
            caps["mcp"] = True

        out = ROOT / "memory/capabilities.json"
        out.parent.mkdir(exist_ok=True)

        out.write_text(
            json.dumps(caps, indent=2)
        )

        return caps
