"""
GMGN Wrapper - Integrasi GMGN Skills ke AgentJW
"""
import subprocess
import json
from typing import Dict, Optional


class GMGNClient:
    """Wrapper untuk gmgn-cli"""

    def __init__(self):
        self.cmd = "gmgn-cli"

    def _run(self, args: list) -> Dict:
        """Run gmgn-cli command"""
        try:
            result = subprocess.run(
                [self.cmd] + args,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
            return {"error": result.stderr, "code": result.returncode}
        except Exception as e:
            return {"error": str(e)}

    def trending(self, chain: str = "sol", interval: str = "1h", limit: int = 10) -> Dict:
        """Get trending tokens"""
        return self._run([
            "market", "trending",
            "--chain", chain,
            "--interval", interval,
            "--limit", str(limit)
        ])

    def token_info(self, chain: str, address: str) -> Dict:
        """Get token info"""
        return self._run([
            "token", "info",
            "--chain", chain,
            "--address", address
        ])

    def portfolio(self, chain: str, wallet: str) -> Dict:
        """Get wallet portfolio"""
        return self._run([
            "portfolio", "holdings",
            "--chain", chain,
            "--wallet", wallet
        ])


_gmgn = None


def get_gmgn_client() -> GMGNClient:
    global _gmgn
    if _gmgn is None:
        _gmgn = GMGNClient()
    return _gmgn
