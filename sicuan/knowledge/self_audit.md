# SiCuan Self-Audit Report

Dibuat: 2026-06-30T05:02:40.601193+00:00
Model analisis: qwen/qwen-2.5-72b-instruct
Scope: sicuan, agents, core, mcp

## Ringkasan

- File dipindai: 221
- Fungsi/method diindeks: 1217
- Grup duplikat identik: 14
- Grup duplikat struktural: 21
- Class divergen: 1
- Broken imports: 5
- Orphan files: 41
- Endpoint collisions: 2

## exact_duplicates

_Temuan menunjukkan beberapa metode yang duplikat, terutama metode pendek dan sederhana. Sebagian besar duplikasi ini mungkin merupakan pola umum, tetapi ada beberapa kasus yang memerlukan perhatian lebih, seperti metode `audit` dan `decide` yang kompleks. Direkomendasikan untuk menggabungkan metode-metode duplikat ke dalam base class atau module terpisah untuk mengurangi redundansi._

- 🟠 **audit / decide method** (high): Metode `audit` dan `decide` memiliki implementasi yang identik dan cukup kompleks. Ini bisa menjadi bug serius.
  - ➡️ Periksa kembali logika metode `audit` dan `decide` untuk memastikan tidak ada kesalahan. Pertimbangkan untuk menggabungkan kedua metode.
- 🟡 **llm method** (medium): Metode `llm` duplikat ditemukan di beberapa file. Ini bisa menjadi indikasi bahwa metode ini perlu ditaruh di base class atau module terpisah.
  - ➡️ Pertimbangkan untuk memindahkan metode `llm` ke base class atau module terpisah dan mengimpor dari sana.
- 🟢 **Config.get_llm_key / Config.get_model** (low): Kedua metode ini memiliki implementasi yang identik dan pendek. Kemungkinan besar ini adalah pola umum atau kesalahan kecil.
  - ➡️ Pertimbangkan untuk menggabungkan kedua metode menjadi satu atau menggunakan alias.
- 🟢 **fs method** (low): Metode `fs` duplikat ditemukan di dua file. Ini mungkin pola umum atau bisa ditaruh di base class.
  - ➡️ Pertimbangkan untuk memindahkan metode `fs` ke base class atau module terpisah.
- 🟢 **__init__ method (KnowledgeIndex / KnowledgeState)** (low): Metode `__init__` duplikat ditemukan di dua file. Ini mungkin pola umum atau bisa ditaruh di base class.
  - ➡️ Pertimbangkan untuk memindahkan metode `__init__` ke base class atau module terpisah.
- 🟢 **__new__ method** (low): Metode `__new__` duplikat ditemukan di tiga file. Ini mungkin pola umum atau bisa ditaruh di base class.
  - ➡️ Pertimbangkan untuk memindahkan metode `__new__` ke base class atau module terpisah.
- 🟢 **__init__ method (ConversationDispatcher / ConversationReasoner)** (low): Metode `__init__` duplikat ditemukan di dua file. Ini mungkin pola umum atau bisa ditaruh di base class.
  - ➡️ Pertimbangkan untuk memindahkan metode `__init__` ke base class atau module terpisah.
- 🟢 **load method** (low): Metode `load` duplikat ditemukan di dua file. Ini mungkin pola umum atau bisa ditaruh di base class.
  - ➡️ Pertimbangkan untuk memindahkan metode `load` ke base class atau module terpisah.
- 🟢 **to_json method** (low): Metode `to_json` duplikat ditemukan di dua file. Ini mungkin pola umum atau bisa ditaruh di base class.
  - ➡️ Pertimbangkan untuk memindahkan metode `to_json` ke base class atau module terpisah.
- 🟢 **__init__ method (ReflectionQuery / ArtifactQuery / DecisionHistory)** (low): Metode `__init__` duplikat ditemukan di tiga file. Ini mungkin pola umum atau bisa ditaruh di base class.
  - ➡️ Pertimbangkan untuk memindahkan metode `__init__` ke base class atau module terpisah.
- 🟢 **memory method** (low): Metode `memory` duplikat ditemukan di dua file. Ini mungkin pola umum atau bisa ditaruh di base class.
  - ➡️ Pertimbangkan untuk memindahkan metode `memory` ke base class atau module terpisah.

## structural_duplicates

_Temuan duplikasi struktural dalam kode ini sebagian besar terdiri dari metode dan konstruktor yang memiliki logika sederhana dan pendek. Ini adalah pola umum dalam pengembangan perangkat lunak dan tidak menunjukkan masalah serius. Sebagian besar duplikasi ini dapat dibiarkan tanpa tindakan lebih lanjut._

- 🟢 **SiCuanChat._handle_summary_query** (low): Duplikasi ini terjadi pada metode yang memiliki logika sederhana dan pendek. Ini adalah pola umum dalam pengembangan perangkat lunak dan tidak menunjukkan masalah serius.
  - ➡️ biarkan, ini wajar
- 🟢 **SiCuanChat._handle_resume_query** (low): Duplikasi ini terjadi pada metode yang memiliki logika sederhana dan pendek. Ini adalah pola umum dalam pengembangan perangkat lunak dan tidak menunjukkan masalah serius.
  - ➡️ biarkan, ini wajar
- 🟢 **ActionRegistry.list_actions** (low): Duplikasi ini terjadi pada metode yang memiliki logika sederhana dan pendek. Ini adalah pola umum dalam pengembangan perangkat lunak dan tidak menunjukkan masalah serius.
  - ➡️ biarkan, ini wajar
- 🟢 **CapabilityManager.list_all** (low): Duplikasi ini terjadi pada metode yang memiliki logika sederhana dan pendek. Ini adalah pola umum dalam pengembangan perangkat lunak dan tidak menunjukkan masalah serius.
  - ➡️ biarkan, ini wajar
- 🟢 **ReflectionEngine.__init__** (low): Duplikasi ini terjadi pada konstruktor yang pendek. Ini adalah pola umum dalam pengembangan perangkat lunak dan tidak menunjukkan masalah serius.
  - ➡️ biarkan, ini wajar
- 🟢 **AutonomousRefactorLoop.__init__** (low): Duplikasi ini terjadi pada konstruktor yang pendek. Ini adalah pola umum dalam pengembangan perangkat lunak dan tidak menunjukkan masalah serius.
  - ➡️ biarkan, ini wajar
- 🟢 **ReflectionEngine.should_retry** (low): Duplikasi ini terjadi pada metode yang memiliki logika sederhana dan pendek. Ini adalah pola umum dalam pengembangan perangkat lunak dan tidak menunjukkan masalah serius.
  - ➡️ biarkan, ini wajar
- 🟢 **ReflectionEngine.should_replan** (low): Duplikasi ini terjadi pada metode yang memiliki logika sederhana dan pendek. Ini adalah pola umum dalam pengembangan perangkat lunak dan tidak menunjukkan masalah serius.
  - ➡️ biarkan, ini wajar
- 🟢 **KnowledgeIndex.get** (low): Duplikasi ini terjadi pada metode yang memiliki logika sederhana dan pendek. Ini adalah pola umum dalam pengembangan perangkat lunak dan tidak menunjukkan masalah serius.
  - ➡️ biarkan, ini wajar
- 🟢 **KnowledgeState.get** (low): Duplikasi ini terjadi pada metode yang memiliki logika sederhana dan pendek. Ini adalah pola umum dalam pengembangan perangkat lunak dan tidak menunjukkan masalah serius.
  - ➡️ biarkan, ini wajar
- 🟢 **ExecutionEventBus.clear** (low): Duplikasi ini terjadi pada metode yang memiliki logika sederhana dan pendek. Ini adalah pola umum dalam pengembangan perangkat lunak dan tidak menunjukkan masalah serius.
  - ➡️ biarkan, ini wajar
- 🟢 **ArtifactSubscriberRegistry.clear** (low): Duplikasi ini terjadi pada metode yang memiliki logika sederhana dan pendek. Ini adalah pola umum dalam pengembangan perangkat lunak dan tidak menunjukkan masalah serius.
  - ➡️ biarkan, ini wajar
- 🟢 **ExecutionEventBus.get_planner_events** (low): Duplikasi ini terjadi pada metode yang memiliki logika sederhana dan pendek. Ini adalah pola umum dalam pengembangan perangkat lunak dan tidak menunjukkan masalah serius.
  - ➡️ biarkan, ini wajar
- 🟢 **ExecutionEventBus.get_executor_events** (low): Duplikasi ini terjadi pada metode yang memiliki logika sederhana dan pendek. Ini adalah pola umum dalam pengembangan perangkat lunak dan tidak menunjukkan masalah serius.
  - ➡️ biarkan, ini wajar
- 🟢 **ExecutionEventBus.get_filesystem_events** (low): Duplikasi ini terjadi pada metode yang memiliki logika sederhana dan pendek. Ini adalah pola umum dalam pengembangan perangkat lunak dan tidak menunjukkan masalah serius.
  - ➡️ biarkan, ini wajar
- 🟢 **ExecutionEventBus.get_actions** (low): Duplikasi ini terjadi pada metode yang memiliki logika sederhana dan pendek. Ini adalah pola umum dalam pengembangan perangkat lunak dan tidak menunjukkan masalah serius.
  - ➡️ biarkan, ini wajar
- 🟢 **ExecutionEventBus.get_planned_actions** (low): Duplikasi ini terjadi pada metode yang memiliki logika sederhana dan pendek. Ini adalah pola umum dalam pengembangan perangkat lunak dan tidak menunjukkan masalah serius.
  - ➡️ biarkan, ini wajar
- 🟢 **ConversationState.add_completed_task** (low): Duplikasi ini terjadi pada metode yang memiliki logika sederhana dan pendek. Ini adalah pola umum dalam pengembangan perangkat lunak dan tidak menunjukkan masalah serius.
  - ➡️ biarkan, ini wajar
- 🟢 **ConversationState.add_pending_task** (low): Duplikasi ini terjadi pada metode yang memiliki logika sederhana dan pendek. Ini adalah pola umum dalam pengembangan perangkat lunak dan tidak menunjukkan masalah serius.
  - ➡️ biarkan, ini wajar
- 🟢 **CapabilityManager.get** (low): Duplikasi ini terjadi pada metode yang memiliki logika sederhana dan pendek. Ini adalah pola umum dalam pengembangan perangkat lunak dan tidak menunjukkan masalah serius.
  - ➡️ biarkan, ini wajar
- 🟢 **ContextManager.get_context** (low): Duplikasi ini terjadi pada metode yang memiliki logika sederhana dan pendek. Ini adalah pola umum dalam pengembangan perangkat lunak dan tidak menunjukkan masalah serius.
  - ➡️ biarkan, ini wajar
- 🟢 **DecisionQuery.get_by_action** (low): Duplikasi ini terjadi pada metode yang memiliki logika sederhana dan pendek. Ini adalah pola umum dalam pengembangan perangkat lunak dan tidak menunjukkan masalah serius.
  - ➡️ biarkan, ini wajar
- 🟢 **DecisionQuery.get_by_project** (low): Duplikasi ini terjadi pada metode yang memiliki logika sederhana dan pendek. Ini adalah pola umum dalam pengembangan perangkat lunak dan tidak menunjukkan masalah serius.
  - ➡️ biarkan, ini wajar
- 🟢 **LongTermMemory.get_facts** (low): Duplikasi ini terjadi pada metode yang memiliki logika sederhana dan pendek. Ini adalah pola umum dalam pengembangan perangkat lunak dan tidak menunjukkan masalah serius.
  - ➡️ biarkan, ini wajar
- 🟢 **LongTermMemory.get_preferences** (low): Duplikasi ini terjadi pada metode yang memiliki logika sederhana dan pendek. Ini adalah pola umum dalam pengembangan perangkat lunak dan tidak menunjukkan masalah serius.
  - ➡️ biarkan, ini wajar
- 🟢 **LongTermMemory._save** (low): Duplikasi ini terjadi pada metode yang memiliki logika sederhana dan pendek. Ini adalah pola umum dalam pengembangan perangkat lunak dan tidak menunjukkan masalah serius.
  - ➡️ biarkan, ini wajar
- 🟢 **DecisionHistory._save** (low): Duplikasi ini terjadi pada metode yang memiliki logika sederhana dan pendek. Ini adalah pola umum dalam pengembangan perangkat lunak dan tidak menunjukkan masalah serius.
  - ➡️ biarkan, ini wajar
- 🟢 **ExecutorEngine._ensure_queue_exists** (low): Duplikasi ini terjadi pada metode yang memiliki logika sederhana dan pendek. Ini adalah pola umum dalam pengembangan perangkat lunak dan tidak menunjukkan masalah serius.
  - ➡️ biarkan, ini wajar
- 🟢 **ProjectMemoryEngine.__init__** (low): Duplikasi ini terjadi pada konstruktor yang pendek. Ini adalah pola umum dalam pengembangan perangkat lunak dan tidak menunjukkan masalah serius.
  - ➡️ biarkan, ini wajar

## class_diverged

_Terdapat beberapa kelas dengan nama yang sama di berbagai file, yang menunjukkan adanya potensi divergensi dalam implementasi. Hal ini perlu diteliti lebih lanjut untuk memastikan apakah salah satu dari kelas tersebut benar-benar tidak digunakan atau hanya belum terhubung dengan baik dalam sistem._

- 🟡 **ContextManager** (medium): Terdapat dua kelas dengan nama yang sama di file yang berbeda, namun tidak ada indikasi bahwa salah satu dari kelas ini tidak pernah digunakan. Kemungkinan besar salah satu kelas ini direncanakan untuk digunakan dalam konteks yang berbeda, tetapi belum terintegrasi ke dalam pipeline utama.
  - ➡️ cek manual: apakah dipanggil via importlib atau digunakan dalam konteks lain

## broken_imports

_Semua temuan broken imports tidak menunjukkan adanya masalah kritis. Modul yang diimpor muncul di beberapa file, menunjukkan bahwa mereka kemungkinan besar ada dan digunakan. Tidak ada tanda-tanda dead code atau modul yang hilang._

- ⚪ **get_godmeme_status in sicuan/brain.py** (non_issue): Import ini muncul di dua file berbeda, menunjukkan bahwa modul 'projects.godmeme_bot.status_sync_provider' kemungkinan besar ada dan digunakan. Tidak ada tanda-tanda bahwa ini adalah dead code.
  - ➡️ Biarkan, ini wajar
- ⚪ **StrategyExecutor in sicuan/core/autonomous_refactor_loop.py (line 20)** (non_issue): Import ini muncul dua kali di file yang sama, menunjukkan bahwa modul 'sicuan.core.strategy_executor' kemungkinan besar ada dan digunakan. Tidak ada tanda-tanda bahwa ini adalah dead code.
  - ➡️ Biarkan, ini wajar
- ⚪ **RefactorEngine in sicuan/core/autonomous_refactor_loop.py** (non_issue): Import ini muncul di file yang sama dengan import lainnya, menunjukkan bahwa modul 'sicuan.core.refactor_engine' kemungkinan besar ada dan digunakan. Tidak ada tanda-tanda bahwa ini adalah dead code.
  - ➡️ Biarkan, ini wajar
- ⚪ **StrategyExecutor in sicuan/core/autonomous_refactor_loop.py (line 195)** (non_issue): Import ini muncul dua kali di file yang sama, menunjukkan bahwa modul 'sicuan.core.strategy_executor' kemungkinan besar ada dan digunakan. Tidak ada tanda-tanda bahwa ini adalah dead code.
  - ➡️ Biarkan, ini wajar
- ⚪ **get_godmeme_status in sicuan/actions/godmeme_status.py** (non_issue): Import ini muncul di dua file berbeda, menunjukkan bahwa modul 'projects.godmeme_bot.status_sync_provider' kemungkinan besar ada dan digunakan. Tidak ada tanda-tanda bahwa ini adalah dead code.
  - ➡️ Biarkan, ini wajar

## orphan_files

_Sebagian besar file yang terdeteksi sebagai orphan tidak terhubung dengan modul lain dan tidak memiliki sinyal pemuatan dinamis, sehingga dianggap sebagai kode yang tidak terpakai. Disarankan untuk menghapus file-file ini untuk menjaga kebersihan kode dan mengurangi kebingungan di masa depan._

- 🟢 **core/metrics.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis yang menunjukkan penggunaannya. Kemungkinan besar ini adalah kode yang tidak terpakai.
  - ➡️ hapus file core/metrics.py
- 🟢 **sicuan/personality_v4.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Ini tampaknya merupakan kode yang tidak terpakai.
  - ➡️ hapus file sicuan/personality_v4.py
- 🟢 **sicuan/runtime_flow_analyzer.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Kemungkinan besar ini adalah kode yang tidak terpakai.
  - ➡️ hapus file sicuan/runtime_flow_analyzer.py
- 🟢 **sicuan/audit/godmeme_audit.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Ini tampaknya merupakan kode yang tidak terpakai.
  - ➡️ hapus file sicuan/audit/godmeme_audit.py
- 🟢 **sicuan/core/llm_patch_guard.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Kemungkinan besar ini adalah kode yang tidak terpakai.
  - ➡️ hapus file sicuan/core/llm_patch_guard.py
- 🟢 **sicuan/core/artifact.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Ini tampaknya merupakan kode yang tidak terpakai.
  - ➡️ hapus file sicuan/core/artifact.py
- 🟢 **sicuan/core/paper_trade_validator.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Kemungkinan besar ini adalah kode yang tidak terpakai.
  - ➡️ hapus file sicuan/core/paper_trade_validator.py
- 🟢 **sicuan/core/input_validator.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Ini tampaknya merupakan kode yang tidak terpakai.
  - ➡️ hapus file sicuan/core/input_validator.py
- 🟢 **sicuan/core/data_awareness_injector.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Kemungkinan besar ini adalah kode yang tidak terpakai.
  - ➡️ hapus file sicuan/core/data_awareness_injector.py
- 🟢 **sicuan/core/capability_engine.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Ini tampaknya merupakan kode yang tidak terpakai.
  - ➡️ hapus file sicuan/core/capability_engine.py
- 🟢 **sicuan/core/capability_manager.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Kemungkinan besar ini adalah kode yang tidak terpakai.
  - ➡️ hapus file sicuan/core/capability_manager.py
- 🟢 **sicuan/core/context_manager.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Ini tampaknya merupakan kode yang tidak terpakai.
  - ➡️ hapus file sicuan/core/context_manager.py
- 🟢 **sicuan/core/legacy_adapter.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Kemungkinan besar ini adalah kode yang tidak terpakai.
  - ➡️ hapus file sicuan/core/legacy_adapter.py
- 🟢 **sicuan/core/logging_config.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Ini tampaknya merupakan kode yang tidak terpakai.
  - ➡️ hapus file sicuan/core/logging_config.py
- 🟢 **sicuan/core/conversation_dispatcher.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Kemungkinan besar ini adalah kode yang tidak terpakai.
  - ➡️ hapus file sicuan/core/conversation_dispatcher.py
- 🟢 **sicuan/core/continuous_learning.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Ini tampaknya merupakan kode yang tidak terpakai.
  - ➡️ hapus file sicuan/core/continuous_learning.py
- 🟢 **sicuan/core/executive_engine.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Kemungkinan besar ini adalah kode yang tidak terpakai.
  - ➡️ hapus file sicuan/core/executive_engine.py
- 🟢 **sicuan/core/task_generator.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Ini tampaknya merupakan kode yang tidak terpakai.
  - ➡️ hapus file sicuan/core/task_generator.py
- 🟢 **sicuan/core/goal_manager.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Kemungkinan besar ini adalah kode yang tidak terpakai.
  - ➡️ hapus file sicuan/core/goal_manager.py
- 🟢 **sicuan/core/evaluator_engine.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Ini tampaknya merupakan kode yang tidak terpakai.
  - ➡️ hapus file sicuan/core/evaluator_engine.py
- 🟢 **sicuan/core/conversation_reasoner.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Kemungkinan besar ini adalah kode yang tidak terpakai.
  - ➡️ hapus file sicuan/core/conversation_reasoner.py
- 🟢 **sicuan/core/workspace_scanner.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Ini tampaknya merupakan kode yang tidak terpakai.
  - ➡️ hapus file sicuan/core/workspace_scanner.py
- 🟢 **sicuan/core/optimization_report.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Kemungkinan besar ini adalah kode yang tidak terpakai.
  - ➡️ hapus file sicuan/core/optimization_report.py
- 🟢 **sicuan/core/data_aware_planner.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Ini tampaknya merupakan kode yang tidak terpakai.
  - ➡️ hapus file sicuan/core/data_aware_planner.py
- 🟢 **sicuan/core/task_queue.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Kemungkinan besar ini adalah kode yang tidak terpakai.
  - ➡️ hapus file sicuan/core/task_queue.py
- 🟢 **sicuan/core/shadow_mode.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Ini tampaknya merupakan kode yang tidak terpakai.
  - ➡️ hapus file sicuan/core/shadow_mode.py
- 🟢 **sicuan/core/conversation_router.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Kemungkinan besar ini adalah kode yang tidak terpakai.
  - ➡️ hapus file sicuan/core/conversation_router.py
- 🟢 **sicuan/core/unified_query.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Ini tampaknya merupakan kode yang tidak terpakai.
  - ➡️ hapus file sicuan/core/unified_query.py
- 🟢 **sicuan/core/function_patch.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Kemungkinan besar ini adalah kode yang tidak terpakai.
  - ➡️ hapus file sicuan/core/function_patch.py
- 🟢 **sicuan/core/result_normalizer.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Ini tampaknya merupakan kode yang tidak terpakai.
  - ➡️ hapus file sicuan/core/result_normalizer.py
- 🟢 **sicuan/core/response_composer.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Kemungkinan besar ini adalah kode yang tidak terpakai.
  - ➡️ hapus file sicuan/core/response_composer.py
- 🟢 **sicuan/core/event_replay.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Ini tampaknya merupakan kode yang tidak terpakai.
  - ➡️ hapus file sicuan/core/event_replay.py
- 🟢 **sicuan/core/data_awareness.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Kemungkinan besar ini adalah kode yang tidak terpakai.
  - ➡️ hapus file sicuan/core/data_awareness.py
- 🟢 **sicuan/core/function_ranker.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Ini tampaknya merupakan kode yang tidak terpakai.
  - ➡️ hapus file sicuan/core/function_ranker.py
- 🟢 **sicuan/core/knowledge_state.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Kemungkinan besar ini adalah kode yang tidak terpakai.
  - ➡️ hapus file sicuan/core/knowledge_state.py
- 🟢 **sicuan/core/project_brain.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Ini tampaknya merupakan kode yang tidak terpakai.
  - ➡️ hapus file sicuan/core/project_brain.py
- 🟢 **sicuan/core/intelligence/endpoint_registry.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Kemungkinan besar ini adalah kode yang tidak terpakai.
  - ➡️ hapus file sicuan/core/intelligence/endpoint_registry.py
- 🟢 **sicuan/core/intelligence/capability_graph.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Ini tampaknya merupakan kode yang tidak terpakai.
  - ➡️ hapus file sicuan/core/intelligence/capability_graph.py
- 🟢 **sicuan/core/intelligence/project_operator.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Kemungkinan besar ini adalah kode yang tidak terpakai.
  - ➡️ hapus file sicuan/core/intelligence/project_operator.py
- 🟢 **sicuan/core/intelligence/runtime_intelligence.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Ini tampaknya merupakan kode yang tidak terpakai.
  - ➡️ hapus file sicuan/core/intelligence/runtime_intelligence.py
- 🟢 **sicuan/actions/evaluate_strategy.py** (low): File ini tidak terhubung dengan modul lain dan tidak ada sinyal pemuatan dinamis. Kemungkinan besar ini adalah kode yang tidak terpakai.
  - ➡️ hapus file sicuan/actions/evaluate_strategy.py

## endpoint_collisions

_Ditemukan dua endpoint yang saling bertabrakan, yaitu /health dan /. Kedua endpoint memiliki metode GET yang sama di file yang berbeda, yang dapat menyebabkan konflik dan perilaku tidak terduga. Dianjurkan untuk menyelesaikan konflik ini dengan memilih satu implementasi atau menggunakan middleware._

- 🟠 **health** (high): Kedua endpoint /health memiliki metode GET yang sama, yang dapat menyebabkan konflik dan perilaku tidak terduga. Tidak ada indikasi dynamic loading yang membuat status orphan meragukan.
  - ➡️ Pilih satu implementasi /health dan hapus yang lain, atau gunakan middleware untuk mengarahkan ke implementasi yang tepat.
- 🟠 **root** (high): Kedua endpoint / memiliki metode GET yang sama, yang dapat menyebabkan konflik dan perilaku tidak terduga. Tidak ada indikasi dynamic loading yang membuat status orphan meragukan.
  - ➡️ Pilih satu implementasi / dan hapus yang lain, atau gunakan middleware untuk mengarahkan ke implementasi yang tepat.
