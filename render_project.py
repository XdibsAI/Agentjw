#!/usr/bin/env python3
"""
render_project.py - Standalone video renderer CLI for AgentJW
Usage:
    python3 render_project.py                # render the most recent video_* project
    python3 render_project.py video_abc123    # render a specific project (by folder name)
    python3 render_project.py --list          # list available video projects
"""
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from core.config import config  # noqa: E402
from tools.video.video_renderer import video_renderer_tool  # noqa: E402


def find_video_projects():
    base = config.PROJECTS_DIR
    out = []
    for d in sorted(base.glob("video_*")):
        pkg = d / "video_package.json"
        if pkg.exists():
            out.append(d)
    return out


def main():
    args = sys.argv[1:]

    if args and args[0] == "--list":
        for d in find_video_projects():
            pkg = json.loads((d / "video_package.json").read_text(encoding="utf-8"))
            title = pkg.get("intent", {}).get("title", "?")
            done = (d / "final_video.mp4").exists()
            mark = "✅ rendered" if done else "⏳ not rendered"
            print(f"{d.name:25s} | {title[:40]:40s} | {mark}")
        return

    projects = find_video_projects()
    if not projects:
        print("No video projects found (looking for projects/video_*/video_package.json)")
        sys.exit(1)

    if args:
        target = config.PROJECTS_DIR / args[0]
        if not (target / "video_package.json").exists():
            print(f"Not found: {target}/video_package.json")
            sys.exit(1)
    else:
        target = projects[-1]

    print(f"Rendering: {target}")
    package = json.loads((target / "video_package.json").read_text(encoding="utf-8"))
    out_path = video_renderer_tool.render(package, target)
    print(f"\nDone -> {out_path}")


if __name__ == "__main__":
    main()
