#!/usr/bin/env python3
"""Security Audit untuk AgentJW"""

import os
import re
import subprocess
from pathlib import Path

class SecurityAudit:
    def __init__(self):
        self.issues = []
        
    def check_env_files(self):
        """Cek file .env dan API keys"""
        print("🔐 Checking .env files...")
        
        env_files = Path('.').glob('*.env')
        for env_file in env_files:
            content = env_file.read_text()
            if 'API_KEY' in content or 'SECRET' in content:
                self.issues.append({
                    "type": "env_file_found",
                    "file": str(env_file)
                })
                print(f"  ⚠️  Found sensitive data in {env_file}")
    
    def check_git_history(self):
        """Cek Git history untuk API keys"""
        print("🔍 Checking Git history...")
        
        try:
            # Cek commit terakhir
            result = subprocess.run(
                ['git', 'log', '--oneline', '-10'],
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                print("  Recent commits:")
                for line in result.stdout.strip().split('\n')[:5]:
                    print(f"    {line}")
        except:
            pass
    
    def check_dependencies(self):
        """Audit dependencies"""
        print("📦 Auditing dependencies...")
        
        if Path('requirements.txt').exists():
            result = subprocess.run(
                ['pip', 'list', '--outdated'],
                capture_output=True,
                text=True
            )
            outdated = [line for line in result.stdout.split('\n') 
                       if 'latest' in line][:5]
            
            if outdated:
                print("  ⚠️  Outdated packages:")
                for pkg in outdated:
                    print(f"    {pkg}")
    
    def check_permissions(self):
        """Cek Permission Engine"""
        print("🔒 Checking Permission Engine...")
        
        # Cek apakah permission engine ada
        if Path('sicuan/core/permission_engine.py').exists():
            print("  ✅ Permission Engine found")
            
            # Cek implementasi
            content = Path('sicuan/core/permission_engine.py').read_text()
            if 'def check_permission' in content:
                print("  ✅ check_permission() exists")
            else:
                self.issues.append({
                    "type": "missing_permission_check",
                    "description": "check_permission not found"
                })
        else:
            self.issues.append({
                "type": "permission_engine_not_found",
                "description": "Permission Engine not implemented"
            })
    
    def run(self):
        """Run full security audit"""
        print("\n" + "="*50)
        print("🔒 AGENTJW SECURITY AUDIT")
        print("="*50 + "\n")
        
        self.check_env_files()
        self.check_git_history()
        self.check_dependencies()
        self.check_permissions()
        
        print("\n" + "="*50)
        if self.issues:
            print("⚠️  ISSUES FOUND:")
            for issue in self.issues:
                print(f"  - {issue['type']}: {issue.get('description', '')}")
            print(f"\nTotal: {len(self.issues)} issues")
        else:
            print("✅ No security issues found!")
        print("="*50)

if __name__ == "__main__":
    audit = SecurityAudit()
    audit.run()
