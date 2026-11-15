# Protokol research v2 — versi 0.4

Status: **P11 selesai (9 November 2026). Lock v0.4 (`P10-lock-3`, `63d07e43…`); test dibuka 2026-11-09T11:30:56Z. Hasil: [P11_results.md](milestones/P11_results.md).**
Keputusan M3 = *go* diberikan oleh operator dengan menjalankan pipeline dengan `go`.

## Silsilah protokol

| Versi | Inti | Hasil | Arsip |
|---|---|---|---|
| v0.2 | learner gamma 1,0; K = 30.720 (ekstensi P08) | M3 no-go: PPO tidak belajar konsisten | tag `protocol-v0.2`; lock `0854491d…` |
| v0.3 | learner gamma 0,97; gerbang fidelity diulang | gerbang gagal pada semua K → berhenti | tag `protocol-v0.3`; [PROTOCOL_v0.3.md](PROTOCOL_v0.3.md) |
| **v0.4** | learner gamma 0,97; **K = F = 102.400** | P11 selesai: RQ1/RQ2 null, RQ3 negatif | `results/research_v2/v0.4/`, [desain](../../configs/research_v2/design_v0.4.json) |

v0.4 tidak mengubah simulasi (config, trace, JAR, normalisasi, P01–P06), learner v0.3, 80 slot × 2 model, F, kontrak reuse protokol A/B,
maupun registri hipotesis (3 primer + 60 sekunder, Holm, bootstrap crossed). Satu-satunya perubahan desain: setiap kandidat dilatih penuh F,
sehingga tidak ada proxy budget pendek dan tidak ada gerbang fidelity proxy. Perubahan operasional: log keputusan ditulis langsung dalam gzip,
P11 dijalankan dalam 10 shard paralel (kuota container 16 CPU / 64 GiB).

**Keterbatasan yang sudah diketahui sebelum P11:** pada pilot, dua seed independen mengurutkan 8 bobot pilot dengan median Spearman 0,095 pada F;
hanya bobot terbaik (vertex2) yang konsisten. Daya uji RQ1–RQ3 bisa terbatas; hasil null dilaporkan penuh. Seed konfirmatori 0–19 pernah dipakai
untuk pemeriksaan eksploratif validasi-saja di P10 (learner v0.2); test tidak pernah disentuh.

## Bukti persiapan (`results/research_v2/v0.4/`)

| Tahap | Hasil |
|---|---|
| Dry-run budget | per outer run S = 16.384.000, V = 3.150.400, F = 102.400, C = 19.636.800, B = 19.637.248; total P11 **1.570.961.920** keputusan |
| Bukti live P09 (kode v0.4) | 6/6 skenario lulus; 10 runner paralel: 10 JVM bersamaan, konten identik dengan sekuensial, efisiensi throughput **79 %** (speedup 7,9×) |
| Verifikasi P09 / P10 | lulus (12 + 74 tes); lock deep-verify 0 masalah, 0 peringatan |
| Dry run evaluasi | kode evaluasi P11 dijalankan pada split **validation** (studi fixture), menghasilkan laporan lengkap; test tetap tersegel |
| Sumber daya | training 860 keputusan/s per worker; 1 outer run ≈ 24,1 jam (search 5,7 j × 2, baseline 6,3 j × 2); **10 worker ≈ 61 jam (2,55 hari)**; disk ≈ 585 GiB (gzip) dari 991 GiB kosong; evaluasi test ≈ 0,8 jam |

Lock pertama v0.4 (`6ca659d3…`) diganti sebelum ada training atau akses test karena estimasi disknya masih mengasumsikan log mentah;
arsipnya di `protocol_lock/superseded/`.

## Menjalankan

Dari root repo (sebaiknya di terminal Jupyter; proses berjalan terlepas dari tab):

```bash
cd "/workspace/RISET S3 Rozi/IFogsim2-ERWOPPO"
./run_p11_v04.sh go-open-test   # P11 training (~2,5 hari), lalu BUKA TEST, evaluasi, dan analisis terdaftar
./run_p11_v04.sh status         # kemajuan (job selesai, disk) — dari terminal mana pun
./run_p11_v04.sh log            # ikuti log (Ctrl-C hanya berhenti melihat)
./run_p11_v04.sh stop           # berhenti rapi; lanjutkan kapan saja dengan perintah yang sama
```

`go` saja menjalankan training tanpa membuka test; jalankan `go-open-test` kemudian untuk tahap test. Setiap tahap idempoten: setelah
interupsi, crash, restart container, atau culling JupyterHub, jalankan perintah yang sama lagi — job yang complete diverifikasi dan dipakai
ulang, job yang terputus diulang dari awal dengan seed yang sama. Training berhenti otomatis (exit 75) bila disk kosong < 60 GiB.

Hasil akhir: `results/research_v2/v0.4/p11/test_evaluation/report.md` (dan `report.json`); pembukaan test dicatat di
`results/research_v2/TEST_OPENED.json`. Temuan test dicatat dan tidak dipakai untuk menyetel ulang studi ini.
