"""
Simple download server for AgentJW APK
"""
import http.server
import socketserver
import os
from pathlib import Path

APK_SOURCE = Path("/home/dibs/agentjw_remote/build/app/outputs/flutter-apk/app-release.apk")
APK_DEST = Path("/home/dibs/agentjw/agentjw_remote.apk")

# Copy APK to agentjw folder
if APK_SOURCE.exists():
    import shutil
    shutil.copy2(str(APK_SOURCE), str(APK_DEST))
    print(f"✓ APK copied: {APK_DEST} ({APK_DEST.stat().st_size // (1024*1024)}MB)")

HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AgentJW Remote</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: #0a0a0a; color: #fff; font-family: -apple-system, sans-serif; min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 20px; }}
.card {{ background: #111; border: 1px solid #222; border-radius: 16px; padding: 32px; max-width: 400px; width: 100%; text-align: center; }}
.logo {{ font-size: 64px; margin-bottom: 16px; }}
h1 {{ color: #00bcd4; font-size: 24px; margin-bottom: 8px; }}
.subtitle {{ color: #888; font-size: 14px; margin-bottom: 24px; }}
.version {{ background: #1a1a1a; border-radius: 8px; padding: 12px; margin-bottom: 24px; }}
.version-label {{ color: #666; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; }}
.version-value {{ color: #00bcd4; font-size: 14px; margin-top: 4px; }}
.btn {{ display: block; background: #00bcd4; color: #000; text-decoration: none; padding: 16px 32px; border-radius: 12px; font-size: 16px; font-weight: bold; margin-bottom: 12px; transition: opacity 0.2s; }}
.btn:hover {{ opacity: 0.8; }}
.btn-secondary {{ background: #1a1a1a; color: #00bcd4; border: 1px solid #00bcd4; }}
.features {{ text-align: left; margin: 24px 0; }}
.feature {{ display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid #1a1a1a; font-size: 13px; color: #ccc; }}
.feature:last-child {{ border-bottom: none; }}
.feature-icon {{ font-size: 18px; width: 24px; text-align: center; }}
.steps {{ background: #0d1117; border-radius: 8px; padding: 16px; text-align: left; margin-top: 16px; }}
.steps h3 {{ color: #00bcd4; font-size: 13px; margin-bottom: 12px; }}
.step {{ font-size: 12px; color: #888; margin-bottom: 8px; display: flex; gap: 8px; }}
.step-num {{ color: #00bcd4; font-weight: bold; min-width: 16px; }}
.status {{ display: inline-flex; align-items: center; gap: 6px; background: #0d2818; color: #00e676; padding: 6px 12px; border-radius: 20px; font-size: 12px; margin-bottom: 16px; }}
.dot {{ width: 8px; height: 8px; background: #00e676; border-radius: 50%; animation: pulse 2s infinite; }}
@keyframes pulse {{ 0%,100%{{ opacity:1 }} 50%{{ opacity:0.4 }} }}
</style>
</head>
<body>
<div class="card">
  <div class="logo">🤖</div>
  <h1>AgentJW Remote</h1>
  <p class="subtitle">GOD MODE Autonomous AI Engineer</p>
  <div class="status"><span class="dot"></span> API Server Active</div>
  <div class="version">
    <div class="version-label">Version</div>
    <div class="version-value">1.0.0 — GOD MODE</div>
  </div>
  <a href="/agentjw_remote.apk" class="btn">⬇️ Download APK (24.6 MB)</a>
  <a href="/api/status" class="btn btn-secondary" target="_blank">🔍 Check API Status</a>
  <div class="features">
    <div class="feature"><span class="feature-icon">💬</span> Chat dengan AgentJW</div>
    <div class="feature"><span class="feature-icon">📁</span> Baca & scan project files</div>
    <div class="feature"><span class="feature-icon">▶️</span> Jalankan trading bot</div>
    <div class="feature"><span class="feature-icon">🔧</span> Auto-repair project</div>
    <div class="feature"><span class="feature-icon">📊</span> Lihat log real-time</div>
    <div class="feature"><span class="feature-icon">📈</span> Check token Solana</div>
    <div class="feature"><span class="feature-icon">🔔</span> Notifikasi via Telegram</div>
  </div>
  <div class="steps">
    <h3>📱 Cara Install</h3>
    <div class="step"><span class="step-num">1.</span> Download APK di atas</div>
    <div class="step"><span class="step-num">2.</span> Aktifkan "Install dari sumber tidak dikenal"</div>
    <div class="step"><span class="step-num">3.</span> Install APK</div>
    <div class="step"><span class="step-num">4.</span> Buka app — auto connect ke VPS</div>
  </div>
</div>
</body>
</html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            body = HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)

        elif self.path == "/agentjw_remote.apk":
            if APK_DEST.exists():
                size = APK_DEST.stat().st_size
                self.send_response(200)
                self.send_header("Content-Type", "application/vnd.android.package-archive")
                self.send_header("Content-Disposition", "attachment; filename=agentjw_remote.apk")
                self.send_header("Content-Length", size)
                self.end_headers()
                with open(APK_DEST, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"APK not found")

        elif self.path == "/api/status":
            import json
            body = json.dumps({"status": "ok", "agent": "AgentJW GOD MODE"}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        print(f"[Download] {format % args}")


if __name__ == "__main__":
    port = 8080
    with socketserver.TCPServer(("0.0.0.0", port), Handler) as httpd:
        print(f"\n✅ Download server running!")
        print(f"   http://94.100.26.128:{port}/")
        print(f"   APK: http://94.100.26.128:{port}/agentjw_remote.apk\n")
        httpd.serve_forever()
