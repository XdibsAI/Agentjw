#!/bin/bash
# ════════════════════════════════════════════════════════════════════
# agentjw_fix_all.sh
# Fix LENGKAP: Backend + Flutter APK AgentJW
#
# Jalankan dari server VPS:
#   bash agentjw_fix_all.sh
#
# Atau dengan opsi:
#   bash agentjw_fix_all.sh --apk-dir ~/agentjw_apk --apply
#
# Apa yang dilakukan script ini:
#   1. Cek & install Python deps (rich, requests)
#   2. Jalankan sync analyzer (agentjw_sync_analyzer_fixed.py)
#   3. Jalankan APK fixer      (agentjw_apk_fixer.py)
#   4. Jalankan Flutter patcher (agentjw_flutter_patcher.py)
#   5. Restart api_server dengan port 18790
#   6. Test semua endpoint
#   7. Buat ringkasan fix
# ════════════════════════════════════════════════════════════════════

set -e

# ── Warna ────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

ok()   { echo -e "  ${GREEN}✅ $1${RESET}"; }
err()  { echo -e "  ${RED}❌ $1${RESET}"; }
warn() { echo -e "  ${YELLOW}⚠️  $1${RESET}"; }
info() { echo -e "  ${CYAN}ℹ  $1${RESET}"; }
h()    { echo -e "\n${BOLD}${CYAN}──────────────────────────────────────────${RESET}"; \
         echo -e "${BOLD}${CYAN}  $1${RESET}"; \
         echo -e "${BOLD}${CYAN}──────────────────────────────────────────${RESET}"; }

# ── Default paths ─────────────────────────────────────────────────
BACKEND_DIR="${HOME}/agentjw"
APK_DIR="${HOME}/agentjw_apk"
APPLY_FLAG=""
SKIP_FLUTTER=false

# ── Parse args ────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --backend-dir) BACKEND_DIR="$2"; shift 2 ;;
        --apk-dir)     APK_DIR="$2";     shift 2 ;;
        --apply)       APPLY_FLAG="--apply"; shift ;;
        --skip-flutter) SKIP_FLUTTER=true; shift ;;
        *) shift ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="${BACKEND_DIR}/logs/fix_all_${TIMESTAMP}.log"

mkdir -p "${BACKEND_DIR}/logs"

echo ""
echo -e "${BOLD}${CYAN}"
echo "  ╔══════════════════════════════════════════════════════════╗"
echo "  ║   AgentJW Complete Fix — Backend + Flutter APK         ║"
echo "  ╚══════════════════════════════════════════════════════════╝"
echo -e "${RESET}"
echo "  Backend  : ${BACKEND_DIR}"
echo "  Flutter  : ${APK_DIR}"
echo "  Log      : ${LOG_FILE}"
echo "  Apply    : ${APPLY_FLAG:-dry-run (tambah --apply untuk patch)}"
echo ""

# ════════════════════════════════════════════════════════════════════
# STEP 0: Prerequisite check
# ════════════════════════════════════════════════════════════════════
h "STEP 0: Prerequisite Check"

if [ ! -d "${BACKEND_DIR}" ]; then
    err "Backend dir tidak ditemukan: ${BACKEND_DIR}"
    echo "  Gunakan: --backend-dir /path/ke/agentjw"
    exit 1
fi
ok "Backend dir: ${BACKEND_DIR}"

# Python
if ! command -v python3 &>/dev/null; then
    err "Python3 tidak ditemukan"
    exit 1
fi
ok "Python3: $(python3 --version)"

# venv
if [ -f "${BACKEND_DIR}/venv/bin/activate" ]; then
    source "${BACKEND_DIR}/venv/bin/activate" 2>/dev/null || true
    ok "venv aktif"
else
    warn "venv tidak ditemukan — gunakan Python system"
fi

# Install rich (optional tapi bagus untuk output)
python3 -c "import rich" 2>/dev/null || {
    info "Install rich untuk output lebih baik..."
    pip install rich -q 2>/dev/null || true
}

# Flutter
if command -v flutter &>/dev/null; then
    ok "Flutter: $(flutter --version 2>/dev/null | head -1)"
else
    warn "Flutter tidak ditemukan di PATH — skip flutter pub get"
    SKIP_FLUTTER=true
fi

# curl
if ! command -v curl &>/dev/null; then
    warn "curl tidak ditemukan — skip HTTP tests"
fi

# ════════════════════════════════════════════════════════════════════
# STEP 1: Backend Sync Analyzer
# ════════════════════════════════════════════════════════════════════
h "STEP 1: Backend Sync Analyzer"

cd "${BACKEND_DIR}"

SYNC_SCRIPT=""
for f in \
    "${SCRIPT_DIR}/agentjw_sync_analyzer_fixed_0_.py" \
    "${SCRIPT_DIR}/agentjw_sync_analyzer_fixed.py" \
    "${SCRIPT_DIR}/agentjw_sync_analyzer.py" \
    "${BACKEND_DIR}/agentjw_sync_analyzer_fixed.py" \
    "${BACKEND_DIR}/agentjw_sync_analyzer.py"; do
    if [ -f "$f" ]; then
        SYNC_SCRIPT="$f"
        break
    fi
done

if [ -n "${SYNC_SCRIPT}" ]; then
    info "Menjalankan: $(basename ${SYNC_SCRIPT})"
    python3 "${SYNC_SCRIPT}" --patch 2>&1 | tee -a "${LOG_FILE}" || warn "Sync analyzer selesai dengan warning"
    ok "Sync analyzer selesai"
else
    warn "Sync analyzer tidak ditemukan — lewati step ini"
fi

# ════════════════════════════════════════════════════════════════════
# STEP 2: APK Fixer (Analyze)
# ════════════════════════════════════════════════════════════════════
h "STEP 2: APK Endpoint & Feature Fixer"

APK_FIXER="${SCRIPT_DIR}/agentjw_apk_fixer.py"
if [ ! -f "${APK_FIXER}" ]; then
    APK_FIXER="${BACKEND_DIR}/agentjw_apk_fixer.py"
fi

if [ -f "${APK_FIXER}" ]; then
    info "Menjalankan APK fixer..."
    python3 "${APK_FIXER}" \
        --backend-dir "${BACKEND_DIR}" \
        --apk-dir "${APK_DIR}" \
        --patch \
        --verbose \
        2>&1 | tee -a "${LOG_FILE}" || warn "APK fixer selesai dengan warning"
    ok "APK fixer selesai"
else
    warn "agentjw_apk_fixer.py tidak ditemukan"
fi

# ════════════════════════════════════════════════════════════════════
# STEP 3: Flutter Patcher (Generate Dart files + backend routes)
# ════════════════════════════════════════════════════════════════════
h "STEP 3: Flutter Dart Patcher"

FLUTTER_PATCHER="${SCRIPT_DIR}/agentjw_flutter_patcher.py"
if [ ! -f "${FLUTTER_PATCHER}" ]; then
    FLUTTER_PATCHER="${BACKEND_DIR}/agentjw_flutter_patcher.py"
fi

if [ -f "${FLUTTER_PATCHER}" ]; then
    PATCHER_ARGS="--apk-dir ${APK_DIR} --backend-dir ${BACKEND_DIR}"
    if [ -n "${APPLY_FLAG}" ]; then
        PATCHER_ARGS="${PATCHER_ARGS} --apply"
    fi
    info "Menjalankan Flutter patcher..."
    python3 "${FLUTTER_PATCHER}" ${PATCHER_ARGS} 2>&1 | tee -a "${LOG_FILE}" || warn "Flutter patcher selesai dengan warning"
    ok "Flutter patcher selesai"
else
    warn "agentjw_flutter_patcher.py tidak ditemukan"
fi

# ════════════════════════════════════════════════════════════════════
# STEP 4: Backend restart
# ════════════════════════════════════════════════════════════════════
h "STEP 4: Restart Backend (port 18790)"

cd "${BACKEND_DIR}"

# Kill existing
pkill -f "api_server.py" 2>/dev/null && info "api_server lama dihentikan" || true
pkill -f "uvicorn api_server" 2>/dev/null || true
sleep 1

# Ensure .env has correct port
if [ -f ".env" ]; then
    if grep -q "API_PORT=8000" .env; then
        sed -i 's/API_PORT=8000/API_PORT=18790/' .env
        ok ".env: API_PORT diperbaiki ke 18790"
    elif ! grep -q "API_PORT" .env; then
        echo "API_PORT=18790" >> .env
        ok ".env: API_PORT=18790 ditambahkan"
    fi
fi

# Start server
mkdir -p logs
if command -v uvicorn &>/dev/null || python3 -c "import uvicorn" 2>/dev/null; then
    nohup python3 -m uvicorn api_server:app \
        --host 0.0.0.0 \
        --port 18790 \
        --log-level info \
        > logs/api_server.log 2>&1 &
    SERVER_PID=$!
    echo "${SERVER_PID}" > logs/api_server.pid
    ok "api_server started (PID: ${SERVER_PID}, port: 18790)"
    sleep 2
else
    err "uvicorn tidak ditemukan"
    warn "Install: pip install uvicorn fastapi"
fi

# ════════════════════════════════════════════════════════════════════
# STEP 5: Endpoint Tests
# ════════════════════════════════════════════════════════════════════
h "STEP 5: Live Endpoint Tests"

PORT=18790
BASE="http://localhost:${PORT}"

test_endpoint() {
    local method="$1"
    local path="$2"
    local data="$3"
    local label="$4"

    if ! command -v curl &>/dev/null; then
        warn "curl tidak ada — skip test ${label}"
        return
    fi

    if [ -n "${data}" ]; then
        CODE=$(curl -s -o /tmp/agentjw_test.json \
            -w "%{http_code}" \
            -X "${method}" \
            -H "Content-Type: application/json" \
            -d "${data}" \
            --max-time 8 \
            "${BASE}${path}" 2>/dev/null)
    else
        CODE=$(curl -s -o /tmp/agentjw_test.json \
            -w "%{http_code}" \
            -X "${method}" \
            --max-time 8 \
            "${BASE}${path}" 2>/dev/null)
    fi

    if [[ "${CODE}" == "200" || "${CODE}" == "201" ]]; then
        ok "[${CODE}] ${method} ${path} — ${label}"
    elif [[ "${CODE}" == "422" ]]; then
        warn "[${CODE}] ${method} ${path} — ${label} (validation error — endpoint ada)"
    elif [[ "${CODE}" == "404" ]]; then
        err "[${CODE}] ${method} ${path} — ${label} (ENDPOINT TIDAK ADA)"
    elif [[ "${CODE}" == "500" ]]; then
        err "[${CODE}] ${method} ${path} — ${label} (SERVER ERROR)"
        cat /tmp/agentjw_test.json 2>/dev/null | head -3
    else
        warn "[${CODE:-NO_RESP}] ${method} ${path} — ${label}"
    fi
}

# Core backend
test_endpoint "GET"  "/api/status"   "" "Health check"
test_endpoint "GET"  "/health"       "" "Alt health"
test_endpoint "GET"  "/projects"     "" "Projects list"

# Chat / LLM
test_endpoint "POST" "/api/agent" \
    '{"message":"halo","session_id":"test","history":[],"mode":"chat"}' \
    "LLM Chat (api/agent)"

# Video studio
test_endpoint "GET"  "/video/projects" "" "Video projects"

# Media routes (baru ditambah)
test_endpoint "GET"  "/media/gallery"  "" "Media gallery"
test_endpoint "POST" "/media/image/generate" \
    '{"prompt":"test prompt","model":"fal-ai/flux/schnell","image_size":"landscape_16_9"}' \
    "Image generate"
test_endpoint "POST" "/media/video/generate" \
    '{"image_url":"https://example.com/test.jpg","model":"fal-ai/kling-video/v1.6/standard/image-to-video"}' \
    "Video generate"

# ════════════════════════════════════════════════════════════════════
# STEP 6: Flutter pub get
# ════════════════════════════════════════════════════════════════════
h "STEP 6: Flutter Pub Get"

if [ "${SKIP_FLUTTER}" = false ] && [ -d "${APK_DIR}" ]; then
    cd "${APK_DIR}"
    info "Running flutter pub get..."
    flutter pub get 2>&1 | tail -5
    ok "flutter pub get selesai"
    cd "${BACKEND_DIR}"
else
    if [ "${SKIP_FLUTTER}" = true ]; then
        warn "Flutter skipped (tidak ditemukan di PATH)"
    else
        warn "Flutter APK dir tidak ditemukan: ${APK_DIR}"
    fi
    info "Jalankan manual: cd ${APK_DIR} && flutter pub get"
fi

# ════════════════════════════════════════════════════════════════════
# STEP 7: Summary
# ════════════════════════════════════════════════════════════════════
h "SUMMARY & NEXT STEPS"

echo ""
echo -e "${BOLD}  File yang di-generate/patch:${RESET}"
echo "  Backend:"
echo "    ~/agentjw/api_server.py        ← +media routes"
echo "    ~/agentjw/logs/                ← reports"
echo ""
echo "  Flutter APK:"
echo "    lib/config.dart               ← Base URL management"
echo "    lib/api_service.dart          ← Centralized HTTP client"
echo "    lib/chat_tab.dart             ← LLM chat UI lengkap"
echo "    lib/bot_status_tab.dart       ← Backend monitor"
echo "    lib/projects_tab.dart         ← Project browser"
echo "    lib/settings_screen.dart      ← Ganti IP server"
echo ""
echo -e "${BOLD}  Endpoint tersedia di backend:${RESET}"
echo "    GET  /api/status              ← health check APK"
echo "    POST /api/agent               ← LLM chat/build/video"
echo "    GET  /projects                ← list projects"
echo "    POST /video/package           ← video studio"
echo "    POST /media/image/generate    ← image generation"
echo "    POST /media/upload            ← upload image"
echo "    POST /media/video/generate    ← video dari image"
echo "    GET  /media/video/jobs/{id}   ← poll job status"
echo "    GET  /media/gallery           ← gallery APK"
echo ""
echo -e "${BOLD}  Yang perlu dilakukan MANUAL:${RESET}"
echo ""
echo "  1. Set IP VPS di APK:"
echo "     Edit lib/config.dart → ganti YOUR_VPS_IP"
echo "     ATAU buka Settings di APK → masukkan URL"
echo ""
echo "  2. Set API keys di .env:"
echo "     nano ~/agentjw/.env"
echo "     ANTHROPIC_API_KEY=sk-ant-..."
echo "     FAL_API_KEY=...  (untuk image/video gen)"
echo ""
echo "  3. Install fal-client:"
echo "     pip install fal-client"
echo ""
echo "  4. Pasang semua Tab di main.dart:"
echo "     Pastikan import semua file baru"
echo "     Tambah MediaTab, SettingsScreen ke nav"
echo ""
echo "  5. Build & install APK:"
echo "     cd ${APK_DIR}"
echo "     flutter build apk --release"
echo "     adb install build/app/outputs/flutter-apk/app-release.apk"
echo ""
echo -e "${BOLD}  Test backend manual:${RESET}"
echo "    curl http://localhost:18790/api/status"
echo "    curl http://localhost:18790/media/gallery"
echo ""
echo "  Log lengkap: ${LOG_FILE}"
echo ""
ok "agentjw_fix_all.sh selesai!"
echo ""
