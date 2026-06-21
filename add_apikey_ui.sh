#!/bin/bash
set -e
F="$HOME/agentjw_remote/lib/settings_screen.dart"

echo "======================================"
echo " Tambah UI API Key di Settings"
echo "======================================"

cp "$F" "$F.bak_ui_$(date +%H%M%S)"
echo "✓ Backup dibuat"

python3 << 'PYEOF'
from pathlib import Path

f = Path.home() / "agentjw_remote" / "lib" / "settings_screen.dart"
text = f.read_text()

# ── 1. Update _test() agar simpan API key juga ──
OLD_TEST = '''  Future<void> _test() async {
    final url = _urlCtrl.text.trim();
    if (url.isEmpty) return;
    setState(() { _testing = true; _status = "Testing..."; });
    try {
      await appConfig.setBaseUrl(url);
      final data = await api.getStatus();
      setState(() {
        _status = "✅ Connected! Model: \\${data['model'] ?? '?'}";
        _testing = false;
      });
    } catch (e) {
      setState(() { _status = "❌ Gagal: \\$e"; _testing = false; });
    }
  }'''

NEW_TEST = '''  Future<void> _test() async {
    final url = _urlCtrl.text.trim();
    final key = _apiKeyCtrl.text.trim();
    if (url.isEmpty) return;
    setState(() { _testing = true; _status = "Testing..."; });
    try {
      await appConfig.setBaseUrl(url);
      if (key.isNotEmpty) {
        await appConfig.setApiKey(key);
      }
      final data = await api.getStatus();
      setState(() {
        _status = "✅ Connected! Model: \\${data['model'] ?? '?'}";
        _testing = false;
      });
    } catch (e) {
      setState(() { _status = "❌ Gagal: \\$e"; _testing = false; });
    }
  }'''

if OLD_TEST in text:
    text = text.replace(OLD_TEST, NEW_TEST, 1)
    print("    ✓ Method _test() diupdate — sekarang simpan API key juga")
else:
    print("    ⚠ Pattern _test() tidak exact match, cek manual")

# ── 2. Tambah TextField API Key setelah field URL + spacing ──
OLD_UI = '''          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: _testing ? null : _test,'''

NEW_UI = '''          const SizedBox(height: 20),
          const Text("API KEY",
            style: TextStyle(color: Colors.grey, fontSize: 11, letterSpacing: 1.2)),
          const SizedBox(height: 6),
          TextField(
            controller: _apiKeyCtrl,
            obscureText: true,
            style: const TextStyle(color: Colors.white, fontSize: 13),
            decoration: InputDecoration(
              hintText: "X-API-Key dari server",
              hintStyle: const TextStyle(color: Colors.grey, fontSize: 12),
              filled: true, fillColor: const Color(0xFF141414),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(10),
                borderSide: const BorderSide(color: Color(0xFF2A2A4A))),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(10),
                borderSide: const BorderSide(color: Color(0xFF2A2A4A))),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(10),
                borderSide: const BorderSide(color: Color(0xFF7C3AED), width: 1.5)),
              suffixIcon: IconButton(
                icon: const Icon(Icons.clear, size: 18, color: Colors.grey),
                onPressed: () => _apiKeyCtrl.clear()),
            ),
          ),
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: _testing ? null : _test,'''

if OLD_UI in text:
    text = text.replace(OLD_UI, NEW_UI, 1)
    print("    ✓ TextField API Key ditambahkan ke UI")
else:
    print("    ⚠ Pattern UI tidak exact match, cek manual")

# ── 3. Update tips text ──
OLD_TIPS = '''          const Text(
            "• Format URL: http://IP_VPS:18790\\n"
            "• Jangan pakai trailing slash\\n"
            "• Pastikan port 18790 terbuka di firewall VPS\\n"
            "• Start backend: cd ~/agentjw && bash fix_api_server.sh",
            style: TextStyle(color: Colors.grey, fontSize: 11, height: 1.6)),'''

NEW_TIPS = '''          const Text(
            "• Format URL: http://IP_VPS:18790\\n"
            "• Jangan pakai trailing slash\\n"
            "• API Key didapat dari server (.env SICUAN_API_KEY)\\n"
            "• Pastikan port 18790 terbuka di firewall VPS\\n"
            "• Start backend: cd ~/agentjw && bash fix_api_server.sh",
            style: TextStyle(color: Colors.grey, fontSize: 11, height: 1.6)),'''

if OLD_TIPS in text:
    text = text.replace(OLD_TIPS, NEW_TIPS, 1)
    print("    ✓ Tips text diupdate")
else:
    print("    ⚠ Tips text tidak exact match, skip (tidak fatal)")

f.write_text(text)
print("    ✓ settings_screen.dart disimpan")
PYEOF

echo ""
echo "=== Syntax check (dart analyze file ini saja) ==="
cd "$HOME/agentjw_remote"
flutter analyze lib/settings_screen.dart 2>&1 | grep -i "error" || echo "  ✓ Tidak ada error"

echo ""
echo "======================================"
echo " Selesai!"
echo " Field API Key sudah muncul di Settings,"
echo " obscured (seperti password), dengan tombol clear."
echo "======================================"
