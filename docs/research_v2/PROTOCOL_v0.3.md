# Protokol research v2 — versi 0.3

Status: **didaftarkan dan dijalankan sampai gerbang fidelity; gerbang GAGAL (8 November 2026) → berhenti sesuai aturan. Tidak ada lock v0.3, tidak ada P11 di bawah v0.3.**
Test split tidak pernah dibuka.

## Hubungan dengan v0.2 (tetap tercatat)

| | v0.2 | v0.3 |
|---|---|---|
| Arsip | tag git `protocol-v0.2` (commit `23bc69c`); lock `results/research_v2/P10_protocol_lock/protocol_lock.json` (`0854491d…`) terverifikasi 0 masalah pada tag itu | artefak di `results/research_v2/v0.3/`; tag `protocol-v0.3` |
| Config simulasi, trace, JAR, normalisasi, P01–P06 | — | **identik dengan v0.2** (hash config `3e32379e…` sama) |
| Learner PPO | gamma 1,0 (bagian `ppo` di config; dikunci schema) | gamma **0,97** melalui `configs/research_v2/learner_v0.3.json` |
| K kandidat | 30.720 (ekstensi eksploratif P08 dengan learner gamma 1,0) | dipilih ulang oleh gerbang v0.3 → **tidak ada K yang lulus** |
| M3 | no-go: learner tidak belajar konsisten ([diagnosis](../../results/research_v2/P10_learning_diagnosis/report.md)) | no-go: gerbang fidelity gagal |

Lock v0.2 sengaja **tidak** lolos pada tree setelah tag (file yang dikuncinya berubah); itu perilaku yang benar dan diuji
(`test_v02_lock_is_preserved_but_superseded_on_this_tree`).

## Perubahan v0.3

1. **Learner:** gamma 0,97 (dipilih pada namespace pilot oleh diagnosis eksploratif: 1,0/0,99/0,98/0,97/0,95 → D 0,443/0,376/0,266/0,250/0,293).
   Hanya objektif training yang terdiskon; Dglobal, kelima biaya, dan metrik fisik tetap tidak terdiskon. Diterapkan lewat `research_v2/learner.py`
   ke trainer kandidat, final, baseline, search penuh, dan runner studi (`learner_version` tercatat di setiap manifest).
2. **Gerbang fidelity** (`research_v2/fidelity_v03.py`, aturan ditulis sebelum dijalankan): 48 model pilot (3 outer × 2 repeat × 8 bobot), ladder K
   10.240 → 20.480 → 30.720 → 51.200, referensi **F = 102.400** (v0.2: 51.200), ambang sama dengan v0.2 (median Spearman ≥ 0,60, tidak ada < 0),
   kesepakatan antar seed di F dilaporkan saja. Tidak boleh memperpanjang ladder di dalam protokol ini.
3. **Lock sadar-versi** (`P10-lock-2`) dengan pendahulu (hash lock v0.2 + tag), protokol learner, dan bukti diagnosis; jumlah worker dari kuota cgroup.

## Hasil gerbang

[`results/research_v2/v0.3/fidelity/`](../../results/research_v2/v0.3/fidelity/result.json) — 48 model, 600 s, 12 worker. Audit independen **lulus**
(hitung ulang dari baris episode, 48/48 model lengkap, 3/3 cek prefix independen identik). Model identik persis dengan run diagnosis (selisih D = 0,0),
karena seed pilot dan eksekusinya sama.

| K | Spearman outer 100 | 101 | 102 | median | hasil |
|---:|---:|---:|---:|---:|---|
| 10.240 | 0,048 | −0,381 | 0,405 | 0,048 | gagal |
| 20.480 | 0,429 | 0,619 | −0,095 | 0,429 | gagal |
| 30.720 | 0,690 | 0,476 | 0,167 | 0,476 | gagal |
| 51.200 | 0,643 | 0,357 | 0,214 | 0,357 | gagal |

Kesepakatan antar seed independen di F (repeat 0 vs repeat 1): 0,095 / 0,000 / 0,524 (median 0,095) — deskriptif.

**Pembacaan:**
- Dengan learner yang stabil pun, peringkat 8 bobot pada budget pendek tidak memprediksi peringkat pada F, dan dua seed independen pada F mengurutkan
  bobot secara berbeda. Untuk sebagian besar bobot, selisih antar-bobot lebih kecil dari variasi antar-seed.
- Namun **puncaknya konsisten**: pada F, vertex2 (0,92 pada zD) adalah bobot terbaik di ketiga outer (D 0,209 / 0,211 / 0,188), equal berada di peringkat
  2–3. Gerbang yang terdaftar memakai korelasi seluruh peringkat sehingga derau di tengah peringkat menggagalkannya. Ini pengamatan *setelah* hasil,
  sehingga **tidak boleh** dipakai mengubah gerbang v0.3; bila relevan, ia hanya dapat menjadi hipotesis untuk protokol baru dengan data baru.
- Seed pilot 100–102 kini sudah dipakai tiga kali (P07/P08, diagnosis P10, gerbang v0.3). Gerbang berikutnya yang jujur memerlukan seed pilot baru.

## Konsekuensi

Sesuai aturan: berhenti. Tidak ada lock v0.3, tidak ada pencarian penuh, P11 tidak dijalankan. Kode v0.3 (learner, penerusan versi, gerbang, lock
sadar-versi) tetap ada dan teruji, tetapi `build_lock` menolak membuat lock karena gerbang tidak lulus.
