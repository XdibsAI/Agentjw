import subprocess
import os
from core.logger import logger

NODE = "/home/dibs/.nvm/versions/node/v24.13.1/bin/node"
OPENCLAW_JS = "/home/dibs/.nvm/versions/node/v24.13.1/lib/node_modules/openclaw/openclaw.mjs"
OPENCLAW_TARGET = "5090639343"


def send_message(message: str, target: str = OPENCLAW_TARGET) -> bool:
    """Fire and forget - non-blocking"""
    try:
        subprocess.Popen(
            [NODE, OPENCLAW_JS, "message", "send",
             "--channel", "telegram",
             "--target", target,
             "--message", message],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return True
    except Exception as e:
        logger.warning("OpenClaw failed: " + str(e))
        return False


def notify_build_done(project_name: str, status: str, project_id: str):
    icon = "✅" if status == "success" else "⚠️"
    send_message(icon + " Build " + status.upper() + "\nProject: " + project_name + "\nID: " + project_id)


def notify_repair_done(project_name: str, repaired: list, failed: list):
    send_message("🔧 Repair Done\nProject: " + project_name + "\nFixed: " + str(len(repaired)) + " | Failed: " + str(len(failed)))


def notify_bot_status(project_name: str, stdout: str, success: bool):
    icon = "▶️" if success else "❌"
    send_message(icon + " Bot: " + project_name + "\n" + stdout[:200])


def ask_agent(message: str) -> str:
    try:
        result = subprocess.run(
            [NODE, OPENCLAW_JS, "agent", "--agent", "main",
             "--message", message, "--deliver"],
            capture_output=True, text=True, timeout=60,
        )
        return result.stdout.strip()
    except Exception as e:
        return "error: " + str(e)
