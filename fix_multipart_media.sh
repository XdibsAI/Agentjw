#!/bin/bash
# ============================================================
# Fix: tambah authHeaders ke MultipartRequest di media_tab.dart
# yang terlewat dari patch regex sebelumnya
# ============================================================

set -e
F="$HOME/agentjw_remote/lib/media_tab.dart"

echo "======================================"
echo " Fix MultipartRequest di media_tab.dart"
echo "======================================"

cp "$F" "$F.bak_multipart_$(date +%H%M%S)"
echo "✓ Backup dibuat"

python3 << 'PYEOF'
from pathlib import Path

f = Path.home() / "agentjw_remote" / "lib" / "media_tab.dart"
text = f.read_text()

OLD = """        final request = http.MultipartRequest(
          'POST', Uri.parse('${widget.baseUrl}/media/upload'));
        request.files.add(await http.MultipartFile.fromPath('file', _pickedImage!.path));"""

NEW = """        final request = http.MultipartRequest(
          'POST', Uri.parse('${widget.baseUrl}/media/upload'));
        request.headers.addAll(appConfig.authHeaders);
        request.files.add(await http.MultipartFile.fromPath('file', _pickedImage!.path));"""

if "request.headers.addAll(appConfig.authHeaders)" in text:
    print("    ⚠ Sudah dipatch, skip")
elif OLD in text:
    text = text.replace(OLD, NEW, 1)
    f.write_text(text)
    print("    ✓ MultipartRequest di media_tab.dart dipatch")
else:
    print("    ✗ Pattern tidak ditemukan exact — cek manual baris MultipartRequest")
PYEOF

echo ""
echo "=== Verifikasi ==="
grep -B2 -A6 "MultipartRequest" "$F"

echo ""
echo "=== Cek import appConfig di media_tab.dart ==="
grep -n "^import\|appConfig" "$F" | head -5
