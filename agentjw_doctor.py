#!/usr/bin/env python3
"""
AgentJW Doctor - Observability Dashboard
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

ROOT = Path("/home/dibs/agentjw")
RUNTIME_FILE = ROOT / "sicuan_audit_report" / "runtime_state.json"
QUEUE_FILE = ROOT / "memory" / "task_queue.json"


class AgentJWDoctor:
    def __init__(self):
        self.runtime_data = self._load_runtime()
        self.queue_data = self._load_queue()

    def _load_runtime(self) -> dict:
        if RUNTIME_FILE.exists():
            try:
                return json.loads(RUNTIME_FILE.read_text())
            except:
                return {}
        return {}

    def _load_queue(self) -> list:
        if QUEUE_FILE.exists():
            try:
                data = json.loads(QUEUE_FILE.read_text())
                # Handle both list of strings and list of dicts
                if isinstance(data, list):
                    return data
                return []
            except:
                return []
        return []

    def _classify_result(self, result: dict) -> str:
        if result.get("success", False):
            return "success"

        error_msg = str(result.get("error", "")).lower()
        target = str(result.get("target", "")).lower()

        expected_patterns = [
            "tidak ditemukan", "tidak ada", "project_tidak_ada",
            "file_tidak_ada", "symbol kosong", "not found",
            "does not exist", "no such", "empty", "belum di-render"
        ]

        for pattern in expected_patterns:
            if pattern in error_msg or pattern in target:
                return "expected_failure"

        return "unexpected_failure"

    def diagnose(self):
        print("\n" + "=" * 60)
        print("🔬 AGENTJW DOCTOR - Observability Dashboard")
        print("=" * 60)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        self._executive_brain_status()
        self._planner_status()
        self._reflection_status()
        self._executor_status()
        self._action_stats()
        self._top_slow_actions()
        self._queue_status()
        self._runtime_memory()
        self._openrouter_status()
        self._confidence_histogram()
        self._health_score()

        print("\n" + "=" * 60)

    def _executive_brain_status(self):
        print("\n🧠 EXECUTIVE BRAIN")
        print("-" * 40)

        history = self.runtime_data.get("execution_history", [])
        total = len(history)
        success = sum(1 for h in history if h.get("success", False))

        expected_fail = 0
        unexpected_fail = 0
        for h in history:
            if not h.get("success", False):
                cls = self._classify_result(h)
                if cls == "expected_failure":
                    expected_fail += 1
                elif cls == "unexpected_failure":
                    unexpected_fail += 1

        failed = total - success

        print(f"  Total workflows : {total}")
        print(f"  Completed       : {success}")
        print(f"  Failed          : {failed}")
        print(f"    Expected      : {expected_fail}")
        print(f"    Unexpected    : {unexpected_fail}")

        if total > 0:
            rate = (success / total) * 100
            status = "🟢 Healthy" if rate > 80 else "🟡 Warning" if rate > 50 else "🔴 Critical"
            print(f"  Success rate    : {rate:.1f}% {status}")

            adjusted_total = total - expected_fail
            if adjusted_total > 0:
                adjusted_rate = (success / adjusted_total) * 100
                print(f"  Adjusted rate   : {adjusted_rate:.1f}% (excluding expected failures)")

        running = len([h for h in history if h.get("status") == "running"])
        print(f"  Running         : {running}")

    def _planner_status(self):
        print("\n📋 PLANNER")
        print("-" * 40)

        history = self.runtime_data.get("execution_history", [])
        if history:
            durations = [h.get("duration", 0) for h in history if h.get("duration", 0) > 0]
            if durations:
                avg_duration = sum(durations) / len(durations)
                print(f"  Average DAG time: {avg_duration:.2f}s")
                print(f"  Total DAGs      : {len(durations)}")
            else:
                print("  No duration data available")
        else:
            print("  No planner data available")

    def _reflection_status(self):
        print("\n💭 REFLECTION")
        print("-" * 40)

        reflections = self.runtime_data.get("reflections", [])
        if reflections:
            confidences = []
            for r in reflections:
                conf = r.get("confidence", 0)
                if conf > 1:
                    confidences.append(conf)
                else:
                    confidences.append(conf * 100)

            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
                print(f"  Average confidence: {avg_confidence:.1f}%")

                recent = confidences[-10:] if len(confidences) > 10 else confidences
                if len(recent) > 1:
                    trend = recent[-1] - recent[0]
                    trend_icon = "📈" if trend > 0 else "📉" if trend < 0 else "➡️"
                    print(f"  Trend (last 10)   : {trend_icon} {trend:+.1f}%")
            else:
                print("  No confidence data available")

            retries = sum(1 for r in reflections if r.get("should_retry", False))
            print(f"  Retries          : {retries}")
            if reflections:
                print(f"  Retry rate       : {(retries / len(reflections)) * 100:.1f}%")
        else:
            print("  No reflection data available")

    def _executor_status(self):
        print("\n⚡ EXECUTOR")
        print("-" * 40)

        queue_size = len(self.queue_data)
        print(f"  Queue size      : {queue_size}")

        history = self.runtime_data.get("execution_history", [])
        if history:
            actions = defaultdict(int)
            for h in history:
                action = h.get("action", "unknown")
                actions[action] += 1

            print(f"  Total tasks     : {len(history)}")
            if actions:
                top_actions = sorted(actions.items(), key=lambda x: x[1], reverse=True)[:5]
                print("  Top actions:")
                for action, count in top_actions:
                    print(f"    - {action}: {count}")

    def _action_stats(self):
        history = self.runtime_data.get("execution_history", [])
        if not history:
            print("\n🎯 ACTION STATS")
            print("-" * 40)
            print("  No action data available")
            return

        print("\n🎯 ACTION STATS (Workflow vs LLM)")
        print("-" * 40)

        non_llm_actions = {"scan_project", "analyze_project", "list_projects", "gallery", "video_info", "show_log", "get_file", "project_summary"}

        action_stats = defaultdict(lambda: {"total": 0, "success": 0, "llm_success": 0, "duration": []})
        for h in history:
            action = h.get("action", "unknown")
            action_stats[action]["total"] += 1

            if h.get("success", False):
                action_stats[action]["success"] += 1

            if action not in non_llm_actions:
                result = h.get("result", {})
                if result.get("data") or result.get("summary") or h.get("summary"):
                    action_stats[action]["llm_success"] += 1
            else:
                action_stats[action]["llm_success"] = -1

            if h.get("duration", 0) > 0:
                action_stats[action]["duration"].append(h.get("duration", 0))

        print(f"  Total actions   : {len(action_stats)}")
        for action, stats in sorted(action_stats.items(), key=lambda x: x[1]["total"], reverse=True)[:5]:
            total = stats["total"]
            success = stats["success"]
            llm_success = stats["llm_success"]
            rate = (success / total) * 100 if total > 0 else 0

            if llm_success == -1:
                llm_display = "N/A"
            else:
                llm_display = f"{llm_success}/{total} ({llm_success/total*100:.0f}%)" if total > 0 else "0%"

            status = "✅" if rate > 80 else "⚠️" if rate > 50 else "❌"
            avg_duration = sum(stats["duration"]) / len(stats["duration"]) if stats["duration"] else 0
            print(f"    {status} {action}: {rate:.0f}% workflow, LLM: {llm_display} ({total} tasks, avg {avg_duration:.2f}s)")

    def _top_slow_actions(self):
        print("\n🐢 TOP SLOW ACTIONS")
        print("-" * 40)

        history = self.runtime_data.get("execution_history", [])
        if not history:
            print("  No data available")
            return

        action_durations = defaultdict(list)
        for h in history:
            action = h.get("action", "unknown")
            duration = h.get("duration", 0)
            if duration > 0:
                action_durations[action].append(duration)

        if not action_durations:
            print("  No duration data available")
            return

        avg_durations = {}
        for action, durations in action_durations.items():
            avg_durations[action] = sum(durations) / len(durations)

        sorted_actions = sorted(avg_durations.items(), key=lambda x: x[1], reverse=True)[:5]
        for action, avg_dur in sorted_actions:
            print(f"    {action}: {avg_dur:.2f}s")

    def _queue_status(self):
        """Display queue status"""
        print("\n📋 QUEUE STATUS")
        print("-" * 40)
        
        if not self.queue_data:
            print("  Queue is empty")
            return
        
        print(f"  Total items in queue: {len(self.queue_data)}")
        
        # Analyze queue by action type
        action_counts = defaultdict(int)
        for item in self.queue_data:
            # Handle both string and dict formats
            if isinstance(item, dict):
                action = item.get("action", "unknown")
            else:
                # If it's a string, try to parse it or use as is
                try:
                    # Try to parse as JSON if it's a string
                    if isinstance(item, str):
                        try:
                            parsed = json.loads(item)
                            if isinstance(parsed, dict):
                                action = parsed.get("action", "unknown")
                            else:
                                action = str(item)[:50]  # Truncate long strings
                        except:
                            action = str(item)[:50]  # Truncate long strings
                    else:
                        action = str(item)[:50]
                except:
                    action = "unknown"
            
            action_counts[action] += 1
        
        print("  Queue breakdown:")
        for action, count in sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"    - {action}: {count} items")
        
        # Show first few items as samples
        print("\n  Sample items:")
        for i, item in enumerate(self.queue_data[:3]):
            if isinstance(item, dict):
                print(f"    {i+1}. {item.get('action', 'unknown')} - {item.get('data', {}).get('target', '')[:50]}")
            elif isinstance(item, str):
                try:
                    parsed = json.loads(item)
                    if isinstance(parsed, dict):
                        print(f"    {i+1}. {parsed.get('action', 'unknown')} - {parsed.get('data', {}).get('target', '')[:50]}")
                    else:
                        print(f"    {i+1}. {item[:50]}...")
                except:
                    print(f"    {i+1}. {item[:50]}...")
            else:
                print(f"    {i+1}. {str(item)[:50]}...")

    def _runtime_memory(self):
        print("\n💾 RUNTIME MEMORY")
        print("-" * 40)

        runtime_size = RUNTIME_FILE.stat().st_size if RUNTIME_FILE.exists() else 0
        queue_size = QUEUE_FILE.stat().st_size if QUEUE_FILE.exists() else 0

        print(f"  Runtime state   : {runtime_size / 1024:.2f} KB")
        print(f"  Queue file      : {queue_size / 1024:.2f} KB")

        history = self.runtime_data.get("execution_history", [])
        reflections = self.runtime_data.get("reflections", [])
        print(f"  History entries : {len(history)}")
        print(f"  Reflections     : {len(reflections)}")

    def _openrouter_status(self):
        print("\n🌐 OPENROUTER")
        print("-" * 40)

        history = self.runtime_data.get("execution_history", [])

        total_tokens = 0
        action_tokens = defaultdict(int)
        action_durations = defaultdict(list)

        for h in history:
            action = h.get("action", "unknown")
            duration = h.get("duration", 0)

            if action in ["modify_logic", "modify_project", "build_project", "repair_project"]:
                estimated_tokens = int(duration / 5 * 1000) if duration > 0 else 0
            elif action in ["trace_code", "analyze_project"]:
                estimated_tokens = int(duration / 2 * 500) if duration > 0 else 0
            else:
                estimated_tokens = int(duration * 100) if duration > 0 else 0

            if action == "trace_code" and estimated_tokens > 10000:
                estimated_tokens = 5000

            action_tokens[action] += estimated_tokens
            total_tokens += estimated_tokens

            if duration > 0:
                action_durations[action].append(duration)

        errors = self.runtime_data.get("errors", [])
        error_402 = sum(1 for e in errors if "402" in str(e) or "Payment" in str(e))
        error_429 = sum(1 for e in errors if "429" in str(e) or "Rate limit" in str(e))

        print(f"  Prompt tokens   : {total_tokens:,}")
        print(f"  Completion tokens: {int(total_tokens * 0.15):,} (estimated)")
        print(f"  Estimated cost  : ${total_tokens * 0.000002:.4f} (at ~$2/1M tokens)")
        print(f"  402 errors      : {error_402}")
        print(f"  429 errors      : {error_429}")

        print("\n  📊 Average tokens per action:")
        for action, tokens in sorted(action_tokens.items(), key=lambda x: x[1], reverse=True)[:5]:
            count = sum(1 for h in history if h.get("action") == action)
            avg_tokens = tokens // count if count > 0 else 0
            avg_duration = sum(action_durations.get(action, [0])) // len(action_durations.get(action, [1])) if action_durations.get(action) else 0
            status = "✅" if avg_tokens < 3000 else "⚠️" if avg_tokens < 8000 else "❌"
            print(f"    {status} {action}: {avg_tokens:,} avg tokens, {avg_duration:.1f}s avg duration")

    def _confidence_histogram(self):
        reflections = self.runtime_data.get("reflections", [])
        if not reflections:
            return

        print("\n📊 CONFIDENCE HISTOGRAM")
        print("-" * 40)

        bins = {"0.9-1.0": 0, "0.8-0.9": 0, "0.7-0.8": 0, "0.6-0.7": 0, "0.5-0.6": 0, "<0.5": 0}

        for r in reflections:
            conf = r.get("confidence", 0)
            if conf > 1:
                conf = conf / 100

            if conf >= 0.9:
                bins["0.9-1.0"] += 1
            elif conf >= 0.8:
                bins["0.8-0.9"] += 1
            elif conf >= 0.7:
                bins["0.7-0.8"] += 1
            elif conf >= 0.6:
                bins["0.6-0.7"] += 1
            elif conf >= 0.5:
                bins["0.5-0.6"] += 1
            else:
                bins["<0.5"] += 1

        max_count = max(bins.values()) if bins.values() else 1
        for label, count in bins.items():
            bar_len = int((count / max_count) * 20) if max_count > 0 else 0
            print(f"  {label}: {'█' * bar_len} {count}")

    def _health_score(self):
        """Calculate overall health score"""
        print("\n🏥 OVERALL HEALTH SCORE")
        print("-" * 40)
        
        history = self.runtime_data.get("execution_history", [])
        reflections = self.runtime_data.get("reflections", [])
        
        if not history:
            print("  No data available")
            return
        
        # Success rate
        success = sum(1 for h in history if h.get("success", False))
        success_rate = (success / len(history)) * 100 if history else 0
        
        # Confidence
        confidences = []
        for r in reflections:
            conf = r.get("confidence", 0)
            if conf > 1:
                confidences.append(conf)
            else:
                confidences.append(conf * 100)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # Queue size
        queue_size = len(self.queue_data)
        
        # Health score (0-100)
        score = (success_rate * 0.5) + (avg_confidence * 0.3) + (max(0, 100 - queue_size * 2) * 0.2)
        score = min(100, max(0, score))
        
        status = "🟢 Excellent" if score > 80 else "🟡 Good" if score > 60 else "🔴 Needs Attention"
        
        print(f"  Health Score    : {score:.1f}/100 - {status}")
        print(f"    Success Rate  : {success_rate:.1f}% (weight: 50%)")
        print(f"    Confidence    : {avg_confidence:.1f}% (weight: 30%)")
        print(f"    Queue         : {queue_size} items (weight: 20%)")


def main():
    doctor = AgentJWDoctor()
    doctor.diagnose()


if __name__ == "__main__":
    main()
