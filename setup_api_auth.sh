#!/bin/bash
# ============================================================
# Setup API Key Authentication — Server Side
# Generate key, simpan di .env, pasang middleware FastAPI
# ============================================================

set -e
ROOT="/home/dibs/agentjw"
API="$ROOT/api_server.py"
ENV="$ROOT/.env"

echo "======================================"
echo " Setup API Key Authentication"
echo "======================================"

# ── 1. Generate API key kalau belum ada ──
echo "[1/4] Generate API key..."

if grep -q "^SICUAN_API_KEY=" "$ENV" 2>/dev/null; then
    EXISTING_KEY=$(grep "^SICUAN_API_KEY=" "$ENV" | cut -d'=' -f2)
    echo "    ⚠ API key sudah ada di .env: $EXISTING_KEY"
    API_KEY="$EXISTING_KEY"
else
    API_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    echo "SICUAN_API_KEY=$API_KEY" >> "$ENV"
    echo "    ✓ API key baru di-generate dan disimpan ke .env"
fi

echo ""
echo "    ┌─────────────────────────────────────────────────┐"
echo "    │ API KEY: $API_KEY"
echo "    └─────────────────────────────────────────────────┘"
echo ""

# ── 2. Backup api_server.py ──
echo "[2/4] Backup api_server.py..."
cp "$API" "$API.bak_before_auth_$(date +%H%M%S)"
echo "    ✓ Backup dibuat"

# ── 3. Pasang middleware auth ──
echo "[3/4] Pasang auth middleware..."

python3 << PYEOF
from pathlib import Path

api = Path("$API")
text = api.read_text()

if "_verify_api_key" in text:
    print("    ⚠ Middleware auth sudah ada, skip")
else:
    OLD = '''app = FastAPI(title="AgentJW API", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])'''

    NEW = '''app = FastAPI(title="AgentJW API", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

# ── API Key Authentication ──
import os as _os
from fastapi import Request as _Request
from fastapi.responses import JSONResponse as _JSONResponse
from dotenv import load_dotenv as _load_dotenv
_load_dotenv()

_SICUAN_API_KEY = _os.getenv("SICUAN_API_KEY", "")

# Endpoint yang TIDAK perlu auth (publik)
_PUBLIC_PATHS = {
    "/health", "/", "/docs", "/openapi.json",
    "/docs/oauth2-redirect", "/redoc"
}

@app.middleware("http")
async def _verify_api_key(request: _Request, call_next):
    path = request.url.path

    # Lewati auth untuk endpoint publik & static files
    if path in _PUBLIC_PATHS or path.startswith("/uploads"):
        return await call_next(request)

    if not _SICUAN_API_KEY:
        # Kalau key belum diset, jangan block (fail-open utk dev)
        return await call_next(request)

    provided = request.headers.get("x-api-key", "")

    if provided != _SICUAN_API_KEY:
        return _JSONResponse(
            status_code=401,
            content={"detail": "Invalid or missing API key. Set header X-API-Key."}
        )

    return await call_next(request)
# ── END API Key Authentication ──'''

    text = text.replace(OLD, NEW, 1)
    api.write_text(text)
    print("    ✓ Middleware auth ditambahkan")
PYEOF

# ── 4. Syntax check & restart ──
echo ""
echo "[4/4] Syntax check & restart..."
cd "$ROOT" && source venv/bin/activate

python3 -c "import ast; ast.parse(open('api_server.py').read()); print('    ✓ Syntax OK')"

pkill -f "uvicorn api_server:app" 2>/dev/null || true
sleep 2
nohup uvicorn api_server:app --host 0.0.0.0 --port 18790 >> logs/api_server.log 2>&1 &
sleep 3
echo "    ✓ API server restarted (PID: $!)"

echo ""
echo "=== Test: tanpa API key (harus 401) ==="
curl -s -o /dev/null -w "  Status: %{http_code}\n" http://localhost:18790/api/status

echo ""
echo "=== Test: dengan API key (harus 200) ==="
curl -s -o /dev/null -w "  Status: %{http_code}\n" -H "X-API-Key: $API_KEY" http://localhost:18790/api/status

echo ""
echo "=== Test: health endpoint tanpa key (harus 200, publik) ==="
curl -s -o /dev/null -w "  Status: %{http_code}\n" http://localhost:18790/health

echo ""
echo "======================================"
echo " Setup selesai!"
echo ""
echo " API KEY KAMU (simpan baik-baik):"
echo " $API_KEY"
echo ""
echo " Endpoint publik (tanpa auth):"
echo "   /health, /, /docs, /openapi.json"
echo ""
echo " Semua endpoint lain butuh header:"
echo "   X-API-Key: $API_KEY"
echo ""
echo " Langkah selanjutnya:"
echo " Patch kode Flutter (agentjw_remote) supaya"
echo " kirim header ini di setiap request."
echo "======================================"
