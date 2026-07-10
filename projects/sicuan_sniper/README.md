# SiCuan Sniper

Trading engine modular untuk menemukan, menganalisis, dan (opsional) mengeksekusi
trade token baru di Solana. Dibangun sebagai modul SiCuan.

## Yang perlu kamu tahu dulu — jujur, bukan disclaimer basa-basi

- **Tidak ada sistem yang "anti rugi".** Mayoritas token baru di Pump.fun/Raydium
  adalah rug pull atau honeypot. Scoring engine di sini mengurangi risiko yang
  bisa dideteksi (mint authority, freeze authority, LP lock, distribusi holder),
  tapi tidak bisa mendeteksi niat jahat developer yang belum action.
- **Klaim "$5 jadi $100 dalam sehari" bukan target yang bisa direkayasa jadi
  fitur software.** Itu levelnya spekulasi tinggi. Yang bisa direkayasa: disiplin
  risk management (stop loss, position sizing, circuit breaker) supaya rugi
  **dibatasi**, bukan dihilangkan.
- **Default: `PAPER_TRADING=true`.** Semua eksekusi disimulasikan, tidak ada
  transaksi on-chain, tidak butuh private key nyata. Kamu yang putuskan kapan
  (dan apakah) mau nyalakan live trading, setelah kamu ngerti risikonya.
- Live execution (Jupiter/Raydium swap nyata) di kode ini ditulis sebagai
  **skeleton yang jelas TODO-nya** — saya tidak menulis modul yang langsung
  bisa menghabiskan wallet asli tanpa kamu review dan lengkapi sendiri.

## Setup di VPS via Termux (SSH)

```bash
# dari Termux
ssh user@vps_ip

# di VPS
cd ~
unzip sicuan_sniper.zip
cd sicuan_sniper
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env          # isi RPC_URL, dan var lain sesuai kebutuhan

python3 main.py     # jalan dalam mode paper trading
```

## Struktur

```
sicuan_sniper/
  config/settings.py          konfigurasi via .env, tervalidasi
  core/models.py              dataclass: Token, Trade, Position, Signal
  core/database.py            SQLite storage (abstraksi, gampang pindah ke Postgres)
  core/logger.py               logging terstruktur
  discovery/                   Discovery Engine — cari token baru
    sources/dexscreener.py     REAL — pakai public API DexScreener
    sources/birdeye.py         stub — butuh API key Birdeye
    sources/pumpfun.py         stub — butuh websocket Pump.fun
    sources/raydium.py         stub — butuh indexer Raydium
    discovery_engine.py        queue prioritas, dedup, cache, retry, failover
  analyzer/token_analyzer.py   analisis on-chain + off-chain per token
  analyzer/scoring_engine.py   weighted scoring -> total score
  decision/decision_engine.py  BUY / WATCH / SKIP / SELL / EMERGENCY_EXIT
  risk/risk_manager.py         daily loss limit, position size, circuit breaker
  execution/execution_engine.py paper trading (real) + live swap (skeleton)
  portfolio/position_manager.py TP bertingkat, trailing stop, hard stop, PnL
  learning/learning_engine.py  rule-based, belajar dari histori trade
  reporting/reporting_engine.py win rate, sharpe, drawdown, profit factor
  strategies/                 profil strategi (ultra_early, momentum, dst)
  main.py                     orchestrator loop
  tests/                      unit test untuk scoring & risk
```

## Alur data

```
DiscoveryEngine.poll()
    -> Token baru (raw)
TokenAnalyzer.analyze(token)
    -> AnalysisResult (liquidity, holders, authorities, dll)
ScoringEngine.score(analysis)
    -> Score (0-100, breakdown per kategori)
DecisionEngine.decide(token, analysis, score, portfolio_state)
    -> Signal(action=BUY/WATCH/SKIP/SELL/EMERGENCY_EXIT, reason=...)
RiskManager.approve(signal, portfolio_state)
    -> disetujui / ditolak (+ alasan)
ExecutionEngine.execute(signal)          # paper atau live
    -> Trade
PositionManager.update(trade)
    -> tracks open positions, cek TP/SL tiap tick
LearningEngine.record(closed_trade)
    -> update rule weights berdasarkan outcome
ReportingEngine.generate()
    -> laporan harian/mingguan/per strategi
```

## Menjalankan test

```bash
python3 -m pytest tests/ -v
```

## Yang SENGAJA tidak saya buat penuh

- Eksekusi swap live ke Jupiter/Raydium/PumpSwap dengan private key nyata —
  `execution/execution_engine.py` punya kelas `LiveExecutor` dengan struktur
  lengkap (retry, slippage, priority fee, simulation) tapi bagian tanda-tangan
  transaksi sengaja saya beri `NotImplementedError` dengan instruksi jelas,
  supaya kamu tidak tidak sengaja menjalankan bot nge-trade uang asli dari kode
  yang belum kamu review baris per baris.
- Deteksi honeypot/scam yang 100% akurat — tidak ada yang bisa menjamin ini;
  yang ada adalah heuristik (mint/freeze authority, LP lock, holder
  concentration) yang mengurangi risiko, bukan menghilangkannya.
