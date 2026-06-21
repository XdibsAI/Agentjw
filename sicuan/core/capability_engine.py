import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

class CapabilityEngine:

    def scan(self):

        caps = {
            "coding": False,
            "debugging": False,
            "filesystem": False,
            "telegram": False,
            "video": False,
            "youtube": False,
            "trading": False,
            "mcp": False,
            "memory": False,
        }

        if (ROOT / "agents").exists():
            caps["coding"] = True
            caps["debugging"] = True

        if (ROOT / "tools").exists():
            caps["filesystem"] = True

        if (ROOT / "sicuan/telegram_bot.py").exists():
            caps["telegram"] = True

        if (ROOT / "tools/video").exists():
            caps["video"] = True

        if (ROOT / "tools/youtube").exists():
            caps["youtube"] = True

        projects = ROOT / "projects"

        if projects.exists():

            for p in projects.iterdir():

                if p.is_dir():

                    caps["trading"] = True
                    break

        if (ROOT / "mcp").exists():
            caps["mcp"] = True

        if (ROOT / "memory").exists():
            caps["memory"] = True

        out = ROOT / "memory/capabilities.json"
        out.write_text(json.dumps(caps, indent=2))

        return caps
