#!/bin/bash
# ============================================================
# Patch api_service.dart — titik pusat, lebih rapi
# Cukup ubah _headers getter, semua method otomatis terlindungi
# ============================================================

set -e
LIB="$HOME/agentjw_remote/lib"
F="$LIB/api_service.dart"

echo "======================================"
echo " Patch api_service.dart (centralized)"
echo "======================================"

cp "$F" "$F.bak_auth_$(date +%H%M%S)"
echo "✓ Backup dibuat"

python3 << 'PYEOF'
from pathlib import Path

f = Path.home() / "agentjw_remote" / "lib" / "api_service.dart"
text = f.read_text()

if "appConfig.authHeaders" in text:
    print("    ⚠ Sudah dipatch sebelumnya, skip _headers patch")
else:
    OLD = '''  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    'Accept':       'application/json',
  };'''

    NEW = '''  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    'Accept':       'application/json',
    ...appConfig.authHeaders,
  };'''

    text = text.replace(OLD, NEW, 1)
    print("    ✓ _headers getter dipatch — semua _get/_post otomatis terlindungi")

# Patch uploadFile — pakai MultipartRequest, tidak lewat _headers
if "req.headers.addAll(appConfig.authHeaders)" not in text:
    OLD_UPLOAD = '''  Future<http.StreamedResponse> uploadFile(File file) async {
    final req = http.MultipartRequest("POST", Uri.parse("$base/media/upload"));
    req.files.add(await http.MultipartFile.fromPath("file", file.path));
    return req.send();
  }'''

    NEW_UPLOAD = '''  Future<http.StreamedResponse> uploadFile(File file) async {
    final req = http.MultipartRequest("POST", Uri.parse("$base/media/upload"));
    req.headers.addAll(appConfig.authHeaders);
    req.files.add(await http.MultipartFile.fromPath("file", file.path));
    return req.send();
  }'''

    if OLD_UPLOAD in text:
        text = text.replace(OLD_UPLOAD, NEW_UPLOAD, 1)
        print("    ✓ uploadFile() dipatch — multipart request juga terlindungi")
    else:
        print("    ⚠ Pattern uploadFile tidak cocok exact, cek manual")

f.write_text(text)
print("    ✓ api_service.dart disimpan")
PYEOF

echo ""
echo "=== Hasil patch ==="
grep -n "authHeaders\|_headers" "$F"

echo ""
echo "======================================"
echo " Selesai!"
echo ""
echo " api_service.dart sekarang otomatis kirim"
echo " X-API-Key di SEMUA method:"
echo "   getStatus, chat, build, videoPackage,"
echo "   videoSection, generateImage, generateVideo,"
echo "   listProjects, getProject, uploadFile, dll"
echo ""
echo " File lain (chat_tab, projects_tab, bot_status_tab)"
echo " yang pakai 'api' instance dari api_service.dart"
echo " TIDAK PERLU dipatch — otomatis ikut."
echo "======================================"
