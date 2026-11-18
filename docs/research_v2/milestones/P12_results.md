# P12 — sensitivitas, audit akhir, dan paket reproduksi (protokol v0.4)

Status: **complete** (15 November 2026), kecuali pemetaan literatur/novelty yang menjadi tugas penulis.
Versi spesifikasi: protokol v0.4, lock `P10-lock-3` (sha256 `63d07e43…`), test dibuka 2026-11-09T11:30:56Z.
Git SHA saat run: `0ecaf5b` (kode P12: `research_v2/p12.py`, launcher `run_p12.sh`, tes `tests/research_v2/test_p12.py`).
Run: 2026-11-15T13:00Z → 18:36Z (≈ 5,6 jam, 12 worker), semua tahap exit normal. Log: `results/research_v2/v0.4/p12/pipeline/pipeline.log`.

**Semua hasil sensitivitas berlabel `exploratory_unadjusted`** (effect, 95% CI bootstrap crossed, p sign-flip exact mentah; tanpa
kontrol multiplisitas). Hasil konfirmatori tetap P11 ([P11_results.md](P11_results.md)). Temuan tidak dipakai untuk menyetel ulang apa pun.

## Tujuan dan perubahan

- Sensitivitas zero-shot satu-faktor-sekali pada 120 model P11 beku + 4 heuristik, split test, level dari blok `sensitivity` lock.
- Varian fisik = salinan JAR utama dengan satu entri `research_v2/default.json` diganti; semua kelas diverifikasi identik byte-per-byte.
  Fog homogen memakai JAR utama dengan opsi reset. Tidak ada file ter-lock yang diubah (preflight: 0 masalah, 2 peringatan = file baru P12).
- Normalisasi/penalti hanya pada split validation (5 trace × 4 workload, fisika utama), dihitung ulang dari baris episode yang sama.

## Verifikasi

| Pemeriksaan | Hasil |
|---|---|
| Kontrol mekanisme varian (identity) | 1.200 episode test P11 (nsga2_r00, equal_B_r07, greedy_eft_r00) direproduksi persis |
| Audit akhir (`p12/audit/audit.json`) | 7/7: lock deep-verify, build+config, catatan TEST_OPENED, 120 checkpoint, 49.600 baris episode vs trace test, laporan P11 dihitung ulang identik, ledger budget S/V/F/B |
| Reproduksi clone bersih (`p12/repro/result.json`) | isi entri JAR identik; kasus fisik (greedy_eft + nsga2_r00, trace validation 10000 light/heavy) identik; run PPO 1.024 keputusan: tensor policy `048351af…` identik |
| Episode di luar referensi [0, 1] | 0 pada semua varian |
| Tes unit | `test_p12` 9 tes; suite penuh 258 OK (1 skip) |

## Sensitivitas fisik (test, n = 20 outer run)

Selisih = D(pembanding) − D(NSGA-II), positif = NSGA-II lebih baik. Arah ketiga RQ sama dengan P11 pada **27/27** (3 RQ × 9 varian).

| Varian | RQ1 equal_F | RQ2 random | RQ3 equal_B | ρ peringkat vs main |
|---|---:|---:|---:|---:|
| main (P11) | 0,0198 | 0,0064 | −0,0781 | 1,000 |
| timeout k = 2 / 4 | 0,0208 / 0,0175 | 0,0043 / 0,0086 | −0,0823 / −0,0738 | 0,988 / 0,988 |
| antrian fog 8 / 32 | 0,0198 / 0,0199 | 0,0063 / 0,0064 | −0,0780 / −0,0781 | 1,000 / 1,000 |
| propagasi WAN 0,01 / 0,04 s | 0,0198 / 0,0199 | 0,0069 / 0,0053 | −0,0784 / −0,0769 | 0,988 / 0,988 |
| daya dinamis ×0,75 / ×1,25 | 0,0192 / 0,0201 | 0,0042 / 0,0075 | −0,0794 / −0,0769 | 1,000 / 1,000 |
| fog homogen (kontrol) | 0,0161 | 0,0084 | −0,0769 | 0,903 |

- RQ1/RQ2: CI selalu memuat 0 (p mentah 0,38–0,84). RQ3: selalu signifikan berlawanan arah (dz ≈ −1, p ≤ 4·10⁻⁵).
- Level D: timeout k = 2 menaikkan D semua metode (≈ +0,015), WAN 0,04 s ≈ +0,009; kapasitas antrian dan daya dinamis hampir tanpa efek
  (antrian tampaknya tidak pernah penuh pada beban ini; energi dinamis porsi kecil dari zE).
- NSGA-II PPO tetap jauh lebih baik dari always_local, nearest_fog, least_fog di semua varian.
- Satu-satunya perubahan arah (heuristik, bukan RQ): pada fog homogen greedy_eft sedikit lebih baik dari NSGA-II (−0,017,
  CI [−0,056; 0,017], p 0,39); D greedy_eft turun 0,263 → 0,229. Di konfigurasi utama juga tidak ada beda jelas (+0,017, p 0,37).

## Normalisasi dan penalti (validation)

Delapan definisi alternatif (referensi latency+penalti, penalti gagal saja, referensi energi, referensi imbalance; ×0,8 dan ×1,2):
arah RQ1–RQ3 sama pada semua definisi. Paling sensitif: referensi imbalance ×0,8 (RQ1 0,016; RQ3 −0,085). Definisi utama tetap yang dilaporkan.

## Deliverable dan lokasi artefak (`results/research_v2/v0.4/p12/`)

- `sensitivity/report.md|json` — laporan sensitivitas lengkap (semua metode, metrik dan perbandingan per varian).
- `audit/audit.json`, `audit/model_index.json`, `audit/recomputed_p11/` — audit akhir.
- `repro/result.json`, `repro/worker.py`, `repro/*_physical.json` — uji reproduksi.
- `package/ARTIFACT_INDEX.json`, `SHA256SUMS`, `README_REPRODUCTION.md` — indeks artefak dan checksum (120 `model.zip` lokal di-hash).
- `claims.md` — tabel klaim dan batasnya.
- `variants/` — config tiap varian dan `index.json` (hash JAR varian). JAR varian dibangun ulang otomatis oleh `p12.py` (`ifogsim/dist_p12/`, tidak di git).

## Tabel klaim

| Klaim | Status |
|---|---|
| RQ1 NSGA-II vs equal_F | tidak didukung (bukti kurang, bukan kesetaraan); arah dipertahankan 9/9 varian |
| RQ2 NSGA-II vs random | tidak didukung; arah dipertahankan 9/9 varian |
| RQ3 search + F vs equal_B (compute B) | bertentangan: equal_B jauh lebih baik; konsisten 9/9 varian |
| Eksploratif heuristik | PPO lebih baik dari always_local/nearest_fog/least_fog; tidak ada beda jelas dengan greedy_eft |

## Risiko/keterbatasan tersisa

- Sensitivitas zero-shot pada model beku; tidak menunjukkan robustness setelah retraining. Satu topologi, workload sintetis, simulasi saja.
- Arsip artefak besar (checkpoint, log keputusan, episode sensitivitas ≈ 640 MB) masih lokal di server; lihat `ARTIFACTS_NOT_IN_GIT.md`.
- `package/ARTIFACT_INDEX.json` dibuat sebelum commit hasil P12, sehingga file P12 sendiri tercatat belum ter-track.
- **Pemetaan literatur terdekat dan pernyataan novelty belum diperbarui** — wajib oleh penulis sebelum klaim state of the art.

## Keputusan dan phase berikutnya

Rencana implementasi research v2 (P00–P12) selesai secara teknis. Langkah berikutnya di luar rencana: arsip artefak besar ke
penyimpanan terpisah, pemetaan literatur, dan penyusunan manuskrip dari laporan P11 + P12.
