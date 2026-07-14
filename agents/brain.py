"""
agents/brain.py - AgentJW Brain
Fixed: decide() returns correct action strings matching orchestrator.execute()
"""
import re
from typing import Dict, List, Optional
from core.logger import logger


class Brain:

    def decide(self, user_input: str, chat_history: Optional[List[Dict]] = None) -> Dict:
        """
        Returns action string that EXACTLY matches orchestrator.execute() handlers:
        build_general | build_trading | build_youtube | run_project |
        scan_project  | show_log      | read_file     | repair       |
        analyze       | modify        | continue      |
        mcp_token     | mcp_trending  | chat
        """
        try:
            lower = user_input.lower()

            # ── MCP tools ──────────────────────────────────────────────────
            if any(k in lower for k in ["cek token","check token","rug check","token address"]):
                return self._d("mcp_token", 0.95, user_input)
            if any(k in lower for k in ["trending","top coin","hot coin","viral coin"]):
                return self._d("mcp_trending", 0.9, user_input)

            # ── Run / Execute ──────────────────────────────────────────────
            if any(k in lower for k in [
                "jalankan","coba jalankan","jalanin","run project",
                "execute","start project","running","coba run","start app"
            ]):
                return self._d("run_project", 0.95, user_input)

            # ── Show log ───────────────────────────────────────────────────
            if any(k in lower for k in ["show log","lihat log","tampilkan log","baca log","log error"]):
                return self._d("show_log", 0.9, user_input)

            # ── Scan / inspect ─────────────────────────────────────────────
            if any(k in lower for k in [
                "scan","struktur","list file","tampilkan struktur",
                "cek project","cek second","lihat project","projects",
                "daftar project","project list","show project","inspect",
                "cek ","lihat ","tampilkan project","status project",
            ]):
                return self._d("scan_project", 0.9, user_input)

            # ── Read file ──────────────────────────────────────────────────
            if any(k in lower for k in ["baca file","read file","tampilkan isi","show file","lihat file","cat "]):
                return self._d("read_file", 0.9, user_input)

            # ── Repair ─────────────────────────────────────────────────────
            if any(k in lower for k in ["repair","fix bug","perbaiki","debug","broken","error di project"]):
                return self._d("repair", 0.9, user_input)

            # ── Analyze ────────────────────────────────────────────────────
            if any(k in lower for k in ["analisa","analyze","review code","cek kode","audit"]):
                return self._d("analyze", 0.85, user_input)

            # ── Modify existing ────────────────────────────────────────────
            if any(k in lower for k in ["modifikasi","modify","ubah","edit","update","tambah fitur","ganti"]):
                return self._d("modify", 0.85, user_input)

            # ── Continue project ───────────────────────────────────────────
            if any(k in lower for k in ["lanjutkan","continue","lanjut project","resume"]):
                return self._d("continue", 0.85, user_input)

            # ── Trading build ──────────────────────────────────────────────
            if any(k in lower for k in [
                "trading bot","trade bot","crypto bot","binance bot","bybit bot",
                "solana bot","sniper bot","dex bot","arbitrage","scalping bot",
                "signal bot","copy trading"
            ]):
                return self._d("build_trading", 0.92, user_input)

            # ── YouTube build ──────────────────────────────────────────────
            if any(k in lower for k in [
                "youtube bot","auto upload","youtube channel","upload youtube",
                "youtube seo","thumbnail generator","youtube analytics"
            ]):
                return self._d("build_youtube", 0.92, user_input)

            # ── General build ──────────────────────────────────────────────
            if any(k in lower for k in [
                "buatkan","buat ","bikin","build ","create ","generate ",
                "buatin","second brain","aplikasi","program ","tool ",
                "api ","bot ","flask","fastapi","sistem","website","dashboard",
                "script","automation","scheduler","reminder","catatan","journal"
            ]):
                return self._d("build_general", 0.88, user_input)

            # ── Default: chat ──────────────────────────────────────────────
            return self._d("chat", 0.6, user_input)

        except Exception as e:
            logger.error(f"Brain.decide failed: {e}")
            return self._d("chat", 0.5, user_input)

    def _d(self, action: str, confidence: float, user_input: str) -> Dict:
        """Build decision dict — resolve target_project from input"""
        target_project = None
        target_file    = None
        try:
            from memory.memory_store import memory_store
            adapter = get_project_adapter()
            projects = adapter.get_projects()
            lower = user_input.lower()
            for p in (projects or []):
                if p.get("id","") in user_input or p.get("name","").lower() in lower:
                    target_project = p["id"]
                    break
            if not target_project and projects and action in (
                "run_project","repair","show_log","scan_project","read_file","modify","continue","analyze"
            ):
                target_project = projects[0]["id"]
        except Exception:
            pass
        m = re.search(r'(\w[\w.-]*\.(py|log|txt|md|json|env|sh))', user_input)
        if m:
            target_file = m.group(1)
        return {
            "action":         action,
            "target_project": target_project,
            "target_file":    target_file,
            "confidence":     confidence,
            "user_input":     user_input,
        }

    def resolve_project(self, target_project_id, projects):
        """Resolve project dict by ID. Called from orchestrator.execute()"""
        if not projects:
            return None
        if not target_project_id:
            return projects[0] if projects else None
        tid = str(target_project_id).lower()
        for p in projects:
            if p.get("id") == target_project_id: return p
        for p in projects:
            if p.get("id","").startswith(tid[:8]): return p
        for p in projects:
            if tid in p.get("name","").lower(): return p
        return projects[0] if projects else None


brain = Brain()