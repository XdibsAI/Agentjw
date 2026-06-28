"""Memory leak test"""
import tracemalloc
import time
from sicuan.brain import SiCuanBrain

def memory_test(n_iterations=100):
    tracemalloc.start()
    brain = SiCuanBrain()
    for i in range(n_iterations):
        brain.execute_action("scan_project", "godmeme_bot", "memory test", f"mem_{i}")
        if i % 10 == 0:
            current, peak = tracemalloc.get_traced_memory()
            print(f"Iteration {i}: {current / 1024 / 1024:.2f} MB (peak: {peak / 1024 / 1024:.2f} MB)")
    tracemalloc.stop()
    print("Memory test complete")
