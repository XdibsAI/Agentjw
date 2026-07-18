# SiCuan Self-Audit Report

Dibuat: 2026-07-15T07:08:36.529768+00:00
Model analisis: openai/gpt-4o-mini
Scope: sicuan, agents, core, mcp

## Ringkasan

- File dipindai: 412
- Fungsi/method diindeks: 2031
- Grup duplikat identik: 108
- Grup duplikat struktural: 58
- Class divergen: 9
- Broken imports: 3
- Orphan files: 108
- Endpoint collisions: 1

## exact_duplicates

_Temuan ini menunjukkan adanya beberapa duplikasi fungsi dengan tingkat kompleksitas yang bervariasi. Beberapa fungsi memiliki logika penting yang sebaiknya digabungkan untuk meningkatkan pemeliharaan, sementara yang lain adalah pola umum yang tidak menimbulkan masalah besar. Tindakan yang direkomendasikan berfokus pada penggabungan fungsi yang kompleks dan mempertahankan fungsi yang lebih sederhana._

- 🟠 **ProjectAdapter.find_project** (high): Fungsi ini memiliki logika yang kompleks dan panjang, sehingga duplikasinya dapat menyebabkan kesulitan dalam pemeliharaan dan potensi bug. Keduanya berada di file yang berbeda, tetapi tampaknya digunakan dalam konteks yang sama.
  - ➡️ gabungkan menjadi satu implementasi di salah satu file
- 🟠 **SiCuanBrain._safe_get** (high): Fungsi ini memiliki logika yang signifikan dan kompleks, sehingga duplikasinya dapat menyebabkan kesulitan dalam pemeliharaan. Keduanya berada di file yang berbeda.
  - ➡️ gabungkan menjadi satu implementasi di salah satu file
- 🟠 **SiCuanBrain.get_data_availability** (high): Fungsi ini memiliki logika yang penting dan kompleks, sehingga duplikasinya dapat menyebabkan kesulitan dalam pemeliharaan. Keduanya berada di file yang berbeda.
  - ➡️ gabungkan menjadi satu implementasi di salah satu file
- 🟠 **SiCuanBrain._find_project** (high): Fungsi ini memiliki logika yang kompleks dan panjang, sehingga duplikasinya dapat menyebabkan kesulitan dalam pemeliharaan. Keduanya berada di file yang berbeda.
  - ➡️ gabungkan menjadi satu implementasi di salah satu file
- 🟠 **SiCuanBrain._get_projects** (high): Fungsi ini memiliki logika yang penting dan kompleks, sehingga duplikasinya dapat menyebabkan kesulitan dalam pemeliharaan. Keduanya berada di file yang berbeda.
  - ➡️ gabungkan menjadi satu implementasi di salah satu file
- 🟢 **ProjectAdapter.get_project_by_name** (low): Fungsi ini cukup pendek dan sederhana, sehingga duplikasinya tidak terlalu berisiko. Ini adalah pola umum yang sering ditemukan dalam kode.
  - ➡️ biarkan, ini wajar
- 🟢 **get_project_adapter** (low): Fungsi ini juga pendek dan berfungsi sebagai getter, sehingga duplikasinya tidak menjadi masalah besar. Ini adalah pola umum dalam pengembangan.
  - ➡️ biarkan, ini wajar
- 🟢 **SiCuanBrain.__init__** (low): Duplikasi ini terjadi pada konstruktor yang pendek, yang merupakan pola umum dalam OOP. Ini tidak menimbulkan masalah besar.
  - ➡️ biarkan, ini wajar
- 🟢 **SiCuanBrain.llm** (low): Fungsi ini adalah metode pendek yang sering ditemukan dalam berbagai kelas, sehingga duplikasinya tidak menjadi masalah besar.
  - ➡️ biarkan, ini wajar
- 🟢 **SiCuanBrain.fs** (low): Duplikasi ini terjadi pada metode pendek yang merupakan pola umum dalam OOP. Ini tidak menimbulkan masalah besar.
  - ➡️ biarkan, ini wajar

## structural_duplicates

_Temuan ini menunjukkan adanya beberapa duplikasi struktur dalam kode. Sebagian besar duplikasi adalah pada fungsi sederhana dan konstruktor, yang merupakan pola umum dalam pemrograman. Beberapa fungsi dengan logika lebih kompleks perlu ditinjau lebih lanjut untuk memastikan tidak ada redundansi yang tidak perlu._

- 🟡 **SiCuanBrain.diagnose_error** (medium): Fungsi ini memiliki logika yang lebih kompleks dan penting. Duplikasi ini perlu diperiksa lebih lanjut untuk memastikan tidak ada redundansi yang tidak perlu.
  - ➡️ cek manual: apakah dipanggil di tempat lain
- 🟡 **SiCuanChat._handle_summary_query** (medium): Fungsi ini memiliki logika yang lebih kompleks. Duplikasi ini perlu diperiksa lebih lanjut untuk memastikan tidak ada redundansi yang tidak perlu.
  - ➡️ cek manual: apakah dipanggil di tempat lain
- 🟡 **SiCuanChat._handle_resume_query** (medium): Fungsi ini juga memiliki logika yang lebih kompleks. Duplikasi ini perlu diperiksa lebih lanjut untuk memastikan tidak ada redundansi yang tidak perlu.
  - ➡️ cek manual: apakah dipanggil di tempat lain
- 🟢 **SiCuanBrain.get_task_status** (low): Fungsi ini memiliki logika yang sederhana dan merupakan getter, sehingga duplikasi dianggap wajar. Keduanya berada dalam konteks yang sama dan tidak menunjukkan indikasi bahwa salah satu tidak digunakan.
  - ➡️ biarkan, ini wajar
- 🟢 **SiCuanBrain.vault_daily_review** (low): Mirip dengan fungsi sebelumnya, ini juga merupakan getter sederhana. Duplikasi ini tidak menunjukkan masalah yang signifikan.
  - ➡️ biarkan, ini wajar
- 🟢 **SiCuanBrain.vault_weekly_review** (low): Fungsi ini juga merupakan getter sederhana. Duplikasi ini tidak menunjukkan indikasi bahwa salah satu tidak digunakan.
  - ➡️ biarkan, ini wajar
- 🟢 **SiCuanBrain.vault_search** (low): Fungsi ini memiliki logika yang sederhana dan merupakan bagian dari pola yang sama. Duplikasi ini tidak menunjukkan masalah yang signifikan.
  - ➡️ biarkan, ini wajar
- 🟢 **_fix_score_threshold** (low): Fungsi ini memiliki logika yang sederhana dan merupakan bagian dari pola yang sama. Duplikasi ini tidak menunjukkan masalah yang signifikan.
  - ➡️ biarkan, ini wajar
- 🟢 **_fix_buy_logic** (low): Fungsi ini juga memiliki logika yang sederhana. Duplikasi ini tidak menunjukkan indikasi bahwa salah satu tidak digunakan.
  - ➡️ biarkan, ini wajar
- 🟢 **SiCuanChat.get_context** (low): Fungsi ini merupakan getter sederhana. Duplikasi ini tidak menunjukkan masalah yang signifikan.
  - ➡️ biarkan, ini wajar
- 🟢 **ActionRegistry.list_actions** (low): Fungsi ini memiliki logika yang sederhana. Duplikasi ini tidak menunjukkan masalah yang signifikan.
  - ➡️ biarkan, ini wajar
- 🟢 **CapabilityManager.list_all** (low): Fungsi ini juga memiliki logika yang sederhana. Duplikasi ini tidak menunjukkan indikasi bahwa salah satu tidak digunakan.
  - ➡️ biarkan, ini wajar
- 🟢 **Alerting.__init__** (low): Duplikasi ini terjadi pada metode konstruktor yang umum. Ini adalah pola yang wajar dalam OOP.
  - ➡️ biarkan, ini wajar
- 🟢 **Workspace.__init__** (low): Mirip dengan fungsi sebelumnya, ini juga merupakan konstruktor yang umum. Duplikasi ini tidak menunjukkan masalah yang signifikan.
  - ➡️ biarkan, ini wajar
- 🟢 **Billing.__init__** (low): Fungsi ini juga merupakan konstruktor yang umum. Duplikasi ini tidak menunjukkan indikasi bahwa salah satu tidak digunakan.
  - ➡️ biarkan, ini wajar
- 🟢 **PluginManager.__init__** (low): Duplikasi ini terjadi pada metode konstruktor yang umum. Ini adalah pola yang wajar dalam OOP.
  - ➡️ biarkan, ini wajar
- 🟢 **APIGateway.__init__** (low): Mirip dengan fungsi sebelumnya, ini juga merupakan konstruktor yang umum. Duplikasi ini tidak menunjukkan masalah yang signifikan.
  - ➡️ biarkan, ini wajar
- 🟢 **SecretVault.__init__** (low): Fungsi ini juga merupakan konstruktor yang umum. Duplikasi ini tidak menunjukkan indikasi bahwa salah satu tidak digunakan.
  - ➡️ biarkan, ini wajar
- 🟢 **WebhookEngine.__init__** (low): Duplikasi ini terjadi pada metode konstruktor yang umum. Ini adalah pola yang wajar dalam OOP.
  - ➡️ biarkan, ini wajar
- 🟢 **WorkspaceResolver.__init__** (low): Fungsi ini juga merupakan konstruktor yang umum. Duplikasi ini tidak menunjukkan indikasi bahwa salah satu tidak digunakan.
  - ➡️ biarkan, ini wajar

## class_diverged

_Terdapat beberapa kelas yang terduplikasi dengan metode yang berbeda di berbagai file, menunjukkan adanya pengembangan paralel atau fitur yang belum sepenuhnya diintegrasikan. Sebagian besar temuan tidak menunjukkan dead code, tetapi perlu diteliti lebih lanjut untuk memastikan integrasi yang tepat._

- 🟡 **ProjectAdapter** (medium): Ada dua implementasi dari ProjectAdapter di file yang berbeda, namun keduanya memiliki metode yang berbeda. Ini menunjukkan bahwa mungkin ada pengembangan paralel atau fitur yang belum sepenuhnya diintegrasikan.
  - ➡️ cek manual: apakah dipanggil via importlib
- 🟡 **ProjectManager** (medium): Terdapat dua kelas ProjectManager dengan metode yang sangat berbeda. Hal ini bisa menunjukkan bahwa ada dua pendekatan yang sedang dieksplorasi, sehingga perlu diteliti lebih lanjut.
  - ➡️ cek manual: apakah dipanggil via importlib
- 🟡 **ContextManager** (medium): Dua implementasi ContextManager ditemukan dengan metode yang berbeda. Ini bisa jadi indikasi adanya pengembangan yang belum selesai atau fitur yang direncanakan.
  - ➡️ cek manual: apakah dipanggil via importlib
- 🟡 **RepairAgent** (medium): Dua implementasi RepairAgent ditemukan dengan metode yang berbeda. Hal ini menunjukkan adanya pengembangan paralel yang perlu diteliti lebih lanjut.
  - ➡️ cek manual: apakah dipanggil via importlib
- 🟡 **CoderAgent** (medium): Terdapat dua kelas CoderAgent dengan metode yang berbeda. Ini bisa jadi indikasi adanya pengembangan yang belum selesai atau fitur yang direncanakan.
  - ➡️ cek manual: apakah dipanggil via importlib
- 🟡 **ReviewerAgent** (medium): Dua implementasi ReviewerAgent ditemukan dengan metode yang berbeda. Hal ini menunjukkan adanya pengembangan paralel yang perlu diteliti lebih lanjut.
  - ➡️ cek manual: apakah dipanggil via importlib
- 🟢 **Strategy** (low): Banyak variasi dari kelas Strategy ditemukan di file yang berbeda, namun sebagian besar hanya memiliki metode 'run' yang sederhana. Ini menunjukkan bahwa ini adalah pola pengujian dan bukan bug serius.
  - ➡️ biarkan, ini wajar
- 🟢 **Base** (low): Kelas Base muncul di beberapa file dengan metode yang mirip. Ini adalah pola umum dalam pengujian dan tidak menunjukkan masalah serius.
  - ➡️ biarkan, ini wajar
- 🟢 **Point** (low): Kelas Point muncul di beberapa file dengan metode yang berbeda. Ini menunjukkan bahwa ini adalah variasi dalam pengujian dan bukan indikasi bug.
  - ➡️ biarkan, ini wajar

## broken_imports

_Temuan broken imports ini menunjukkan ketergantungan pada modul yang mungkin belum diimplementasikan. Meskipun tidak bisa dianggap dead code, perlu dilakukan pengecekan lebih lanjut untuk memastikan apakah modul tersebut memang direncanakan untuk dikembangkan atau tidak._

- 🟠 **get_godmeme_status (sicuan/brain.py)** (high): Modul 'projects.godmeme_bot.status_sync_provider' mungkin belum ditulis atau diimplementasikan, sehingga import ini menjadi broken. Namun, mengingat adanya beberapa referensi ke modul yang sama di file lain, ada kemungkinan ini adalah fitur yang direncanakan.
  - ➡️ cek manual: apakah dipanggil via importlib atau ada rencana implementasi untuk modul ini
- 🟠 **get_godmeme_status (sicuan/core/semantic_query.py)** (high): Sama seperti temuan sebelumnya, import ini menunjukkan ketergantungan pada modul yang mungkin belum ada. Namun, karena ada referensi lain, ini bisa jadi fitur yang sedang dalam pengembangan.
  - ➡️ cek manual: apakah dipanggil via importlib atau ada rencana implementasi untuk modul ini
- 🟠 **get_godmeme_status (sicuan/actions/godmeme_status.py)** (high): Import ini juga menunjukkan ketergantungan pada modul yang mungkin belum ada. Dengan adanya beberapa referensi di file lain, ini menunjukkan bahwa ada potensi pengembangan fitur yang belum selesai.
  - ➡️ cek manual: apakah dipanggil via importlib atau ada rencana implementasi untuk modul ini

## orphan_files

_Banyak file dalam kategori ini tidak terhubung dengan bagian lain dari project, menunjukkan kemungkinan bahwa mereka adalah kode mati. Namun, beberapa file memiliki konteks pemuatan dinamis yang menunjukkan bahwa mereka mungkin direncanakan untuk digunakan di masa depan. Disarankan untuk memverifikasi setiap file secara manual sebelum penghapusan._

- 🟡 **sicuan/platform/plugin.py** (medium): File ini memiliki dynamic loading context, menunjukkan bahwa mungkin ada penggunaan yang direncanakan. Perlu verifikasi lebih lanjut.
  - ➡️ cek manual: apakah dipanggil via importlib
- 🟢 **core/image_service.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, namun tidak ada indikasi bahwa ini adalah fitur yang direncanakan. Sebaiknya diperiksa lebih lanjut.
  - ➡️ hapus file core/image_service.py
- 🟢 **sicuan/cleanup.py** (low): File ini tidak terhubung dengan bagian lain dari project, kemungkinan tidak digunakan. Perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/cleanup.py
- 🟢 **sicuan/platform/event_bus.py** (low): Tidak ada referensi ke file ini dalam codebase, tetapi perlu diperiksa apakah ada rencana penggunaan di masa depan.
  - ➡️ hapus file sicuan/platform/event_bus.py
- 🟢 **sicuan/platform/alerting.py** (low): File ini tidak terhubung dengan bagian lain dari project, namun bisa jadi bagian dari fitur yang belum selesai.
  - ➡️ hapus file sicuan/platform/alerting.py
- 🟢 **sicuan/platform/workspace_context.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/platform/workspace_context.py
- 🟢 **sicuan/platform/backup.py** (low): File ini tidak terhubung dengan bagian lain dari project, kemungkinan tidak digunakan. Perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/platform/backup.py
- 🟢 **sicuan/core/artifact.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/artifact.py
- 🟢 **sicuan/core/input_validator.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, namun tidak ada indikasi bahwa ini adalah fitur yang direncanakan.
  - ➡️ hapus file sicuan/core/input_validator.py
- 🟢 **sicuan/core/data_awareness_injector.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/data_awareness_injector.py
- 🟢 **sicuan/core/target_router.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/target_router.py
- 🟢 **sicuan/core/entry_tester.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/entry_tester.py
- 🟢 **sicuan/core/executive_brain_complete.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/executive_brain_complete.py
- 🟢 **sicuan/core/capability_engine.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/capability_engine.py
- 🟢 **sicuan/core/dynamic_blacklist.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/dynamic_blacklist.py
- 🟢 **sicuan/core/capability_manager.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/capability_manager.py
- 🟢 **sicuan/core/context_router.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/context_router.py
- 🟢 **sicuan/core/memory_service.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/memory_service.py
- 🟢 **sicuan/core/conversation_dispatcher.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/conversation_dispatcher.py
- 🟢 **sicuan/core/task_generator.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/task_generator.py
- 🟢 **sicuan/core/attribution_dashboard.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/attribution_dashboard.py
- 🟢 **sicuan/core/token_scorer.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/token_scorer.py
- 🟢 **sicuan/core/evaluator_engine.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/evaluator_engine.py
- 🟢 **sicuan/core/conversation_reasoner.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/conversation_reasoner.py
- 🟢 **sicuan/core/data_aware_planner.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/data_aware_planner.py
- 🟢 **sicuan/core/conversation_slot.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/conversation_slot.py
- 🟢 **sicuan/core/task_queue.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/task_queue.py
- 🟢 **sicuan/core/intent_engine.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/intent_engine.py
- 🟢 **sicuan/core/unified_query.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/unified_query.py
- 🟢 **sicuan/core/script_generator.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/script_generator.py
- 🟢 **sicuan/core/function_patch.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/function_patch.py
- 🟢 **sicuan/core/result_normalizer.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/result_normalizer.py
- 🟢 **sicuan/core/adaptive_entry_time.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/adaptive_entry_time.py
- 🟢 **sicuan/core/runtime_fixer.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/runtime_fixer.py
- 🟢 **sicuan/core/event_replay.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/event_replay.py
- 🟢 **sicuan/core/llm_task_executor.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/llm_task_executor.py
- 🟢 **sicuan/core/data_awareness.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/data_awareness.py
- 🟢 **sicuan/core/response_gate.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/response_gate.py
- 🟢 **sicuan/core/dispatcher.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/dispatcher.py
- 🟢 **sicuan/core/function_ranker.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/function_ranker.py
- 🟢 **sicuan/core/drift_monitor.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/drift_monitor.py
- 🟢 **sicuan/core/knowledge_state.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/knowledge_state.py
- 🟢 **sicuan/core/project_brain.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/project_brain.py
- 🟢 **sicuan/core/intelligence/endpoint_registry.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/intelligence/endpoint_registry.py
- 🟢 **sicuan/core/intelligence/capability_graph.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/intelligence/capability_graph.py
- 🟢 **sicuan/core/intelligence/project_operator.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/intelligence/project_operator.py
- 🟢 **sicuan/core/intelligence/runtime_intelligence.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/core/intelligence/runtime_intelligence.py
- 🟢 **sicuan/actions/auto_fix_from_recommendations.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/actions/auto_fix_from_recommendations.py
- 🟢 **sicuan/actions/evaluate_strategy.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/actions/evaluate_strategy.py
- 🟢 **sicuan/tests/generate_stress_tests.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/generate_stress_tests.py
- 🟢 **sicuan/tests/temp_stress/18_runtime_exception.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/temp_stress/18_runtime_exception.py
- 🟢 **sicuan/tests/temp_stress/16_large_file.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/temp_stress/16_large_file.py
- 🟢 **sicuan/tests/temp_stress/05_abstract_class.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/temp_stress/05_abstract_class.py
- 🟢 **sicuan/tests/temp_stress/09_import_alias.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/temp_stress/09_import_alias.py
- 🟢 **sicuan/tests/temp_stress/10_circular_import.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/temp_stress/10_circular_import.py
- 🟢 **sicuan/tests/temp_stress/02_decorator.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/temp_stress/02_decorator.py
- 🟢 **sicuan/tests/temp_stress/11_single_syntax_error.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/temp_stress/11_single_syntax_error.py
- 🟢 **sicuan/tests/temp_stress/14_generic_typing.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/temp_stress/14_generic_typing.py
- 🟢 **sicuan/tests/temp_stress/17_multi_file.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/temp_stress/17_multi_file.py
- 🟢 **sicuan/tests/temp_stress/04_inheritance.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/temp_stress/04_inheritance.py
- 🟢 **sicuan/tests/temp_stress/06_dataclass.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/temp_stress/06_dataclass.py
- 🟢 **sicuan/tests/temp_stress/11_multiple_syntax_error.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/temp_stress/11_multiple_syntax_error.py
- 🟢 **sicuan/tests/temp_stress/08_property.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/temp_stress/08_property.py
- 🟢 **sicuan/tests/temp_stress/01_nested_class.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/temp_stress/01_nested_class.py
- 🟢 **sicuan/tests/temp_stress/15_overload.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/temp_stress/15_overload.py
- 🟢 **sicuan/tests/temp_stress/12_broken_docstring.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/temp_stress/12_broken_docstring.py
- 🟢 **sicuan/tests/temp_stress/07_enum.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/temp_stress/07_enum.py
- 🟢 **sicuan/tests/temp_stress/13_mixed_tabs_spaces.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/temp_stress/13_mixed_tabs_spaces.py
- 🟢 **sicuan/tests/temp_stress/03_async_function.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/temp_stress/03_async_function.py
- 🟢 **sicuan/tests/temp_stress/19_multiple_independent_syntax_errors.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/temp_stress/19_multiple_independent_syntax_errors.py
- 🟢 **sicuan/tests/temp/missing_import.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/temp/missing_import.py
- 🟢 **sicuan/tests/temp/broken_class.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/temp/broken_class.py
- 🟢 **sicuan/tests/temp/dataclass_simple.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/temp/dataclass_simple.py
- 🟢 **sicuan/tests/temp/missing_method.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/temp/missing_method.py
- 🟢 **sicuan/tests/temp/dataclass_fixed.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/temp/dataclass_fixed.py
- 🟢 **sicuan/tests/temp/import_missing.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/temp/import_missing.py
- 🟢 **sicuan/tests/temp/duplicate_method.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/temp/duplicate_method.py
- 🟢 **sicuan/tests/temp/async_missing_colon.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/temp/async_missing_colon.py
- 🟢 **sicuan/tests/temp/healthy.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/temp/healthy.py
- 🟢 **sicuan/tests/temp/syntax_error.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/temp/syntax_error.py
- 🟢 **sicuan/tests/temp/class_missing_colon.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/temp/class_missing_colon.py
- 🟢 **sicuan/tests/fixtures_stress/18_runtime_exception.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/fixtures_stress/18_runtime_exception.py
- 🟢 **sicuan/tests/fixtures_stress/16_large_file.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/fixtures_stress/16_large_file.py
- 🟢 **sicuan/tests/fixtures_stress/05_abstract_class.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/fixtures_stress/05_abstract_class.py
- 🟢 **sicuan/tests/fixtures_stress/09_import_alias.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/fixtures_stress/09_import_alias.py
- 🟢 **sicuan/tests/fixtures_stress/10_circular_import.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/fixtures_stress/10_circular_import.py
- 🟢 **sicuan/tests/fixtures_stress/02_decorator.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/fixtures_stress/02_decorator.py
- 🟢 **sicuan/tests/fixtures_stress/11_single_syntax_error.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/fixtures_stress/11_single_syntax_error.py
- 🟢 **sicuan/tests/fixtures_stress/14_generic_typing.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/fixtures_stress/14_generic_typing.py
- 🟢 **sicuan/tests/fixtures_stress/17_multi_file.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/fixtures_stress/17_multi_file.py
- 🟢 **sicuan/tests/fixtures_stress/04_inheritance.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/fixtures_stress/04_inheritance.py
- 🟢 **sicuan/tests/fixtures_stress/06_dataclass.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/fixtures_stress/06_dataclass.py
- 🟢 **sicuan/tests/fixtures_stress/11_multiple_syntax_error.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/fixtures_stress/11_multiple_syntax_error.py
- 🟢 **sicuan/tests/fixtures_stress/08_property.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/fixtures_stress/08_property.py
- 🟢 **sicuan/tests/fixtures_stress/01_nested_class.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/fixtures_stress/01_nested_class.py
- 🟢 **sicuan/tests/fixtures_stress/15_overload.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/fixtures_stress/15_overload.py
- 🟢 **sicuan/tests/fixtures_stress/12_broken_docstring.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/fixtures_stress/12_broken_docstring.py
- 🟢 **sicuan/tests/fixtures_stress/07_enum.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/fixtures_stress/07_enum.py
- 🟢 **sicuan/tests/fixtures_stress/13_mixed_tabs_spaces.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/fixtures_stress/13_mixed_tabs_spaces.py
- 🟢 **sicuan/tests/fixtures_stress/03_async_function.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/fixtures_stress/03_async_function.py
- 🟢 **sicuan/tests/fixtures_stress/19_multiple_independent_syntax_errors.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/fixtures_stress/19_multiple_independent_syntax_errors.py
- 🟢 **sicuan/tests/fixtures/missing_import.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/fixtures/missing_import.py
- 🟢 **sicuan/tests/fixtures/broken_class.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/fixtures/broken_class.py
- 🟢 **sicuan/tests/fixtures/missing_method.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/fixtures/missing_method.py
- 🟢 **sicuan/tests/fixtures/dataclass_fixed.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/fixtures/dataclass_fixed.py
- 🟢 **sicuan/tests/fixtures/duplicate_method.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/fixtures/duplicate_method.py
- 🟢 **sicuan/tests/fixtures/healthy.py** (low): File ini tidak terdeteksi digunakan di bagian lain dari codebase, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/fixtures/healthy.py
- 🟢 **sicuan/tests/fixtures/syntax_error.py** (low): File ini tidak terhubung dengan bagian lain dari project, perlu verifikasi lebih lanjut.
  - ➡️ hapus file sicuan/tests/fixtures/syntax_error.py

## endpoint_collisions

_Terdapat dua endpoint yang bertabrakan dengan nama fungsi yang sama di dua file berbeda. Ini dapat menyebabkan masalah dalam routing dan harus segera ditangani untuk memastikan API berfungsi dengan baik dan tidak membingungkan pengguna._

- 🟠 **api_server.py/root** (high): Endpoint '/' di api_server.py dan gusmcp_server.py memiliki nama fungsi yang sama, yang dapat menyebabkan kebingungan dalam routing. Meskipun keduanya ada, potensi konflik ini harus diatasi untuk menjaga kejelasan dan konsistensi dalam API.
  - ➡️ ubah nama fungsi di salah satu file untuk menghindari konflik
- 🟠 **gusmcp_server.py/root** (high): Endpoint '/' di gusmcp_server.py dan api_server.py memiliki nama fungsi yang sama, yang dapat menyebabkan kebingungan dalam routing. Meskipun keduanya ada, potensi konflik ini harus diatasi untuk menjaga kejelasan dan konsistensi dalam API.
  - ➡️ ubah nama fungsi di salah satu file untuk menghindari konflik
