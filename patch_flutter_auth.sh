#!/bin/bash
# ============================================================
# Patch Flutter (agentjw_remote) — kirim X-API-Key di semua request
# Jalankan di dalam VPS, di folder ~/agentjw_remote
# ============================================================

set -e
ROOT="$HOME/agentjw_remote"
LIB="$ROOT/lib"
API_KEY="ibnm8ap2nr247nCF3IhhXHzoct96TbkImpuk-GqvaDU"

echo "======================================"
echo " Patch Flutter — API Key Auth"
echo "======================================"

if [ ! -d "$LIB" ]; then
    echo "✗ Folder $LIB tidak ditemukan!"
    exit 1
fi

# ── Backup semua file dart dulu ──
BACKUP_DIR="$ROOT/lib_backup_$(date +%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp "$LIB"/*.dart "$BACKUP_DIR/" 2>/dev/null || true
echo "✓ Backup lib/*.dart ke $BACKUP_DIR"

# ─────────────────────────────────────────
# 1. Patch config.dart — tambah apiKey getter
# ─────────────────────────────────────────
echo "[1/3] Patch config.dart..."

python3 << PYEOF
from pathlib import Path

f = Path("$LIB/config.dart")
text = f.read_text()

if "_apiKey" in text:
    print("    ⚠ apiKey sudah ada, skip")
else:
    # Tambah const default key
    text = text.replace(
        'static const String _defaultUrl = "http://94.100.26.128:18790";',
        'static const String _defaultUrl = "http://94.100.26.128:18790";\n  static const String _defaultApiKey = "$API_KEY";\n  static const String _prefApiKeyKey = "sicuan_api_key";'
    )

    # Tambah field _apiKey setelah _baseUrl
    text = text.replace(
        'String _baseUrl = _defaultUrl;\n  String get baseUrl => _baseUrl;',
        'String _baseUrl = _defaultUrl;\n  String get baseUrl => _baseUrl;\n\n  String _apiKey = _defaultApiKey;\n  String get apiKey => _apiKey;\n\n  Map<String, String> get authHeaders => {"X-API-Key": _apiKey};'
    )

    # Load apiKey saat load() dipanggil (cari method load())
    text = text.replace(
        '_baseUrl = prefs.getString(_prefKey) ?? _defaultUrl;',
        '_baseUrl = prefs.getString(_prefKey) ?? _defaultUrl;\n    _apiKey = prefs.getString(_prefApiKeyKey) ?? _defaultApiKey;'
    )

    # Tambah method setApiKey setelah method set baseUrl (cari pattern await prefs.setString(_prefKey, _baseUrl);)
    text = text.replace(
        'await prefs.setString(_prefKey, _baseUrl);',
        'await prefs.setString(_prefKey, _baseUrl);\n  }\n\n  Future<void> setApiKey(String key) async {\n    _apiKey = key.trim();\n    final prefs = await SharedPreferences.getInstance();\n    await prefs.setString(_prefApiKeyKey, _apiKey);'
    )

    f.write_text(text)
    print("    ✓ config.dart dipatch")
PYEOF

# ─────────────────────────────────────────
# 2. Patch semua file yang panggil http.get/http.post
#    Tambah headers: appConfig.authHeaders
# ─────────────────────────────────────────
echo "[2/3] Patch http calls di semua file..."

python3 << 'PYEOF'
import re
from pathlib import Path

LIB = Path.home() / "agentjw_remote" / "lib"

# File-file yang perlu dipatch (yang ada http call)
target_files = [
    "main.dart", "chat_tab.dart", "media_tab.dart",
    "projects_tab.dart", "bot_status_tab.dart"
]

patched_count = 0

for fname in target_files:
    f = LIB / fname
    if not f.exists():
        print(f"    ⚠ {fname} tidak ditemukan, skip")
        continue

    text = f.read_text()
    original = text

    # Pattern 1: http.get(Uri.parse(...)).timeout(...)
    # Tambah headers: appConfig.authHeaders sebagai parameter kedua
    text = re.sub(
        r'http\.get\((Uri\.parse\([^)]+\))\)',
        r'http.get(\1, headers: appConfig.authHeaders)',
        text
    )

    # Pattern 2: http.post(Uri.parse(...), headers: {...}, body: ...)
    # Cari http.post yang SUDAH punya headers: { ... }
    def merge_post_headers(match):
        full = match.group(0)
        if 'appConfig.authHeaders' in full:
            return full
        # Cari headers: {...} dan merge
        headers_match = re.search(r'headers:\s*\{([^}]*)\}', full)
        if headers_match:
            old_headers = headers_match.group(1)
            new_headers = f'{{...appConfig.authHeaders, {old_headers}}}'
            full = full.replace(f'headers: {{{old_headers}}}', f'headers: {new_headers}')
        return full

    # http.post(...) yang multi-line — cari blok dari http.post( sampai ); penutup
    text = re.sub(
        r'http\.post\([^;]*?;',
        merge_post_headers,
        text,
        flags=re.DOTALL
    )

    # Pattern 3: http.Request('POST', ...) lalu .headers
    # Cari: final req = http.Request('POST', Uri.parse(...));
    text = re.sub(
        r"(http\.Request\('POST',\s*Uri\.parse\([^)]+\)\));",
        r"\1;\n          req.headers.addAll(appConfig.authHeaders);",
        text
    )

    if text != original:
        f.write_text(text)
        patched_count += 1
        print(f"    ✓ {fname} dipatch")
    else:
        print(f"    - {fname} tidak ada perubahan (mungkin tidak ada http call langsung)")

print(f"\n  Total file dipatch: {patched_count}")
PYEOF

# ─────────────────────────────────────────
# 3. Tambah input API Key di settings_screen.dart
# ─────────────────────────────────────────
echo "[3/3] Patch settings_screen.dart — tambah field API Key..."

python3 << 'PYEOF'
from pathlib import Path

f = Path.home() / "agentjw_remote" / "lib" / "settings_screen.dart"
text = f.read_text()

if "_apiKeyCtrl" in text:
    print("    ⚠ Field API Key sudah ada, skip")
else:
    # Tambah controller baru setelah _urlCtrl
    text = text.replace(
        "late final _urlCtrl = TextEditingController(text: appConfig.baseUrl);",
        "late final _urlCtrl = TextEditingController(text: appConfig.baseUrl);\n  late final _apiKeyCtrl = TextEditingController(text: appConfig.apiKey);"
    )
    f.write_text(text)
    print("    ✓ Controller _apiKeyCtrl ditambahkan")
    print("    ⚠ MANUAL: Tambahkan TextField untuk _apiKeyCtrl di UI build(),")
    print("      dan panggil appConfig.setApiKey(_apiKeyCtrl.text) saat save.")
    print("      Cek instruksi lengkap di akhir output script ini.")
PYEOF

echo ""
echo "=== Verifikasi: cek apakah authHeaders sudah dipakai ==="
grep -rn "appConfig.authHeaders" "$LIB"/*.dart | wc -l
echo "kali ditemukan di file dart"

echo ""
echo "======================================"
echo " Patch selesai!"
echo ""
echo " API Key sudah di-embed sebagai default"
echo " di config.dart:"
echo "   $API_KEY"
echo ""
echo " PENTING — perlu cek manual:"
echo " 1. Review hasil patch di setiap file"
echo "    (terutama media_tab.dart yang banyak http.post)"
echo " 2. Tambahkan TextField API Key di settings_screen.dart"
echo "    UI build() method — controller sudah disiapkan:"
echo "    _apiKeyCtrl"
echo " 3. Setelah review, build APK:"
echo "    flutter clean && flutter pub get"
echo "    flutter build apk --release"
echo ""
echo " Backup tersimpan di:"
echo "   $BACKUP_DIR"
echo "======================================"
