# P11 — hasil konfirmatori protokol v0.4

- Lock: `results/research_v2/v0.4/protocol_lock/protocol_lock.json` (`P10-lock-3`, sha256 `63d07e43…`).
- Training: 120/120 job complete pada 10 shard (2026-11-08T02:46Z → 2026-11-09T11:15Z, ≈ 32,5 jam; estimasi 61 jam). Semua shard exit 0.
- Test dibuka 2026-11-09T11:30:56Z (`results/research_v2/TEST_OPENED.json`); evaluasi 120 model + 4 heuristik, 0 error.
- Laporan lengkap: `results/research_v2/v0.4/p11/test_evaluation/report.md` (analisis konfirmatori, n = 20 outer run).

## Uji primer (Holm, α = 0,05; selisih = D(pembanding) − D(NSGA-II), positif = NSGA-II lebih baik)

| Uji | Pembanding | Selisih | 95% CI | dz | p exact | Holm p |
|---|---|---:|---|---:|---:|---:|
| RQ1 | equal_F | 0,0198 (7,5 %) | [−0,0284; 0,0639] | 0,185 | 0,4244 | 0,8487 |
| RQ2 | random | 0,0064 (2,5 %) | [−0,0279; 0,0459] | 0,072 | 0,7682 | 0,8487 |
| RQ3 | equal_B | −0,0781 (−46,7 %) | [−0,1134; −0,0471] | −1,006 | 9,5e−6 | 2,9e−5 |

Dglobal rata-rata: equal_B 0,167; manual_B 0,169; nsga2 0,245; random 0,252; greedy_eft 0,263; equal_F 0,265; manual_F 0,260;
always_local 0,372; least_fog 0,476; nearest_fog 0,514.

## Interpretasi

1. RQ1: dengan budget training final yang sama (F = 102.400), bobot NSGA-II tidak terbukti lebih baik dari bobot equal (arah positif, CI memuat 0).
2. RQ2: NSGA-II tidak terbukti lebih baik dari random search atas bobot.
3. RQ3: pada compute total yang setara, melatih PPO lebih lama dengan bobot equal (B ≈ 19,6 juta keputusan) jauh lebih baik daripada
   search bobot + training final F; konsisten di keempat workload (secondary Holm signifikan terutama pada heavy/dynamic).
4. Eksploratif: semua PPO jauh lebih baik dari always_local/nearest_fog/least_fog; NSGA-II tidak berbeda nyata dari greedy_eft (p = 0,37).

Sesuai aturan protokol, temuan test dicatat dan tidak dipakai untuk menyetel ulang studi ini. Non-signifikan berarti bukti tidak cukup, bukan kesetaraan.
