#!/bin/bash
set -e
F="$HOME/agentjw_remote/lib/media_tab.dart"

echo "======================================"
echo " Tambah import config.dart"
echo "======================================"

cp "$F" "$F.bak_import_$(date +%H%M%S)"
echo "✓ Backup dibuat"

python3 << 'PYEOF'
from pathlib import Path

f = Path.home() / "agentjw_remote" / "lib" / "media_tab.dart"
text = f.read_text()

if "import 'config.dart';" in text:
    print("    ⚠ Import sudah ada, skip")
else:
    OLD = "import 'package:http/http.dart' as http;"
    NEW = "import 'package:http/http.dart' as http;\nimport 'config.dart';"
    text = text.replace(OLD, NEW, 1)
    f.write_text(text)
    print("    ✓ import 'config.dart'; ditambahkan")
PYEOF

echo ""
echo "=== Verifikasi import di semua file yang pakai appConfig ==="
for f in main.dart media_tab.dart api_service.dart settings_screen.dart; do
    path="$HOME/agentjw_remote/lib/$f"
    has_usage=$(grep -c "appConfig\." "$path" 2>/dev/null || echo 0)
    has_import=$(grep -c "import 'config.dart';" "$path" 2>/dev/null || echo 0)
    if [ "$has_usage" -gt 0 ] && [ "$has_import" -eq 0 ]; then
        echo "  ✗ $f — PAKAI appConfig TAPI TIDAK IMPORT!"
    elif [ "$has_usage" -gt 0 ]; then
        echo "  ✓ $f — pakai appConfig, import OK"
    else
        echo "  - $f — tidak pakai appConfig"
    fi
done
