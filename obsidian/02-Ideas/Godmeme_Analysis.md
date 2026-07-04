# Godmeme Bot Analysis

## Thesis
Bot trading godmeme berpotensi menghasilkan profit jika parameter dioptimasi.

## Data
- Total trades: 280
- Win rate: 15%
- PnL: -0.566 SOL

## Masalah Utama
1. Score threshold terlalu tinggi (10)
2. Bot hanya SELL, tidak ada BUY
3. Win rate rendah

## Hipotesis
- Turunkan score threshold ke 8 akan meningkatkan BUY signal
- Daily loss limit perlu dinaikkan

## Next Action
- Implementasi perubahan di strategy.py
- Test paper trading 1 minggu
