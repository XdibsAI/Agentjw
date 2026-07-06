"""
Auto Fix Loop — Perbaiki error sampai sukses
"""

import time
from typing import Dict, List, Optional
from datetime import datetime


class AutoFixLoop:
    """Loop auto-fix sampai error resolved"""

    def __init__(self, brain, max_attempts: int = 3):
        self.brain = brain
        self.max_attempts = max_attempts
        self.history = []
        self.last_error = None

    def run(self, initial_error: str) -> Dict:
        """Run auto-fix loop sampai sukses atau max attempts"""
        error = initial_error
        attempt = 0
        last_result = None

        print(f"[AUTO-FIX] Starting loop for: {error[:50]}...")

        while attempt < self.max_attempts:
            attempt += 1
            print(f"[AUTO-FIX] Attempt {attempt}/{self.max_attempts}")

            # 1. Diagnose
            diagnosis = self.brain.diagnose_error(error)
            print(f"[AUTO-FIX] Diagnosis: {diagnosis.get('action')} - {diagnosis.get('fix', 'N/A')[:50]}")

            # 2. Auto-fix
            result = self.brain.auto_fix_error(error)
            last_result = result

            # 3. Check result
            if result.get("status") == "verified":
                print(f"[AUTO-FIX] ✅ Success! Error resolved.")
                self.history.append({
                    "attempt": attempt,
                    "error": error,
                    "result": "success",
                    "timestamp": datetime.now().isoformat()
                })
                return {
                    "success": True,
                    "attempts": attempt,
                    "result": result,
                    "history": self.history
                }

            # 4. Jika gagal, coba ambil error baru
            if result.get("validation", {}).get("reason"):
                error = result["validation"]["reason"]
                print(f"[AUTO-FIX] ❌ Failed. New error: {error[:50]}...")
            else:
                error = "Unknown error after fix attempt"

            self.history.append({
                "attempt": attempt,
                "error": error,
                "result": "failed",
                "timestamp": datetime.now().isoformat()
            })

            # Wait sebelum retry
            time.sleep(2)

        # Max attempts reached
        print(f"[AUTO-FIX] ❌ Max attempts ({self.max_attempts}) reached.")
        return {
            "success": False,
            "attempts": attempt,
            "result": last_result,
            "history": self.history
        }


# Singleton
_loop = None

def get_auto_fix_loop(brain):
    global _loop
    if _loop is None:
        _loop = AutoFixLoop(brain)
    return _loop
