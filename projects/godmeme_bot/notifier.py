import logging
import json
import asyncio
import smtplib
import ssl
from typing import Dict, List, Optional, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass
from enum import Enum
import telegram
from solana.rpc.api import Client

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    TRADE_EXECUTED = "trade_executed"
    TRADE_CLOSED = "trade_closed"
    RISK_ALERT = "risk_alert"
    SYSTEM_ALERT = "system_alert"
    PERFORMANCE_UPDATE = "performance_update"
    ERROR_ALERT = "error_alert"

@dataclass
class Notification:
    notification_type: NotificationType
    title: str
    message: str
    metadata: Optional[Dict[str, Any]] = None
    priority: str = "normal"  # low, normal, high, critical

class Notifier:
    def __init__(self, config, database):
        self.config = config
        self.database = database
        self.email_enabled = bool(getattr(config, 'EMAIL_HOST', None) and getattr(config, 'EMAIL_USER', None) and getattr(config, 'EMAIL_PASSWORD', None))
        self.telegram_enabled = bool(getattr(config, 'TELEGRAM_BOT_TOKEN', None) and getattr(config, 'TELEGRAM_CHAT_ID', None))
        self.discord_enabled = bool(getattr(config, 'DISCORD_WEBHOOK_URL', None))
        
        # Initialize Telegram bot if enabled
        if self.telegram_enabled:
            self.telegram_bot = telegram.Bot(token=config.TELEGRAM_BOT_TOKEN)
            self.telegram_chat_id = config.TELEGRAM_CHAT_ID
        else:
            self.telegram_bot = None
            
        # Setup email configuration
        if self.email_enabled:
            self.email_host = config.EMAIL_HOST
            self.email_port = getattr(config, 'EMAIL_PORT', 587)
            self.email_user = config.EMAIL_USER
            self.email_password = config.EMAIL_PASSWORD
            self.email_from = getattr(config, 'EMAIL_FROM', config.EMAIL_USER)
            self.email_to = getattr(config, 'EMAIL_TO', None)
            
        logger.info(f"Notifier initialized with email: {self.email_enabled}, telegram: {self.telegram_enabled}, discord: {self.discord_enabled}")

    async def send_notification(self, notification: Notification) -> bool:
        """Send notification through all enabled channels"""
        success = True
        
        # Log notification to database
        try:
            if hasattr(self.database, 'log_notification'):
                self.database.log_notification(
                    notification_type=notification.notification_type.value,
                    title=notification.title,
                    message=notification.message,
                    metadata=notification.metadata,
                    priority=notification.priority
                )
        except Exception as e:
            logger.error(f"Failed to log notification to database: {e}")
            
        # Send through enabled channels
        if self.email_enabled:
            try:
                await self._send_email(notification)
            except Exception as e:
                logger.error(f"Failed to send email notification: {e}")
                success = False
                
        if self.telegram_enabled:
            try:
                await self._send_telegram(notification)
            except Exception as e:
                logger.error(f"Failed to send Telegram notification: {e}")
                success = False
                
        if self.discord_enabled:
            try:
                await self._send_discord(notification)
            except Exception as e:
                logger.error(f"Failed to send Discord notification: {e}")
                success = False
                
        return success

    async def _send_email(self, notification: Notification) -> None:
        """Send email notification"""
        if not self.email_enabled:
            return
            
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_from
            msg['To'] = self.email_to
            msg['Subject'] = f"[{notification.notification_type.value.upper()}] {notification.title}"
            
            body = notification.message
            if notification.metadata:
                body += f"\n\nMetadata: {json.dumps(notification.metadata, indent=2)}"
                
            msg.attach(MIMEText(body, 'plain'))
            
            # Create secure connection and send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.email_host, self.email_port) as server:
                server.starttls(context=context)
                server.login(self.email_user, self.email_password)
                server.sendmail(self.email_from, self.email_to, msg.as_string())
                
            logger.info(f"Email notification sent: {notification.title}")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise

    async def _send_telegram(self, notification: Notification) -> None:
        """Send Telegram notification"""
        if not self.telegram_enabled:
            return
            
        try:
            message = f"*{notification.title}*\n\n{notification.message}"
            if notification.metadata:
                message += f"\n\n_Metadata_: ```{json.dumps(notification.metadata, indent=2)}```"
                
            # Format for Telegram markdown
            message = message.replace('_', '\\_')
            
            await self.telegram_bot.send_message(
                chat_id=self.telegram_chat_id,
                text=message,
                parse_mode='Markdown'
            )
            
            logger.info(f"Telegram notification sent: {notification.title}")
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            raise

    async def _send_discord(self, notification: Notification) -> None:
        """Send Discord notification"""
        if not self.discord_enabled:
            return
            
        try:
            import httpx
            
            # Determine color based on priority
            color_map = {
                "low": 0x808080,
                "normal": 0x00ff00,
                "high": 0xffa500,
                "critical": 0xff0000
            }
            
            color = color_map.get(notification.priority, 0x00ff00)
            
            # Build embed
            embed = {
                "title": notification.title,
                "description": notification.message,
                "color": color,
                "fields": []
            }
            
            if notification.metadata:
                for key, value in notification.metadata.items():
                    embed["fields"].append({
                        "name": key.replace('_', ' ').title(),
                        "value": str(value)[:1024],  # Discord limit
                        "inline": True
                    })
                    
            payload = {
                "embeds": [embed]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.config.DISCORD_WEBHOOK_URL,
                    json=payload,
                    timeout=10.0
                )
                response.raise_for_status()
                
            logger.info(f"Discord notification sent: {notification.title}")
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")
            raise

    async def send_trade_notification(self, trade_data: Dict[str, Any]) -> None:
        """Send notification for trade execution"""
        notification = Notification(
            notification_type=NotificationType.TRADE_EXECUTED,
            title=f"Trade Executed: {trade_data.get('symbol', 'Unknown')}",
            message=f"Trade executed for {trade_data.get('symbol', 'Unknown')} at {trade_data.get('price', 'N/A')} SOL",
            metadata=trade_data,
            priority="high" if trade_data.get('is_large_trade', False) else "normal"
        )
        await self.send_notification(notification)

    async def send_close_notification(self, trade_data: Dict[str, Any]) -> None:
        """Send notification for trade closure"""
        notification = Notification(
            notification_type=NotificationType.TRADE_CLOSED,
            title=f"Trade Closed: {trade_data.get('symbol', 'Unknown')}",
            message=f"Trade closed for {trade_data.get('symbol', 'Unknown')} with PnL: {trade_data.get('pnl', 'N/A')} SOL ({trade_data.get('pnl_percentage', 'N/A')}%)",
            metadata=trade_data,
            priority="normal"
        )
        await self.send_notification(notification)

    async def send_risk_alert(self, alert_data: Dict[str, Any]) -> None:
        """Send risk management alert"""
        notification = Notification(
            notification_type=NotificationType.RISK_ALERT,
            title=f"Risk Alert: {alert_data.get('alert_type', 'Unknown')}",
            message=alert_data.get('message', 'Risk alert triggered'),
            metadata=alert_data,
            priority="high"
        )
        await self.send_notification(notification)

    async def send_system_alert(self, alert_data: Dict[str, Any]) -> None:
        """Send system alert"""
        notification = Notification(
            notification_type=NotificationType.SYSTEM_ALERT,
            title=f"System Alert: {alert_data.get('alert_type', 'Unknown')}",
            message=alert_data.get('message', 'System alert triggered'),
            metadata=alert_data,
            priority=alert_data.get('priority', 'normal')
        )
        await self.send_notification(notification)

    async def send_error_alert(self, error_data: Dict[str, Any]) -> None:
        """Send error alert"""
        notification = Notification(
            notification_type=NotificationType.ERROR_ALERT,
            title=f"Error Alert: {error_data.get('error_type', 'Unknown')}",
            message=error_data.get('message', 'An error occurred'),
            metadata=error_data,
            priority="high"
        )
        await self.send_notification(notification)

    async def send_performance_update(self, performance_data: Dict[str, Any]) -> None:
        """Send performance update"""
        notification = Notification(
            notification_type=NotificationType.PERFORMANCE_UPDATE,
            title="Performance Update",
            message=f"Daily PnL: {performance_data.get('daily_pnl', 'N/A')} SOL ({performance_data.get('daily_pnl_percentage', 'N/A')}%)",
            metadata=performance_data,
            priority="normal"
        )
        await self.send_notification(notification)

    def health_check(self) -> Dict[str, Any]:
        """Return health status of notification channels"""
        return {
            "email_enabled": self.email_enabled,
            "telegram_enabled": self.telegram_enabled,
            "discord_enabled": self.discord_enabled,
            "email_configured": bool(getattr(self, 'email_host', None) and getattr(self, 'email_user', None) and getattr(self, 'email_password', None)) if self.email_enabled else False,
            "telegram_configured": bool(getattr(self, 'telegram_bot', None) and getattr(self, 'telegram_chat_id', None)) if self.telegram_enabled else False,
            "discord_configured": bool(getattr(self.config, 'DISCORD_WEBHOOK_URL', None)) if self.discord_enabled else False
        }