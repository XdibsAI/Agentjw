"""
Webhook Engine - Event-driven webhooks
"""

import json
import requests
from pathlib import Path
from typing import Dict, List
from datetime import datetime


class WebhookEngine:
    """Webhook engine untuk event notification"""

    def __init__(self):
        self.webhook_dir = Path("/home/dibs/agentjw/memory/webhooks")
        self.webhook_dir.mkdir(exist_ok=True)
        self._load_webhooks()

    def _load_webhooks(self):
        """Load webhooks"""
        self.webhooks = {}
        for f in self.webhook_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                ws_id = data.get("workspace_id")
                if ws_id not in self.webhooks:
                    self.webhooks[ws_id] = []
                self.webhooks[ws_id].append(data)
            except:
                pass

    def _save_webhook(self, webhook: Dict):
        """Save webhook"""
        wh_id = f"{webhook['workspace_id']}_{int(time.time())}"
        webhook_file = self.webhook_dir / f"{wh_id}.json"
        webhook_file.write_text(json.dumps(webhook, indent=2))
        
        if webhook["workspace_id"] not in self.webhooks:
            self.webhooks[webhook["workspace_id"]] = []
        self.webhooks[webhook["workspace_id"]].append(webhook)

    def register(self, workspace_id: str, url: str, events: List[str], secret: str = None) -> Dict:
        """Register webhook"""
        webhook = {
            "workspace_id": workspace_id,
            "url": url,
            "events": events,
            "secret": secret,
            "created_at": datetime.now().isoformat(),
            "is_active": True,
            "delivery_count": 0,
            "success_count": 0
        }
        self._save_webhook(webhook)
        return webhook

    def trigger(self, workspace_id: str, event: str, data: Dict):
        """Trigger webhook event"""
        if workspace_id not in self.webhooks:
            return
        
        for webhook in self.webhooks[workspace_id]:
            if not webhook.get("is_active", True):
                continue
            
            if event not in webhook.get("events", []):
                continue
            
            # Send webhook
            try:
                payload = {
                    "event": event,
                    "timestamp": datetime.now().isoformat(),
                    "workspace_id": workspace_id,
                    "data": data
                }
                
                headers = {"Content-Type": "application/json"}
                if webhook.get("secret"):
                    headers["X-Webhook-Secret"] = webhook["secret"]
                
                response = requests.post(
                    webhook["url"],
                    json=payload,
                    headers=headers,
                    timeout=10
                )
                
                webhook["delivery_count"] += 1
                if response.status_code in [200, 201, 202]:
                    webhook["success_count"] += 1
                
                # Update stats
                self._update_stats(webhook)
                
            except Exception as e:
                print(f"[WEBHOOK] Error sending to {webhook['url']}: {e}")

    def _update_stats(self, webhook: Dict):
        """Update webhook stats"""
        # TODO: Save stats
        pass


def get_webhook_engine():
    _engine = None
    if _engine is None:
        _engine = WebhookEngine()
    return _engine
