"""Load test untuk AgentJW"""
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from sicuan.brain import SiCuanBrain

def run_task(action, target):
    brain = SiCuanBrain()
    return brain.execute_action(action, target, "load test", f"load_{threading.get_ident()}")

def load_test(n_workers=10, n_tasks=100):
    tasks = [("scan_project", "godmeme_bot") for _ in range(n_tasks)]
    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        results = list(executor.map(lambda t: run_task(*t), tasks))
    success = sum(1 for r in results if r)
    print(f"Success rate: {success}/{n_tasks} ({success/n_tasks*100:.1f}%)")
    return results

if __name__ == "__main__":
    load_test()
