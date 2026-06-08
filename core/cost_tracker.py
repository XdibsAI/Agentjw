import json
import os
from datetime import datetime

COST_FILE = "logs/cost_tracker.json"

class CostTracker:

    def __init__(self):
        os.makedirs("logs", exist_ok=True)

        if not os.path.exists(COST_FILE):
            with open(COST_FILE, "w") as f:
                json.dump({
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "requests": 0
                }, f)

    def add(self,input_tokens=0,output_tokens=0):

        with open(COST_FILE) as f:
            data=json.load(f)

        data["input_tokens"] += input_tokens
        data["output_tokens"] += output_tokens
        data["requests"] += 1
        data["last_update"] = datetime.utcnow().isoformat()

        with open(COST_FILE,"w") as f:
            json.dump(data,f,indent=2)

    def stats(self):
        with open(COST_FILE) as f:
            return json.load(f)
