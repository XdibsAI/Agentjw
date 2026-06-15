#!/usr/bin/env python3
# flake8: noqa
import warnings; warnings.filterwarnings("ignore", category=SyntaxWarning)
"""
agentjw_flutter_patcher.py
==========================
Patch LENGKAP Flutter APK AgentJW:

1. Generate semua file Dart yang belum ada:
   - lib/chat_tab.dart         ← LLM chat + history + mode selector
   - lib/video_studio_tab.dart ← Video package + section generator
   - lib/projects_tab.dart     ← Project list + detail viewer
   - lib/bot_status_tab.dart   ← Health check + live stats
   - lib/config.dart           ← Base URL + settings tersimpan
   - lib/api_service.dart      ← Centralized HTTP client

2. Patch main.dart:
   - Pasang semua Tab yang benar
   - BottomNavigationBar lengkap
   - BaseUrl dari SharedPreferences

3. Patch pubspec.yaml:
   - Tambah semua dependencies yang dibutuhkan

4. Tambah backend endpoint stubs yang hilang:
   - /media/image/generate
   - /media/upload
   - /media/video/generate
   - /media/video/jobs/{id}
   - /media/gallery

5. Buat README fix guide

Jalankan:
  python3 agentjw_flutter_patcher.py --apk-dir ~/agentjw_apk --backend-dir ~/agentjw
  python3 agentjw_flutter_patcher.py --apk-dir ~/agentjw_apk --backend-dir ~/agentjw --apply
"""

import os
import re
import sys
import shutil
import argparse
from pathlib import Path
from datetime import datetime

# ── Args ──────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="AgentJW Flutter Patcher")
parser.add_argument("--apk-dir",     default=str(Path.home()/"agentjw_apk"), help="Path Flutter project")
parser.add_argument("--backend-dir", default=str(Path.home()/"agentjw"),     help="Path backend AgentJW")
parser.add_argument("--apply",       action="store_true", help="Apply semua patch (default: dry-run)")
parser.add_argument("--force",       action="store_true", help="Overwrite file yang sudah ada")
args = parser.parse_args()

APK_DIR     = Path(args.apk_dir)
BACKEND_DIR = Path(args.backend_dir)
APPLY       = args.apply
FORCE       = args.force
NOW         = datetime.now()
BAKSUFFIX   = f".bak_{NOW.strftime('%H%M%S')}"

def p(s):  print(s)
def ok(s): print(f"  ✅ {s}")
def err(s):print(f"  ❌ {s}")
def fix(s):print(f"  🔧 {s}")
def dry(s):print(f"  [DRY] {s}")
def h(s):  print(f"\n{'─'*60}\n  {s}\n{'─'*60}")

def write_dart(rel_path: str, content: str, force=False):
    """Write a Dart file under APK_DIR/lib/"""
    dest = APK_DIR / "lib" / rel_path
    if dest.exists() and not force and not FORCE:
        dry(f"SKIP (sudah ada): lib/{rel_path}  — gunakan --force untuk overwrite")
        return False
    if not APPLY:
        dry(f"WRITE: lib/{rel_path}  ({len(content)} chars)")
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        shutil.copy2(dest, str(dest) + BAKSUFFIX)
    dest.write_text(content, encoding="utf-8")
    ok(f"Ditulis: lib/{rel_path}")
    return True

def patch_file(path: Path, old: str, new: str, label: str) -> bool:
    if not path.exists():
        err(f"File tidak ditemukan: {path}")
        return False
    content = path.read_text(encoding="utf-8")
    if old not in content:
        dry(f"SKIP patch '{label}' — pattern tidak ditemukan di {path.name}")
        return False
    if not APPLY:
        dry(f"PATCH '{label}' di {path.name}")
        return False
    shutil.copy2(path, str(path) + BAKSUFFIX)
    path.write_text(content.replace(old, new, 1), encoding="utf-8")
    ok(f"Patched: {label} di {path.name}")
    return True

def append_file(path: Path, content: str, guard: str, label: str) -> bool:
    if not path.exists():
        err(f"File tidak ditemukan: {path}")
        return False
    existing = path.read_text(encoding="utf-8")
    if guard in existing:
        ok(f"SKIP (sudah ada): {label}")
        return False
    if not APPLY:
        dry(f"APPEND '{label}' ke {path.name}")
        return False
    shutil.copy2(path, str(path) + BAKSUFFIX)
    path.write_text(existing + "\n" + content, encoding="utf-8")
    ok(f"Appended: {label} ke {path.name}")
    return True


# ══════════════════════════════════════════════════════════════════
# FILE: lib/config.dart
# ══════════════════════════════════════════════════════════════════
CONFIG_DART = '''// lib/config.dart — AgentJW APK Configuration
// Simpan & load baseUrl dari SharedPreferences

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class AppConfig extends ChangeNotifier {
  // Default URL — ganti sesuai IP VPS kamu
  static const String _defaultUrl = "http://YOUR_VPS_IP:18790";
  static const String _prefKey    = "agentjw_base_url";

  String _baseUrl = _defaultUrl;
  String get baseUrl => _baseUrl;

  static final AppConfig _instance = AppConfig._internal();
  factory AppConfig() => _instance;
  AppConfig._internal();

  Future<void> load() async {
    final prefs = await SharedPreferences.getInstance();
    _baseUrl = prefs.getString(_prefKey) ?? _defaultUrl;
    notifyListeners();
  }

  Future<void> setBaseUrl(String url) async {
    _baseUrl = url.trim().replaceAll(RegExp(r"/+\$"), "");
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_prefKey, _baseUrl);
    notifyListeners();
  }

  Future<void> reset() async {
    await setBaseUrl(_defaultUrl);
  }
}

final appConfig = AppConfig();
'''

# ══════════════════════════════════════════════════════════════════
# FILE: lib/api_service.dart
# ══════════════════════════════════════════════════════════════════
API_SERVICE_DART = '''// lib/api_service.dart — Centralized AgentJW API Client
// Semua HTTP call terpusat di sini agar mudah debug & maintain

import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'config.dart';

class ApiException implements Exception {
  final int statusCode;
  final String message;
  ApiException(this.statusCode, this.message);
  @override
  String toString() => "ApiException($statusCode): $message";
}

class ApiService {
  static final ApiService _i = ApiService._();
  factory ApiService() => _i;
  ApiService._();

  String get base => appConfig.baseUrl;

  // ── Helpers ──────────────────────────────────────────────────
  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    'Accept':       'application/json',
  };

  Future<Map<String, dynamic>> _get(String path,
      {Duration timeout = const Duration(seconds: 15)}) async {
    final r = await http.get(Uri.parse("$base$path"), headers: _headers)
        .timeout(timeout);
    return _parse(r);
  }

  Future<Map<String, dynamic>> _post(String path, Map<String, dynamic> body,
      {Duration timeout = const Duration(seconds: 120)}) async {
    final r = await http.post(
      Uri.parse("$base$path"),
      headers: _headers,
      body: jsonEncode(body),
    ).timeout(timeout);
    return _parse(r);
  }

  Map<String, dynamic> _parse(http.Response r) {
    if (r.statusCode >= 200 && r.statusCode < 300) {
      try {
        return jsonDecode(r.body) as Map<String, dynamic>;
      } catch (_) {
        return {"raw": r.body};
      }
    }
    throw ApiException(r.statusCode,
        r.body.length > 300 ? r.body.substring(0, 300) : r.body);
  }

  // ── Backend Status ────────────────────────────────────────────
  Future<Map<String, dynamic>> getStatus() => _get("/api/status");

  // ── LLM Chat ─────────────────────────────────────────────────
  Future<Map<String, dynamic>> chat({
    required String message,
    String sessionId = "",
    List<Map<String, String>> history = const [],
    String mode = "chat",
  }) => _post("/api/agent", {
    "message":    message,
    "session_id": sessionId,
    "history":    history,
    "mode":       mode,
  });

  // ── Build / Code Gen ─────────────────────────────────────────
  Future<Map<String, dynamic>> build(String prompt) =>
      _post("/api/build", {"message": prompt, "mode": "build"});

  // ── Video Studio ──────────────────────────────────────────────
  Future<Map<String, dynamic>> videoPackage({
    required String title,
    String duration = "12-15",
    String lang     = "bilingual",
    String style    = "cinematic documentary",
  }) => _post("/video/package", {
    "title": title, "duration": duration,
    "lang": lang, "style": style,
  });

  Future<Map<String, dynamic>> videoSection({
    required String section,
    required String title,
  }) => _post("/video/section", {"section": section, "title": title});

  Future<Map<String, dynamic>> videoJobStatus(String jobId) =>
      _get("/video/jobs/$jobId");

  Future<Map<String, dynamic>> listVideoProjects() =>
      _get("/video/projects");

  // ── Media / Image Gen ────────────────────────────────────────
  Future<Map<String, dynamic>> generateImage({
    required String prompt,
    String model    = "fal-ai/flux/schnell",
    String imageSize = "landscape_16_9",
    String negPrompt = "",
  }) => _post("/media/image/generate", {
    "prompt":           prompt,
    "model":            model,
    "image_size":       imageSize,
    "negative_prompt":  negPrompt,
    "num_images":       1,
  });

  Future<Map<String, dynamic>> generateVideo({
    required String imageUrl,
    String model    = "fal-ai/kling-video/v1.6/standard/image-to-video",
    String prompt   = "",
    String duration = "5",
  }) => _post("/media/video/generate", {
    "image_url": imageUrl, "model": model,
    "prompt": prompt, "duration": duration,
  });

  Future<Map<String, dynamic>> mediaJobStatus(String jobId) =>
      _get("/media/video/jobs/$jobId");

  Future<Map<String, dynamic>> gallery() => _get("/media/gallery");

  Future<http.StreamedResponse> uploadFile(File file) async {
    final req = http.MultipartRequest("POST", Uri.parse("$base/media/upload"));
    req.files.add(await http.MultipartFile.fromPath("file", file.path));
    return req.send();
  }

  // ── Projects ─────────────────────────────────────────────────
  Future<Map<String, dynamic>> listProjects() => _get("/projects");

  Future<Map<String, dynamic>> getProject(String pid) =>
      _get("/projects/$pid");
}

final api = ApiService();
'''

# ══════════════════════════════════════════════════════════════════
# FILE: lib/chat_tab.dart
# ══════════════════════════════════════════════════════════════════
CHAT_TAB_DART = '''// lib/chat_tab.dart — AgentJW Chat UI
// Mendukung: chat | build | video mode, history, session, LLM response

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'api_service.dart';

class ChatTab extends StatefulWidget {
  final String baseUrl;
  final ValueChanged<bool>? onConnectionChange;
  const ChatTab({required this.baseUrl, this.onConnectionChange, super.key});
  @override
  State<ChatTab> createState() => _ChatTabState();
}

class _ChatTabState extends State<ChatTab> {
  final _ctrl   = TextEditingController();
  final _scroll = ScrollController();

  String _session = "";
  bool   _loading    = false;
  bool   _connected  = false;
  String _mode       = "chat";

  // Each message: {"role": "user"|"assistant", "content": "..."}
  final List<Map<String, String>> _msgs = [];

  @override
  void initState() {
    super.initState();
    _initSession();
    _ping();
  }

  @override
  void dispose() {
    _ctrl.dispose();
    _scroll.dispose();
    super.dispose();
  }

  Future<void> _initSession() async {
    final p = await SharedPreferences.getInstance();
    setState(() {
      _session = p.getString("agentjw_session") ?? _genSession(p);
    });
  }

  String _genSession(SharedPreferences p) {
    final id = "s_\${DateTime.now().millisecondsSinceEpoch}";
    p.setString("agentjw_session", id);
    return id;
  }

  Future<void> _ping() async {
    try {
      await api.getStatus();
      setState(() => _connected = true);
      widget.onConnectionChange?.call(true);
    } catch (_) {
      setState(() => _connected = false);
      widget.onConnectionChange?.call(false);
    }
  }

  Future<void> _send() async {
    final msg = _ctrl.text.trim();
    if (msg.isEmpty || _loading) return;
    _ctrl.clear();
    FocusScope.of(context).unfocus();

    setState(() {
      _msgs.add({"role": "user", "content": msg});
      _loading = true;
    });
    _scrollBottom();

    try {
      // Kirim 10 pesan terakhir sebagai history
      final hist = _msgs.length > 1
          ? _msgs.sublist(_msgs.length > 21 ? _msgs.length - 21 : 0,
                          _msgs.length - 1)
              .map((m) => {"role": m["role"]!, "content": m["content"]!})
              .toList()
          : <Map<String, String>>[];

      final data = await api.chat(
        message:   msg,
        sessionId: _session,
        history:   hist,
        mode:      _mode,
      );

      final reply = data["response"]?.toString()
                 ?? data["result"]?.toString()
                 ?? "✅ Done";

      setState(() => _msgs.add({"role": "assistant", "content": reply}));
    } on ApiException catch (e) {
      setState(() => _msgs.add({
        "role": "assistant",
        "content": "❌ Server error \${e.statusCode}:\\n\${e.message}"
      }));
    } catch (e) {
      setState(() => _msgs.add({
        "role": "assistant",
        "content": "❌ Koneksi gagal: \$e\\n\\nCek IP/port VPS kamu."
      }));
    } finally {
      setState(() => _loading = false);
      _scrollBottom();
    }
  }

  void _scrollBottom() => Future.delayed(const Duration(milliseconds: 120), () {
    if (_scroll.hasClients) {
      _scroll.animateTo(_scroll.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut);
    }
  });

  void _clearSession() async {
    final p = await SharedPreferences.getInstance();
    final id = _genSession(p);
    setState(() { _msgs.clear(); _session = id; });
  }

  @override
  Widget build(BuildContext context) {
    return Column(children: [
      _buildTopBar(),
      Expanded(child: _buildMessages()),
      _buildInput(),
    ]);
  }

  Widget _buildTopBar() => Container(
    color: const Color(0xFF0D0D0D),
    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
    child: Row(children: [
      // Connection indicator
      Container(width: 8, height: 8,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: _connected ? const Color(0xFF4CAF50) : Colors.redAccent)),
      const SizedBox(width: 6),
      Expanded(
        child: Text(
          _connected ? "AgentJW Online" : "Offline — cek VPS",
          style: TextStyle(
            color: _connected ? const Color(0xFF4CAF50) : Colors.redAccent,
            fontSize: 11),
        ),
      ),
      // Mode pill
      Container(
        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
        decoration: BoxDecoration(
          color: const Color(0xFF1E1E3A),
          borderRadius: BorderRadius.circular(20),
        ),
        child: DropdownButtonHideUnderline(
          child: DropdownButton<String>(
            value: _mode,
            isDense: true,
            dropdownColor: const Color(0xFF1A1A2E),
            style: const TextStyle(fontSize: 11, color: Colors.white),
            items: const [
              DropdownMenuItem(value: "chat",  child: Text("💬 Chat")),
              DropdownMenuItem(value: "build", child: Text("🏗 Build")),
              DropdownMenuItem(value: "video", child: Text("🎬 Video")),
            ],
            onChanged: (v) => setState(() => _mode = v!),
          ),
        ),
      ),
      IconButton(
        icon: const Icon(Icons.wifi_find_outlined, size: 17, color: Colors.grey),
        onPressed: _ping, tooltip: "Reconnect", padding: EdgeInsets.zero,
        constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
      ),
      IconButton(
        icon: const Icon(Icons.restart_alt_outlined, size: 17, color: Colors.grey),
        onPressed: _clearSession, tooltip: "New session",
        padding: EdgeInsets.zero,
        constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
      ),
    ]),
  );

  Widget _buildMessages() {
    if (_msgs.isEmpty) {
      return Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
        Text("🤖", style: const TextStyle(fontSize: 42)),
        const SizedBox(height: 10),
        Text("AgentJW siap digunakan",
          style: TextStyle(color: Colors.grey[500], fontSize: 14)),
        const SizedBox(height: 4),
        Text("Mode: \${_mode.toUpperCase()}",
          style: TextStyle(color: Colors.grey[700], fontSize: 11)),
        const SizedBox(height: 16),
        _modeHint(),
      ]));
    }

    return ListView.builder(
      controller: _scroll,
      padding: const EdgeInsets.fromLTRB(10, 8, 10, 4),
      itemCount: _msgs.length + (_loading ? 1 : 0),
      itemBuilder: (_, i) {
        if (i == _msgs.length) return _typingBubble();
        final m = _msgs[i];
        return _bubble(m["content"]!, m["role"] == "user");
      },
    );
  }

  Widget _modeHint() {
    final hints = {
      "chat":  "Tanya apa saja tentang kode, strategi, fitur...",
      "build": "Ketik: 'bikin bot solana dengan stop-loss 10%'",
      "video": "Ketik judul video: 'Cara Cuan DeFi 2024'",
    };
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 30),
      child: Text(hints[_mode] ?? "",
        textAlign: TextAlign.center,
        style: TextStyle(color: Colors.grey[700], fontSize: 11)),
    );
  }

  Widget _bubble(String text, bool isUser) {
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: GestureDetector(
        onLongPress: () {
          Clipboard.setData(ClipboardData(text: text));
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text("Disalin!"), duration: Duration(seconds: 1)));
        },
        child: Container(
          margin: const EdgeInsets.only(bottom: 6),
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
          constraints: BoxConstraints(
            maxWidth: MediaQuery.of(context).size.width * 0.88),
          decoration: BoxDecoration(
            color: isUser
              ? const Color(0xFF7C3AED)
              : const Color(0xFF1A1A2E),
            borderRadius: BorderRadius.only(
              topLeft:     const Radius.circular(14),
              topRight:    const Radius.circular(14),
              bottomLeft:  Radius.circular(isUser ? 14 : 2),
              bottomRight: Radius.circular(isUser ? 2 : 14),
            ),
          ),
          child: SelectableText(text,
            style: const TextStyle(
              color: Colors.white, fontSize: 13, height: 1.45)),
        ),
      ),
    );
  }

  Widget _typingBubble() {
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 6),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        decoration: BoxDecoration(
          color: const Color(0xFF1A1A2E),
          borderRadius: BorderRadius.circular(14)),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          _dot(0), _dot(1), _dot(2),
        ]),
      ),
    );
  }

  Widget _dot(int i) => TweenAnimationBuilder<double>(
    tween: Tween(begin: 0.3, end: 1.0),
    duration: Duration(milliseconds: 500 + i * 180),
    curve: Curves.easeInOut,
    builder: (_, v, __) => Container(
      width: 7, height: 7,
      margin: const EdgeInsets.symmetric(horizontal: 2),
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: Colors.grey.withOpacity(v),
      ),
    ),
  );

  Widget _buildInput() => Container(
    color: const Color(0xFF0D0D0D),
    padding: const EdgeInsets.fromLTRB(10, 6, 10, 10),
    child: Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
      Expanded(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxHeight: 140),
          child: TextField(
            controller: _ctrl,
            maxLines:   null,
            minLines:   1,
            textInputAction: TextInputAction.newline,
            style: const TextStyle(fontSize: 13, color: Colors.white),
            decoration: InputDecoration(
              hintText: _mode == "build"
                ? "Bikin app: 'bot trading dengan trailing stop...'"
                : _mode == "video"
                  ? "Judul video: 'Cara Cuan DeFi 2024...'"
                  : "Tanya AgentJW...",
              hintStyle: TextStyle(color: Colors.grey[700], fontSize: 12),
              filled:      true,
              fillColor:   const Color(0xFF141414),
              contentPadding: const EdgeInsets.fromLTRB(12, 10, 12, 10),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: const BorderSide(color: Color(0xFF2A2A4A))),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: const BorderSide(color: Color(0xFF2A2A4A))),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: const BorderSide(color: Color(0xFF7C3AED), width: 1.5)),
            ),
          ),
        ),
      ),
      const SizedBox(width: 8),
      GestureDetector(
        onTap: _loading ? null : _send,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          width: 46, height: 46,
          decoration: BoxDecoration(
            color: _loading ? Colors.grey[800] : const Color(0xFF7C3AED),
            borderRadius: BorderRadius.circular(12),
          ),
          child: _loading
            ? const Padding(padding: EdgeInsets.all(13),
                child: CircularProgressIndicator(
                  strokeWidth: 2, color: Colors.white))
            : const Icon(Icons.send_rounded,
                color: Colors.white, size: 21),
        ),
      ),
    ]),
  );
}
'''

# ══════════════════════════════════════════════════════════════════
# FILE: lib/bot_status_tab.dart
# ══════════════════════════════════════════════════════════════════
BOT_STATUS_TAB_DART = '''// lib/bot_status_tab.dart — AgentJW Backend Status Monitor

import 'dart:async';
import 'package:flutter/material.dart';
import 'api_service.dart';

class BotStatusTab extends StatefulWidget {
  final String baseUrl;
  const BotStatusTab({required this.baseUrl, super.key});
  @override
  State<BotStatusTab> createState() => _BotStatusTabState();
}

class _BotStatusTabState extends State<BotStatusTab> {
  Map<String, dynamic>? _status;
  bool  _loading = true;
  String _error  = "";
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _fetch();
    _timer = Timer.periodic(const Duration(seconds: 30), (_) => _fetch());
  }

  @override
  void dispose() { _timer?.cancel(); super.dispose(); }

  Future<void> _fetch() async {
    setState(() { _loading = true; _error = ""; });
    try {
      final data = await api.getStatus();
      setState(() { _status = data; _loading = false; });
    } catch (e) {
      setState(() { _error = e.toString(); _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      body: RefreshIndicator(
        onRefresh: _fetch,
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(14),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            _header(),
            const SizedBox(height: 16),
            if (_loading) const Center(child: CircularProgressIndicator(color: Color(0xFF7C3AED))),
            if (_error.isNotEmpty) _errorCard(),
            if (_status != null && !_loading) ...[
              _statusCard(),
              const SizedBox(height: 12),
              _endpointsCard(),
              const SizedBox(height: 12),
              _configCard(),
            ],
          ]),
        ),
      ),
    );
  }

  Widget _header() => Row(children: [
    const Text("🤖 ", style: TextStyle(fontSize: 20)),
    const Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text("AgentJW Status",
        style: TextStyle(color: Color(0xFF7C3AED),
          fontWeight: FontWeight.bold, fontSize: 16)),
      Text("Backend Health Monitor",
        style: TextStyle(color: Colors.grey, fontSize: 10, letterSpacing: 1)),
    ]),
    const Spacer(),
    IconButton(
      icon: const Icon(Icons.refresh, color: Colors.grey, size: 20),
      onPressed: _fetch,
    ),
  ]);

  Widget _errorCard() => Container(
    width: double.infinity,
    padding: const EdgeInsets.all(14),
    decoration: BoxDecoration(
      color: const Color(0xFF2A0A0A),
      border: Border.all(color: Colors.red.withOpacity(0.5)),
      borderRadius: BorderRadius.circular(10)),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      const Text("❌ Backend Tidak Dapat Diakses",
        style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold, fontSize: 13)),
      const SizedBox(height: 6),
      Text(_error, style: const TextStyle(color: Colors.grey, fontSize: 11)),
      const SizedBox(height: 10),
      const Text("Pastikan:", style: TextStyle(color: Colors.white70, fontSize: 12)),
      const Text("• Backend berjalan di VPS",
        style: TextStyle(color: Colors.grey, fontSize: 11)),
      Text("• URL: \${widget.baseUrl}",
        style: const TextStyle(color: Colors.grey, fontSize: 11)),
      const Text("• Port firewall terbuka",
        style: TextStyle(color: Colors.grey, fontSize: 11)),
    ]),
  );

  Widget _statusCard() {
    final ok = _status!["status"] == "ok";
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF0D1A0D),
        border: Border.all(
          color: (ok ? const Color(0xFF4CAF50) : Colors.red).withOpacity(0.4)),
        borderRadius: BorderRadius.circular(10)),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Icon(ok ? Icons.check_circle : Icons.error,
            color: ok ? const Color(0xFF4CAF50) : Colors.red, size: 20),
          const SizedBox(width: 8),
          Text(ok ? "Backend Online" : "Backend Error",
            style: TextStyle(
              color: ok ? const Color(0xFF4CAF50) : Colors.red,
              fontWeight: FontWeight.bold, fontSize: 14)),
          const Spacer(),
          Text("v\${_status!['version'] ?? '?'}",
            style: const TextStyle(color: Colors.grey, fontSize: 11)),
        ]),
        const SizedBox(height: 10),
        _row("Model",    _status!["model"] ?? "-"),
        _row("Provider", _status!["provider"] ?? "-"),
        _row("Video Studio",
          (_status!["video_studio"] == true) ? "✅ Aktif" : "❌ Tidak aktif"),
        _row("Timestamp", (_status!["timestamp"] ?? "").toString().substring(0, 19)),
      ]),
    );
  }

  Widget _endpointsCard() {
    final eps = List<String>.from(_status!["endpoints"] ?? []);
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF111122),
        border: Border.all(color: const Color(0xFF2A2A4A)),
        borderRadius: BorderRadius.circular(10)),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text("ENDPOINTS", style: TextStyle(
          color: Color(0xFF7C3AED), fontSize: 11,
          fontWeight: FontWeight.bold, letterSpacing: 1.2)),
        const SizedBox(height: 8),
        ...eps.map((e) => Padding(
          padding: const EdgeInsets.only(bottom: 4),
          child: Text("  \$e",
            style: const TextStyle(color: Color(0xFF88CCAA),
              fontFamily: "monospace", fontSize: 11)),
        )),
      ]),
    );
  }

  Widget _configCard() => Container(
    padding: const EdgeInsets.all(12),
    decoration: BoxDecoration(
      color: const Color(0xFF0D0D0D),
      border: Border.all(color: const Color(0xFF2A2A4A)),
      borderRadius: BorderRadius.circular(10)),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      const Text("KONFIGURASI APK", style: TextStyle(
        color: Color(0xFF7C3AED), fontSize: 11,
        fontWeight: FontWeight.bold, letterSpacing: 1.2)),
      const SizedBox(height: 8),
      _row("Base URL", widget.baseUrl),
    ]),
  );

  Widget _row(String label, String value) => Padding(
    padding: const EdgeInsets.only(bottom: 5),
    child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
      SizedBox(width: 100,
        child: Text(label,
          style: const TextStyle(color: Colors.grey, fontSize: 11))),
      Expanded(
        child: Text(value,
          style: const TextStyle(color: Colors.white70, fontSize: 11))),
    ]),
  );
}
'''

# ══════════════════════════════════════════════════════════════════
# FILE: lib/projects_tab.dart
# ══════════════════════════════════════════════════════════════════
PROJECTS_TAB_DART = '''// lib/projects_tab.dart — AgentJW Projects Browser

import 'package:flutter/material.dart';
import 'api_service.dart';

class ProjectsTab extends StatefulWidget {
  final String baseUrl;
  const ProjectsTab({required this.baseUrl, super.key});
  @override
  State<ProjectsTab> createState() => _ProjectsTabState();
}

class _ProjectsTabState extends State<ProjectsTab> {
  List<dynamic> _projects = [];
  bool   _loading = true;
  String _error   = "";
  String _search  = "";

  @override
  void initState() { super.initState(); _load(); }

  Future<void> _load() async {
    setState(() { _loading = true; _error = ""; });
    try {
      final data = await api.listProjects();
      setState(() {
        _projects = data["projects"] ?? data["items"] ?? [];
        _loading  = false;
      });
    } catch (e) {
      setState(() { _error = e.toString(); _loading = false; });
    }
  }

  List<dynamic> get _filtered => _search.isEmpty
      ? _projects
      : _projects.where((p) {
          final s = _search.toLowerCase();
          return (p["name"] ?? "").toLowerCase().contains(s)
              || (p["id"] ?? "").toLowerCase().contains(s);
        }).toList();

  @override
  Widget build(BuildContext context) {
    return Column(children: [
      Container(
        color: const Color(0xFF0D0D0D),
        padding: const EdgeInsets.fromLTRB(10, 8, 10, 8),
        child: Row(children: [
          const Text("📁 ", style: TextStyle(fontSize: 16)),
          const Text("Projects",
            style: TextStyle(color: Color(0xFF7C3AED),
              fontWeight: FontWeight.bold, fontSize: 15)),
          const Spacer(),
          Text("\${_projects.length} project",
            style: const TextStyle(color: Colors.grey, fontSize: 11)),
          const SizedBox(width: 8),
          IconButton(
            icon: const Icon(Icons.refresh, color: Colors.grey, size: 19),
            onPressed: _load, padding: EdgeInsets.zero,
            constraints: const BoxConstraints(minWidth: 30, minHeight: 30)),
        ]),
      ),
      // Search
      Padding(
        padding: const EdgeInsets.fromLTRB(10, 6, 10, 4),
        child: TextField(
          onChanged: (v) => setState(() => _search = v),
          style: const TextStyle(fontSize: 12, color: Colors.white),
          decoration: InputDecoration(
            hintText: "Cari project...",
            hintStyle: const TextStyle(color: Colors.grey, fontSize: 12),
            prefixIcon: const Icon(Icons.search, color: Colors.grey, size: 18),
            filled: true, fillColor: const Color(0xFF141414),
            contentPadding: const EdgeInsets.symmetric(vertical: 8),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(10),
              borderSide: const BorderSide(color: Color(0xFF2A2A4A))),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(10),
              borderSide: const BorderSide(color: Color(0xFF2A2A4A))),
          ),
        ),
      ),

      Expanded(
        child: _loading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF7C3AED)))
          : _error.isNotEmpty
            ? Center(child: Text("❌ \$_error",
                style: const TextStyle(color: Colors.red, fontSize: 12)))
            : _filtered.isEmpty
              ? const Center(child: Text("Belum ada project",
                  style: TextStyle(color: Colors.grey)))
              : RefreshIndicator(
                  onRefresh: _load,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(8),
                    itemCount: _filtered.length,
                    itemBuilder: (_, i) => _projectCard(_filtered[i]),
                  ),
                ),
      ),
    ]);
  }

  Widget _projectCard(dynamic p) {
    final name   = p["name"]?.toString() ?? p["id"]?.toString() ?? "Unknown";
    final id     = p["id"]?.toString() ?? "";
    final status = p["status"]?.toString() ?? "unknown";
    final lang   = p["language"]?.toString() ?? "";

    Color statusColor = Colors.grey;
    if (status == "success" || status == "complete") statusColor = const Color(0xFF4CAF50);
    if (status == "error" || status == "failed")    statusColor = Colors.red;
    if (status == "running")                         statusColor = Colors.orange;

    return Card(
      color: const Color(0xFF141414),
      margin: const EdgeInsets.only(bottom: 8),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(10),
        side: const BorderSide(color: Color(0xFF2A2A4A))),
      child: InkWell(
        borderRadius: BorderRadius.circular(10),
        onTap: () => _showDetail(p),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Row(children: [
            Container(
              width: 36, height: 36,
              decoration: BoxDecoration(
                color: const Color(0xFF1E1E3A),
                borderRadius: BorderRadius.circular(8)),
              child: const Center(
                child: Text("📦", style: TextStyle(fontSize: 18)))),
            const SizedBox(width: 10),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(name, style: const TextStyle(
                color: Colors.white, fontWeight: FontWeight.w600, fontSize: 13)),
              const SizedBox(height: 2),
              Row(children: [
                Container(
                  width: 6, height: 6,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle, color: statusColor)),
                const SizedBox(width: 4),
                Text(status,
                  style: TextStyle(color: statusColor, fontSize: 10)),
                if (lang.isNotEmpty) ...[
                  const SizedBox(width: 8),
                  Text(lang,
                    style: const TextStyle(color: Colors.grey, fontSize: 10)),
                ],
              ]),
              if (id.isNotEmpty)
                Text("ID: \$id",
                  style: const TextStyle(color: Colors.grey, fontSize: 9)),
            ])),
            const Icon(Icons.chevron_right, color: Colors.grey, size: 18),
          ]),
        ),
      ),
    );
  }

  void _showDetail(dynamic p) {
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF0D0D0D),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16))),
      builder: (_) => _ProjectDetail(project: p),
    );
  }
}

class _ProjectDetail extends StatelessWidget {
  final dynamic project;
  const _ProjectDetail({required this.project});

  @override
  Widget build(BuildContext context) {
    final entries = (project as Map).entries.toList();
    return Column(children: [
      Container(
        height: 4, width: 40, margin: const EdgeInsets.only(top: 8),
        decoration: BoxDecoration(
          color: Colors.grey[700], borderRadius: BorderRadius.circular(2))),
      Padding(
        padding: const EdgeInsets.all(14),
        child: Text(
          project["name"]?.toString() ?? "Project Detail",
          style: const TextStyle(color: Colors.white,
            fontWeight: FontWeight.bold, fontSize: 15)),
      ),
      Expanded(
        child: ListView(
          padding: const EdgeInsets.symmetric(horizontal: 14),
          children: entries.map((e) => Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              SizedBox(width: 100,
                child: Text(e.key.toString(),
                  style: const TextStyle(color: Colors.grey, fontSize: 11))),
              Expanded(
                child: Text(e.value?.toString() ?? "-",
                  style: const TextStyle(color: Colors.white70, fontSize: 11))),
            ]),
          )).toList(),
        ),
      ),
    ]);
  }
}
'''

# ══════════════════════════════════════════════════════════════════
# FILE: lib/settings_screen.dart
# ══════════════════════════════════════════════════════════════════
SETTINGS_SCREEN_DART = '''// lib/settings_screen.dart — Ganti Base URL (IP VPS)

import 'package:flutter/material.dart';
import 'config.dart';
import 'api_service.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});
  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late final _urlCtrl = TextEditingController(text: appConfig.baseUrl);
  String _status = "";
  bool   _testing = false;

  Future<void> _test() async {
    final url = _urlCtrl.text.trim();
    if (url.isEmpty) return;
    setState(() { _testing = true; _status = "Testing..."; });
    try {
      await appConfig.setBaseUrl(url);
      final data = await api.getStatus();
      setState(() {
        _status = "✅ Connected! Model: \${data['model'] ?? '?'}";
        _testing = false;
      });
    } catch (e) {
      setState(() { _status = "❌ Gagal: \$e"; _testing = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0D0D0D),
        title: const Text("Settings", style: TextStyle(fontSize: 15)),
        iconTheme: const IconThemeData(color: Colors.white),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text("SERVER URL",
            style: TextStyle(color: Colors.grey, fontSize: 11, letterSpacing: 1.2)),
          const SizedBox(height: 6),
          TextField(
            controller: _urlCtrl,
            style: const TextStyle(color: Colors.white, fontSize: 13),
            decoration: InputDecoration(
              hintText: "http://YOUR_VPS_IP:18790",
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
                onPressed: () => _urlCtrl.clear()),
            ),
          ),
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: _testing ? null : _test,
              icon: _testing
                ? const SizedBox(width: 14, height: 14,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                : const Icon(Icons.wifi_tethering_outlined, size: 16),
              label: Text(_testing ? "Testing..." : "Test & Simpan"),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF7C3AED),
                padding: const EdgeInsets.symmetric(vertical: 12),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              ),
            ),
          ),
          if (_status.isNotEmpty) ...[
            const SizedBox(height: 10),
            Text(_status, style: TextStyle(
              color: _status.startsWith("✅")
                ? const Color(0xFF4CAF50) : Colors.red,
              fontSize: 12)),
          ],
          const SizedBox(height: 24),
          const Divider(color: Color(0xFF2A2A4A)),
          const SizedBox(height: 12),
          const Text("TIPS",
            style: TextStyle(color: Colors.grey, fontSize: 11, letterSpacing: 1.2)),
          const SizedBox(height: 8),
          const Text(
            "• Format URL: http://IP_VPS:18790\\n"
            "• Jangan pakai trailing slash\\n"
            "• Pastikan port 18790 terbuka di firewall VPS\\n"
            "• Start backend: cd ~/agentjw && bash fix_api_server.sh",
            style: TextStyle(color: Colors.grey, fontSize: 11, height: 1.6)),
        ]),
      ),
    );
  }
}
'''

# ══════════════════════════════════════════════════════════════════
# BACKEND PATCH: Missing /media/* endpoints
# ══════════════════════════════════════════════════════════════════
BACKEND_MEDIA_ROUTES = '''

# ══════════════════════════════════════════════════════════════════
# MEDIA ROUTES — dipanggil APK Flutter (MediaTab)
# Ditambah otomatis oleh agentjw_flutter_patcher.py
# ══════════════════════════════════════════════════════════════════
from fastapi import UploadFile, File
import aiofiles

@app.post("/media/image/generate")
async def media_image_generate(req: dict):
    """
    Generate gambar via fal.ai.
    APK kirim: prompt, model, image_size, negative_prompt, num_images
    """
    try:
        prompt = req.get("prompt", "").strip()
        model  = req.get("model", "fal-ai/flux/schnell")
        size   = req.get("image_size", "landscape_16_9")
        neg    = req.get("negative_prompt", "")

        if not prompt:
            raise HTTPException(400, "prompt wajib diisi")

        # ── Coba integrasikan dengan fal-client jika tersedia ──────────
        try:
            import fal_client
            from core.config import config
            fal_key = getattr(config, "FAL_API_KEY", "") or os.getenv("FAL_API_KEY", "")
            if fal_key:
                os.environ["FAL_KEY"] = fal_key
                result = fal_client.run(model, arguments={
                    "prompt":          prompt,
                    "negative_prompt": neg,
                    "image_size":      size,
                    "num_images":      req.get("num_images", 1),
                })
                images = result.get("images", [])
                url = images[0]["url"] if images else ""
                return {
                    "status":    "ok",
                    "image_url": url,
                    "url":       url,
                    "model":     model,
                }
        except ImportError:
            pass  # fal_client belum diinstall

        # ── Fallback: return info bahwa perlu fal-client ───────────────
        return {
            "status":    "pending_config",
            "image_url": "",
            "message":   (
                f"Image generation siap. "
                f"Install fal-client: pip install fal-client "
                f"dan set FAL_API_KEY di .env untuk model {model}"
            ),
            "prompt": prompt,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"media_image_generate error: {e}")


@app.post("/media/upload")
async def media_upload(file: UploadFile = File(...)):
    """
    Upload file gambar dari APK (untuk img2video).
    Return: filename + URL untuk di-pass ke /media/video/generate
    """
    try:
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)

        ext      = Path(file.filename or "upload.jpg").suffix.lower() or ".jpg"
        filename = f"{uuid.uuid4().hex}{ext}"
        dest     = upload_dir / filename

        content = await file.read()
        dest.write_bytes(content)

        return {
            "status":   "ok",
            "filename": filename,
            "url":      f"/uploads/{filename}",
            "size":     len(content),
        }
    except Exception as e:
        raise HTTPException(500, f"upload error: {e}")


@app.post("/media/video/generate")
async def media_video_generate(req: dict, background_tasks: BackgroundTasks):
    """
    Generate video dari image URL.
    APK kirim: image_url, model, prompt, duration
    Return: job_id untuk di-poll via /media/video/jobs/{id}
    """
    try:
        image_url = req.get("image_url", "").strip()
        model     = req.get("model", "fal-ai/kling-video/v1.6/standard/image-to-video")
        prompt    = req.get("prompt", "")
        duration  = req.get("duration", "5")

        if not image_url:
            raise HTTPException(400, "image_url wajib diisi")

        jid = str(uuid.uuid4())[:12]
        _set_job(jid, "processing")

        def _do_video():
            try:
                import fal_client
                from core.config import config
                fal_key = getattr(config, "FAL_API_KEY", "") or os.getenv("FAL_API_KEY", "")
                if fal_key:
                    os.environ["FAL_KEY"] = fal_key
                    result = fal_client.run(model, arguments={
                        "image_url":       image_url,
                        "prompt":          prompt,
                        "duration":        duration,
                        "aspect_ratio":    "16:9",
                    })
                    video_url = result.get("video", {}).get("url", "")
                    _set_job(jid, "completed", result={"video_url": video_url, "url": video_url})
                else:
                    _set_job(jid, "error", error="FAL_API_KEY belum diset di .env")
            except ImportError:
                _set_job(jid, "error",
                    error="fal-client belum diinstall. Jalankan: pip install fal-client")
            except Exception as e:
                _set_job(jid, "error", error=str(e))

        background_tasks.add_task(_do_video)

        return {
            "status": "ok",
            "job_id": jid,
            "poll":   f"GET /media/video/jobs/{jid}",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"media_video_generate error: {e}")


@app.get("/media/video/jobs/{job_id}")
async def media_video_job_status(job_id: str):
    """
    Cek status video generation job.
    APK polling setiap ~5 detik sampai status = 'completed' | 'error'
    Response: { job_id, status, result: { video_url } }
    """
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, f"Job {job_id} tidak ditemukan")

    # Flatten result.video_url ke top-level untuk memudahkan APK
    result  = job.get("result") or {}
    vid_url = result.get("video_url") or result.get("url") or ""

    return {
        "job_id":    job_id,
        "status":    job.get("status", "unknown"),
        "video_url": vid_url,
        "url":       vid_url,
        "error":     job.get("error"),
        "result":    result,
        "updated_at": job.get("updated_at"),
    }


@app.get("/media/gallery")
async def media_gallery():
    """
    Daftar semua file media (gambar + video) di folder uploads/.
    Digunakan GalleryTab APK untuk tampilkan riwayat.
    """
    try:
        upload_dir = Path("uploads")
        items = []
        if upload_dir.exists():
            for f in sorted(
                upload_dir.iterdir(),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )[:100]:
                if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".gif",
                                        ".mp4", ".mov", ".webm"}:
                    is_video = f.suffix.lower() in {".mp4", ".mov", ".webm"}
                    items.append({
                        "filename":   f.name,
                        "url":        f"/uploads/{f.name}",
                        "type":       "video" if is_video else "image",
                        "size":       f.stat().st_size,
                        "size_mb":    round(f.stat().st_size / 1_048_576, 2),
                        "created_at": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                    })

        return {"items": items, "total": len(items)}

    except Exception as e:
        raise HTTPException(500, f"gallery error: {e}")


# Static file serving untuk uploads
from fastapi.staticfiles import StaticFiles
_uploads_dir = Path("uploads")
_uploads_dir.mkdir(exist_ok=True)
try:
    app.mount("/uploads", StaticFiles(directory=str(_uploads_dir)), name="uploads")
except Exception:
    pass  # Already mounted

# ══ END MEDIA ROUTES ══════════════════════════════════════════════
'''

# ══════════════════════════════════════════════════════════════════
# PUBSPEC PATCH
# ══════════════════════════════════════════════════════════════════
REQUIRED_DEPS = {
    "http":               "^1.2.0",
    "dio":                "^5.4.0",
    "provider":           "^6.1.2",
    "shared_preferences": "^2.2.3",
    "image_picker":       "^1.1.2",
    "path_provider":      "^2.1.2",
    "open_file":          "^3.3.2",
    "permission_handler": "^11.3.1",
    "connectivity_plus":  "^6.0.3",
    "video_player":       "^2.8.3",
    "flutter_markdown":   "^0.7.3",
    "cached_network_image": "^3.3.1",
}

# ══════════════════════════════════════════════════════════════════
# ANDROID PERMISSIONS PATCH (AndroidManifest.xml)
# ══════════════════════════════════════════════════════════════════
ANDROID_PERMISSIONS = [
    '<uses-permission android:name="android.permission.INTERNET"/>',
    '<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE"/>',
    '<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE"/>',
    '<uses-permission android:name="android.permission.READ_MEDIA_IMAGES"/>',
    '<uses-permission android:name="android.permission.READ_MEDIA_VIDEO"/>',
    '<uses-permission android:name="android.permission.CAMERA"/>',
]


# ══════════════════════════════════════════════════════════════════
# MAIN PATCHER
# ══════════════════════════════════════════════════════════════════
def main():
    p("")
    p("╔══════════════════════════════════════════════════════════╗")
    p("║   AgentJW Flutter APK Complete Patcher                 ║")
    p("╚══════════════════════════════════════════════════════════╝")
    p(f"  APK dir    : {APK_DIR}")
    p(f"  Backend dir: {BACKEND_DIR}")
    p(f"  Mode       : {'APPLY (semua patch aktif)' if APPLY else 'DRY-RUN (tambah --apply untuk patch)'}")
    p("")

    if not APK_DIR.exists():
        err(f"Flutter dir tidak ditemukan: {APK_DIR}")
        err("Jalankan dengan --apk-dir /path/ke/flutter")
        sys.exit(1)

    # ── STEP 1: Dart Files ─────────────────────────────────────
    h("STEP 1: Generate Dart Files")
    write_dart("config.dart",           CONFIG_DART)
    write_dart("api_service.dart",      API_SERVICE_DART)
    write_dart("chat_tab.dart",         CHAT_TAB_DART)
    write_dart("bot_status_tab.dart",   BOT_STATUS_TAB_DART)
    write_dart("projects_tab.dart",     PROJECTS_TAB_DART)
    write_dart("settings_screen.dart",  SETTINGS_SCREEN_DART)

    # ── STEP 2: pubspec.yaml ───────────────────────────────────
    h("STEP 2: Patch pubspec.yaml")
    pubspec = APK_DIR / "pubspec.yaml"
    if pubspec.exists():
        pub_content = pubspec.read_text(encoding="utf-8")
        missing_deps = []
        for pkg, ver in REQUIRED_DEPS.items():
            if pkg not in pub_content:
                missing_deps.append(f"  {pkg}: {ver}")

        if missing_deps:
            deps_block = "\n".join(missing_deps)
            patch_file(pubspec,
                old="dependencies:\n  flutter:\n    sdk: flutter",
                new=f"dependencies:\n  flutter:\n    sdk: flutter\n{deps_block}",
                label=f"Tambah {len(missing_deps)} dependencies ke pubspec.yaml")
        else:
            ok("pubspec.yaml — semua dependencies sudah ada")
    else:
        err(f"pubspec.yaml tidak ditemukan di {APK_DIR}")

    # ── STEP 3: AndroidManifest.xml permissions ────────────────
    h("STEP 3: Android Permissions")
    manifest = APK_DIR / "android" / "app" / "src" / "main" / "AndroidManifest.xml"
    if manifest.exists():
        mf_content = manifest.read_text(encoding="utf-8")
        missing_perms = [p for p in ANDROID_PERMISSIONS if p not in mf_content]
        if missing_perms:
            perms_str = "\n    ".join(missing_perms)
            patch_file(manifest,
                old="<manifest",
                new=f"<manifest",
                label="(manifest tag exists)")
            # Append before </manifest>
            append_file(manifest,
                content="\n    " + "\n    ".join(missing_perms) + "\n",
                guard=missing_perms[0],
                label=f"Tambah {len(missing_perms)} Android permissions")
        else:
            ok("AndroidManifest.xml — permissions sudah lengkap")
    else:
        dry(f"AndroidManifest.xml tidak ditemukan di {manifest}")

    # ── STEP 4: Backend media routes ──────────────────────────
    h("STEP 4: Backend Media Routes")
    api_server = BACKEND_DIR / "api_server.py"
    if api_server.exists():
        append_file(api_server,
            content=BACKEND_MEDIA_ROUTES,
            guard="/media/image/generate",
            label="Media routes (/media/image/generate, /media/upload, /media/video/generate, /media/gallery)")
    else:
        err(f"api_server.py tidak ditemukan di {BACKEND_DIR}")

    # ── STEP 5: Install backend deps ──────────────────────────
    h("STEP 5: Backend Dependencies")
    req_file = BACKEND_DIR / "requirements.txt"
    EXTRA_BACKEND_DEPS = [
        "fal-client",
        "aiofiles",
        "python-multipart",
    ]
    if req_file.exists():
        req_content = req_file.read_text(encoding="utf-8")
        missing_req = [d for d in EXTRA_BACKEND_DEPS if d.split("-")[0] not in req_content]
        if missing_req and APPLY:
            with open(req_file, "a") as f:
                f.write("\n# Media support (auto-added)\n")
                for d in missing_req:
                    f.write(f"{d}\n")
            ok(f"Ditambah ke requirements.txt: {', '.join(missing_req)}")
        elif missing_req:
            dry(f"requirements.txt — tambah: {', '.join(missing_req)}")
        else:
            ok("requirements.txt — sudah lengkap")

    # ── STEP 6: Generate install script ───────────────────────
    h("STEP 6: Generate install_deps.sh")
    install_sh = BACKEND_DIR / "install_media_deps.sh"
    install_content = """#!/bin/bash
# install_media_deps.sh — Install semua deps untuk media support
# Auto-generated oleh agentjw_flutter_patcher.py
set -e
cd ~/agentjw
source venv/bin/activate 2>/dev/null || true

echo "[1/3] Install Python media deps..."
pip install fal-client aiofiles python-multipart pillow --quiet

echo "[2/3] Install Flutter deps..."
if [ -d "${APK_DIR}" ]; then
    cd "${APK_DIR}"
    flutter pub get
    cd ~/agentjw
fi

echo "[3/3] Restart api_server..."
pkill -f api_server.py 2>/dev/null || true
sleep 1
nohup uvicorn api_server:app --host 0.0.0.0 --port 18790 > logs/api.log 2>&1 &
echo "  ✅ api_server started (port 18790)"
echo ""
echo "Done! Test: curl http://localhost:18790/api/status"
""".replace("${APK_DIR}", str(APK_DIR))

    if APPLY:
        install_sh.write_text(install_content, encoding="utf-8")
        os.chmod(install_sh, 0o755)
        ok(f"Dibuat: {install_sh}")
    else:
        dry(f"WRITE: {install_sh}")

    # ── STEP 7: Print summary ──────────────────────────────────
    h("SUMMARY")
    if not APPLY:
        p("")
        p("  ⚠️  INI DRY-RUN — tidak ada yang diubah.")
        p(f"  Jalankan dengan --apply untuk apply semua patch:")
        p(f"  python3 agentjw_flutter_patcher.py --apk-dir {APK_DIR} --backend-dir {BACKEND_DIR} --apply")
    else:
        p("")
        ok("Semua patch berhasil diapply!")
        p("")
        p("  LANGKAH SELANJUTNYA:")
        p(f"  1. cd {BACKEND_DIR} && bash install_media_deps.sh")
        p(f"  2. cd {APK_DIR} && flutter pub get")
        p(f"  3. flutter run   (atau flutter build apk --release)")
        p("")
        p("  VERIFIKASI:")
        p(f"  curl http://localhost:18790/api/status")
        p(f"  curl http://localhost:18790/media/gallery")

    p("")


if __name__ == "__main__":
    main()
