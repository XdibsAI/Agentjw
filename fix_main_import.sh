#!/bin/bash
set -e
F="$HOME/agentjw_remote/lib/main.dart"

echo "======================================"
echo " Fix: tambah import config.dart di main.dart"
echo "======================================"

cp "$F" "$F.bak_import_$(date +%H%M%S)"
echo "✓ Backup dibuat"

echo ""
echo "=== Import yang ada sekarang ==="
grep "^import" "$F"

python3 << 'PYEOF'
from pathlib import Path

f = Path.home() / "agentjw_remote" / "lib" / "main.dart"
text = f.read_text()

if "import 'config.dart';" in text:
    print("\n    ⚠ Import sudah ada")
else:
    lines = text.split("\n")
    # cari baris import terakhir
    last_import_idx = max(
        i for i, line in enumerate(lines)
        if line.strip().startswith("import ")
    )
    lines.insert(last_import_idx + 1, "import 'config.dart';")
    text = "\n".join(lines)
    f.write_text(text)
    print("\n    ✓ import 'config.dart'; ditambahkan setelah import terakhir")
PYEOF

echo ""
echo "=== Verifikasi ulang semua file ==="
for f in main.dart media_tab.dart api_service.dart settings_screen.dart chat_tab.dart projects_tab.dart bot_status_tab.dart config.dart; do
    path="$HOME/agentjw_remote/lib/$f"
    [ -f "$path" ] || continue
    usage=$(grep -o "appConfig\." "$path" 2>/dev/null | wc -l)
    has_import=$(grep -c "import 'config.dart';" "$path" 2>/dev/null || true)
    has_import=${has_import:-0}
    if [ "$usage" -gt 0 ] && [ "$has_import" -eq 0 ]; then
        echo "  ✗ $f — PAKAI appConfig ($usage x) TAPI TIDAK IMPORT!"
    elif [ "$usage" -gt 0 ]; then
        echo "  ✓ $f — pakai appConfig ($usage x), import OK"
    else
        echo "  - $f — tidak pakai appConfig langsung"
    fi
done

echo ""
echo "=== Re-run flutter analyze (filter 'appConfig' only) ==="
cd "$HOME/agentjw_remote"
flutter analyze lib/ 2>&1 | grep -i "appConfig\|error •" || echo "  ✓ Tidak ada error tersisa terkait appConfig"
