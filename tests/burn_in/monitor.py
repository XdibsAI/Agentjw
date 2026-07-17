#!/usr/bin/env python3
"""Burn-in test monitor untuk AgentJW"""

import json
import time
import psutil
import subprocess
from datetime import datetime
from pathlib import Path
import sys

class BurnInMonitor:
    def __init__(self, duration_hours=168):  # 7 hari
        self.duration = duration_hours * 3600
        self.start_time = time.time()
        self.log_dir = Path("logs/burn_in")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.metrics = {
            "start_time": datetime.now().isoformat(),
            "duration_hours": duration_hours,
            "samples": []
        }
        
    def collect_metrics(self):
        """Kumpulkan metrics sistem dan AgentJW"""
        # System metrics
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # AgentJW process
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            if 'python' in proc.info['name']:
                # Cek apakah ini proses AgentJW
                try:
                    cmdline = ' '.join(proc.cmdline())
                    if 'agentjw' in cmdline or 'sicuan' in cmdline:
                        agent_cpu = proc.cpu_percent()
                        agent_memory = proc.memory_percent()
                        break
                except:
                    pass
        
        # Get health score
        try:
            import sys
            sys.path.insert(0, '/home/dibs/agentjw')
            from sicuan.core.production_metrics import get_production_metrics
            from sicuan.core.ceo_agent import get_ceo_agent
            
            metrics = get_production_metrics()
            ceo = get_ceo_agent()
            
            health = ceo.get_health_score()
            automation = ceo.get_automation_rate()
            
            data = metrics._data
            workflow_rate = data["workflow"]["success_rate"]
            mtbf = data["recovery"]["mtbf"]
            mttr = data["recovery"]["mttr"]
        except:
            health = 0
            automation = 0
            workflow_rate = 0
            mtbf = 0
            mttr = 0
        
        sample = {
            "timestamp": datetime.now().isoformat(),
            "uptime_hours": (time.time() - self.start_time) / 3600,
            "system": {
                "cpu_percent": cpu,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024**3)
            },
            "agent": {
                "cpu_percent": agent_cpu if 'agent_cpu' in locals() else 0,
                "memory_percent": agent_memory if 'agent_memory' in locals() else 0
            },
            "business": {
                "health_score": health,
                "automation_rate": automation,
                "workflow_success_rate": workflow_rate,
                "mtbf": mtbf,
                "mttr": mttr
            }
        }
        
        self.metrics["samples"].append(sample)
        self.save_metrics()
        
        return sample
    
    def save_metrics(self):
        """Save metrics ke file"""
        filepath = self.log_dir / f"burn_in_{datetime.now().strftime('%Y%m%d')}.json"
        with open(filepath, 'w') as f:
            json.dump(self.metrics, f, indent=2)
    
    def run(self):
        """Main loop monitoring"""
        print(f"🚀 Starting burn-in test for {self.duration/3600} hours")
        print(f"📊 Monitoring every 5 minutes...")
        print(f"📁 Logging to {self.log_dir}")
        
        while (time.time() - self.start_time) < self.duration:
            sample = self.collect_metrics()
            
            # Print status
            uptime = sample['uptime_hours']
            health = sample['business']['health_score']
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                  f"Uptime: {uptime:.1f}h | "
                  f"Health: {health}/100 | "
                  f"CPU: {sample['system']['cpu_percent']:.1f}% | "
                  f"Memory: {sample['system']['memory_percent']:.1f}%")
            
            # Cek jika health turun drastis
            if health < 50:
                print(f"⚠️  WARNING: Health score dropped to {health}")
            
            time.sleep(300)  # 5 menit
        
        print("✅ Burn-in test completed!")
        return self.metrics

if __name__ == "__main__":
    monitor = BurnInMonitor(duration_hours=168)  # 7 hari
    monitor.run()
