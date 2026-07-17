"""
Marketing Agent — Promo, konten, broadcast, follow-up
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class MarketingAgent:
    """Marketing Agent — Kelola promo, konten, broadcast"""

    def __init__(self):
        self.campaigns = []
        self.broadcasts = []
        self.campaign_counter = 0

    def create_campaign(self, name: str, target_segment: str, message: str, 
                        start_date: str = None, end_date: str = None) -> Dict:
        """Buat campaign marketing baru"""
        self.campaign_counter += 1
        campaign = {
            "id": f"CM-{self.campaign_counter:04d}",
            "name": name,
            "target_segment": target_segment,
            "message": message,
            "status": "draft",
            "start_date": start_date or datetime.now().isoformat(),
            "end_date": end_date or (datetime.now() + timedelta(days=30)).isoformat(),
            "created_at": datetime.now().isoformat(),
            "metrics": {
                "sent": 0,
                "opened": 0,
                "clicked": 0,
                "converted": 0
            }
        }
        self.campaigns.append(campaign)
        return campaign

    def launch_campaign(self, campaign_id: str) -> Dict:
        """Launch campaign"""
        for c in self.campaigns:
            if c["id"] == campaign_id:
                c["status"] = "active"
                c["launched_at"] = datetime.now().isoformat()
                return c
        return {"error": "Campaign not found"}

    def get_active_campaigns(self) -> List[Dict]:
        return [c for c in self.campaigns if c["status"] == "active"]

    def get_campaigns_by_segment(self, segment: str) -> List[Dict]:
        return [c for c in self.campaigns if c["target_segment"] == segment]

    def create_broadcast(self, message: str, target_segment: str = "all") -> Dict:
        """Buat broadcast message"""
        broadcast = {
            "id": f"BC-{len(self.broadcasts)+1:04d}",
            "message": message,
            "target_segment": target_segment,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "sent_at": None
        }
        self.broadcasts.append(broadcast)
        return broadcast

    def send_broadcast(self, broadcast_id: str) -> Dict:
        """Kirim broadcast"""
        for b in self.broadcasts:
            if b["id"] == broadcast_id:
                b["status"] = "sent"
                b["sent_at"] = datetime.now().isoformat()
                return b
        return {"error": "Broadcast not found"}

    def get_pending_broadcasts(self) -> List[Dict]:
        return [b for b in self.broadcasts if b["status"] == "pending"]

    def format_campaign(self, campaign: Dict) -> str:
        lines = []
        lines.append(f"📢 **{campaign['name']}**")
        lines.append(f"🎯 Target: {campaign['target_segment']}")
        lines.append(f"📊 Status: {campaign['status']}")
        lines.append(f"📝 {campaign['message'][:100]}...")
        metrics = campaign.get("metrics", {})
        lines.append(f"📈 Sent: {metrics.get('sent', 0)} | Opened: {metrics.get('opened', 0)} | Converted: {metrics.get('converted', 0)}")
        return "\n".join(lines)


_marketing = None


def get_marketing_agent() -> MarketingAgent:
    global _marketing
    if _marketing is None:
        _marketing = MarketingAgent()
    return _marketing
