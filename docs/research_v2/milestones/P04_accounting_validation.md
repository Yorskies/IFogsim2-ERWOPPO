# P04 — Ledger energi dan lima metrik

Status: **complete — verifikasi lokal**.
Tanggal: 8 November 2026. Spesifikasi penelitian v0.2; wire `research-v2.1`.
Git HEAD awal `529ebbc7b7720b2b142f83363403a514153a77c5`; perubahan P04 masih di working tree,
belum commit/push.

## Tujuan dan batas perubahan

Seluruh komponen energi dan biaya evaluasi dapat direkonstruksi dari catatan mentah tanpa mengandalkan reward.
Tidak ada socket/Gym/reward (P05), agregasi lintas trace dan workload (`Dglobal`, P10), atau policy. Source dan
hasil legacy tidak diubah.

## Deliverable

| Deliverable | Lokasi |
|---|---|
| Ledger energi dan metrik per episode (satu-satunya sumber resmi) | `ifogsim/src/org/fog/erwo/v2/MetricsLedger.java` |
| Energi CPU-IT per node dan atribusi per task | `ComputeNode.java` |
| Energi jaringan: detik serialization, bit-hop, idle radio/AP/switch/gateway, energi per hop | `NetworkModel.java` |
| Integral simpangan baku utilisasi fog terhadap waktu | `EngineCoordinator.java` |
| Evaluator Python independen (hanya membaca catatan mentah) | `research_v2/evaluator.py` |
| 16 tes: E01–E04, M01–M03, aturan akuntansi lain, kecocokan evaluator | `tests/research_v2/test_accounting.py` |
| Audit milestone dan laporan mesin | `research_v2/verify_accounting.py`, [P04_verification.json](P04_verification.json) |

## Ledger dan rumus

Energi total = jumlah semua komponen, dihitung sekali. Counter energi bawaan `FogDevice` tidak dibaca.

| Komponen | Idle | Dinamis |
|---|---|---|
| CPU-IT tiap node | `Pidle × H` | `(Pbusy − Pidle) / PE × ∫ PE-sibuk dt`; integral eksak karena jumlah PE sibuk konstan per bagian |
| Radio IoT | `0,1 W × jumlah IoT × H` | `TX 1,3 W × detik upload + RX 0,9 W × detik download` |
| AP | `3 W × jumlah fog × H` | `RX 1,5 W × detik upload + TX 2,0 W × detik download` |
| Switch (LAN) | `20 W × H` | `5 nJ × bit-hop LAN` yang benar-benar terkirim |
| Gateway WAN | `10 W × H` | `20 nJ × bit-hop WAN` yang benar-benar terkirim |

Detik dan bit dihitung dari serialization yang berlangsung, termasuk bagian parsial pesan yang dibatalkan timeout,
dan tidak ada daya dinamis saat antre maupun propagasi. Daya idle default: CPU 568,4333 W + komunikasi 55 W =
623,4333 W; selama 69 s menjadi 43.016,8977 J.

**Lima biaya (per trace, tanpa clipping):**
`zL = (Σ latensi selesai + Nfailed × 9 s) / (N × 9 s)`; `zE = Edinamis / (50 J × N)`; `zD = (Nlate + Nfailed)/N`;
`zQ = Nfailed/N`; `zB = ∫ std_populasi(u_F1..F5) dt / (H × √0,24)`; `D = √((zL² + zE² + zD² + zB² + zQ²) / 5)`.
Penalti 9 s pada tugas gagal adalah konvensi evaluasi dan dilabeli demikian; latensi fisik hanya dihitung untuk
tugas yang selesai, dilaporkan sebagai mean, median, dan p95 (nearest-rank, elemen `ceil(p·n)`; median merata-ratakan
dua nilai tengah untuk n genap). Jika tidak ada tugas selesai, statistik latensi dan J per keberhasilan adalah `null`
dengan jumlah yang jelas. Throughput dipisah antara 0–T dan T–H.

## Keputusan desain

1. **Java menghitung, Python memverifikasi.** Java harus menghitung ledger karena P05 membutuhkan delta biaya untuk
   reward tertunda. `evaluator.py` menghitung ulang dari interval CPU per task, log hop jaringan, spesifikasi node,
   dan config, tanpa membaca angka energi atau biaya dari Java.
2. **Integral CPU eksak.** Persamaan linear terhadap utilisasi dan jumlah PE sibuk konstan antar-event membuat
   `∫ P(u) dt` sama dengan `Pidle × H + (Pbusy − Pidle)/PE × ∫ PE-sibuk dt`. Integral ditutup tepat di H.
3. **`zB` tidak dapat diturunkan dari busy PE-seconds** (std bersifat nonlinear), sehingga koordinator
   mengintegrasikannya pada setiap event sebelum state berubah. Evaluator mengintegrasikannya sendiri dengan sweep
   atas titik perubahan interval CPU.
4. **Komunikasi hanya dihitung pada mode jaringan.** Mode fixture P02 tidak memodelkan jaringan, jadi grup energinya
   hanya CPU dan `communication_modeled=false`. Idle radio dihitung per node `IoT-*` pada daftar node.
5. **Fog yang dihitung dalam `zB` adalah node `F<angka>` yang ada.** `fog_count` dilaporkan; bila tidak ada fog,
   `zB` dan `D` bernilai `null`, bukan nol.
6. **Nilai biaya di luar [0, 1] ditandai (`out_of_reference`, `diagnosis_required`) dan tidak dipotong.** Penghentian
   studi karena tanda ini adalah tanggung jawab runner pilot/kalibrasi (P06).
7. **Energi tugas gagal tetap dihitung**: CPU sampai dibatalkan dan byte yang sempat dikirim. Energi dinamis
   diatribusikan ke task (`cpu_dynamic_j`, `comm_dynamic_j`) dan selisihnya dengan total (`attribution_gap_j`)
   harus nol; energi idle tidak diatribusikan.
8. **Skala acuan dari config tervalidasi**; tidak ada min/max dari data yang sedang dinilai.

## Verifikasi dan hasil aktual

```powershell
$jdk = "$env:USERPROFILE\.jdks\jdk-21.0.13.0.2+1"
venv\Scripts\python.exe ifogsim\build_v2.py --jdk-home $jdk --self-test
venv\Scripts\python.exe -m research_v2.verify_accounting --jdk-home $jdk
```

**16 tes lulus; 0 failure, 0 error, 0 skip.** Regresi pada build yang sama: P00 23/23, P01 49/49, P02 21/21, P03 17/17.

- **E01**: sistem idle selama 69 s: 623,4333 W, 43.016,8977 J, energi dinamis 0, `zE = 0`.
- **E02**: tugas lokal 100 MI pada 500 MIPS menambah tepat `(2,5 − 0,5) × 0,2 = 0,4 J`; idle tidak bertambah.
- **E03**: upload 1 MiB menambah `(1,3 + 1,5) × 0,4194304 = 1,17440512 J`; pengembalian hasil
  `(2,0 + 0,9) × 0,0209716 s`; hop kabel `5 nJ` (LAN) dan `20 nJ` (WAN) per bit-hop; idle tidak ditambah ulang.
- **E04**: utilisasi fog `[1,1,0,0,0]` konstan selama 69 s memberi integral `69 × √0,24` dan `zB = 1`.
- **M01**: N=10 (6/2/2) memberi violation 0,4, reliability 0,8, `zD` 0,4, `zQ` 0,2.
- **M02**: `zL = (0,2 + 9)/18 = 0,5111`, `zE = 1/(50·2) = 0,01`, latensi fisik rata-rata 0,2 s.
- **M03**: semua gagal menghasilkan statistik latensi dan J per keberhasilan `null`; N=0 ditolak.
- **Lain-lain**: aturan persentil, throughput di dalam dan setelah jendela kedatangan, energi parsial tugas yang
  dibatalkan (1,2 J untuk 0,6 s), total sama dengan jumlah komponen, atribusi menutup, dan tanda di luar acuan
  (`zE ≈ 4` tidak dipotong).
- **Evaluator independen**: pada trace kalibrasi nyata (light, moderate, heavy, dynamic) × {jaringan + `nearest_fog`,
  jaringan + `cloud`, fixture + `nearest_fog`}, seluruh angka ledger, metrik, lima biaya, `D`, dan energi per task
  cocok dengan perhitungan ulang hingga toleransi relatif 1e-9. Tanpa log hop, agregat link juga cocok.

### Pemeriksaan efektivitas tes (mutation)

Delapan bug akuntansi disuntikkan satu per satu, lalu dikembalikan (source diverifikasi identik) dan JAR dibangun ulang:

| Mutan | Hasil |
|---|---|
| Energi CPU tidak dibagi jumlah PE | Dibunuh (20 entri gagal) |
| `zE` memakai energi total, bukan dinamis | Dibunuh (26) |
| `zB` memakai std sampel (n−1) | Dibunuh (12), termasuk E04 |
| Penalti latensi tugas gagal dihapus | Dibunuh (19), termasuk M02 dan M03 |
| Idle radio dihitung dua kali | Dibunuh (14), termasuk E03b |
| Tugas yang dibatalkan ditagih sebagai berjalan penuh | Dibunuh (14), termasuk tes tugas dibatalkan dan E04 |
| Latensi tugas gagal dihitung nol | Dibunuh (14), termasuk M02 |
| Energi upload tanpa sisi penerima | Dibunuh (11), termasuk E03 |

### Karakterisasi pada trace kalibrasi 0 (bukan benchmark metode)

Satu trace per workload, topologi heterogen, transport jaringan, tindakan tetap. `Eidle` sama untuk semuanya
(43,017 kJ); tidak ada biaya di luar [0, 1].

| Tindakan | Workload | N | zL | zE | zD | zB | zQ | D | Edinamis (J) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| nearest_fog | light | 328 | 0,147 | 0,137 | 0,363 | 0,512 | 0,061 | 0,296 | 2.241 |
| nearest_fog | moderate | 887 | 0,454 | 0,134 | 0,747 | 0,619 | 0,353 | 0,508 | 5.953 |
| nearest_fog | heavy | 1.812 | 0,909 | 0,094 | 0,992 | 0,321 | 0,848 | 0,727 | 8.489 |
| nearest_fog | dynamic | 935 | 0,734 | 0,111 | 0,875 | 0,499 | 0,658 | 0,632 | 5.186 |
| cloud | light | 328 | 0,090 | 0,039 | 0,180 | 0,000 | 0,030 | 0,093 | 647 |
| cloud | moderate | 887 | 0,524 | 0,040 | 0,855 | 0,000 | 0,421 | 0,486 | 1.750 |
| cloud | heavy | 1.812 | 0,960 | 0,024 | 0,994 | 0,000 | 0,911 | 0,740 | 2.165 |
| cloud | dynamic | 935 | 0,782 | 0,031 | 0,907 | 0,000 | 0,711 | 0,623 | 1.447 |

Pengamatan yang terverifikasi: energi idle (43 kJ) jauh melebihi energi dinamis (≤ 8,5 kJ) pada semua baris,
dan `zE` hanya memakai bagian dinamis sesuai spesifikasi. `zB = 0` untuk `cloud` karena fog tidak pernah terpakai.
Penyebab selisih antar-tindakan tidak dianalisis di sini.

## Risiko dan keterbatasan tersisa

- Hanya biaya per trace dan `D` per trace. Agregasi lintas trace dan empat workload (`Dglobal`, `Dw`, F) adalah P10.
- Parameter energi adalah asumsi sintetis; angka ini adalah energi IT sistem yang dimodelkan, bukan listrik fasilitas.
- Evaluator memakai config yang sama dengan engine: kode dan masukan mentahnya independen, spesifikasinya tidak.
- Tidak ada daya dinamis saat antre/propagasi, retransmisi, DVFS, atau tidur node (sesuai §11 dan §15).
- Mode fixture tidak memodelkan energi komunikasi.
- Pemeriksaan antar-metode `zE` hanya bermakna pada trace dan topologi yang identik.
- Verifikasi hanya di Windows, Python 3.12.6, Microsoft OpenJDK 21.0.13. Ubuntu belum diuji.
- Fingerprint source pada `P02_verification.json` dan `P03_verification.json` bersifat historis (koordinator dan
  node berubah di P04); regresi P02 dan P03 pada build P04 lulus.

## Keputusan dan phase berikutnya

- [x] Tujuan, batas, dan keputusan desain dicatat.
- [x] Acceptance E01–E04 dan M01–M03 dijalankan dengan hasil tersimpan.
- [x] Evaluator independen sepakat dengan ledger Java pada trace nyata.
- [x] Efektivitas tes diperiksa dengan bug yang disuntikkan.
- [x] Regresi P00–P03 lulus; legacy dan trace P01 tidak diubah.
- [x] Keterbatasan dinyatakan.

**Lanjut ke P05 — socket v2, Gymnasium, observasi, dan reward:** protokol JSON Lines berversi, `reset`/`step` dengan
satu aksi per kedatangan dan drain sampai H, observasi 108 fitur dari snapshot publik, serta reward tertunda
`−100 × Σ w · Δbiaya` dari outcome aktual. Biaya kumulatif di ledger ini adalah dasarnya; P05 perlu menyediakan
biaya kumulatif pada setiap keputusan, bukan hanya pada akhir episode.
