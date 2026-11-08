# Analisis statistik dan protocol lock (P10)

Kode: `research_v2/analysis/` (`stats.py`, `loader.py`, `report.py`, `lock.py`). Spesifikasi: §16.3 dan §23 dokumen kesepakatan. Modul ini
hanya memakai NumPy: tidak melatih, tidak menjalankan JVM, dan tidak membaca split test.

## Definisi

- **Unit inferensi = outer training run** (20). Per run: z per trace → mean trace per workload → macro-average empat workload
  (bobot 1/4) → `F_j` → `Dglobal = sqrt(sum(F_j^2)/5)`. `Dw` per workload memakai mean z workload tersebut. Task/episode tidak pernah
  dijadikan replikat; p-value tidak pernah dirata-ratakan.
- **Tanda selisih:** `D(pembanding) − D(NSGA-II)`; positif = NSGA-II lebih baik.
- **Tiga uji primer** (satu keluarga Holm, alpha 0,05): RQ1 `equal_F` vs `nsga2`; RQ2 `random` vs `nsga2`; RQ3 `equal_B` vs `nsga2`.
  Uji: sign-flip dua sisi exact, enumerasi 2^20 pada 20 selisih; p = proporsi tanda dengan `|jumlah| ≥ |teramati|` (toleransi
  floating-point 1e-12 relatif). Asumsi: selisih simetris di sekitar nol di bawah H0; pairing saja tidak menjaminnya.
- **60 uji sekunder** (5 biaya × 4 workload × 3 pasangan): sign-flip Monte Carlo 100.000 draw, `p=(b+1)/(M+1)`, seed 20261106
  (satu matriks tanda dipakai bersama seluruh hipotesis), Holm sebagai keluarga tersendiri. Seluruh 60 hasil dilaporkan, berlabel
  *secondary, pre-specified* — bukan konfirmatori.
- **Interval 95%:** 10.000 bootstrap berpasangan crossed (seed 20261105): indeks outer-run dan indeks trace per workload diundi; indeks
  trace yang sama dipakai oleh semua model/run terpilih; agregasi dihitung ulang dari trace hasil undian. Interval persentil.
- **dz berpasangan** = mean/SD selisih (ddof=1). SD nol (toleransi relatif 1e-12) → `undefined`, tidak pernah diganti nol.
- **Perbandingan lain** (manual, heuristik, sensitivitas) → `exploratory_unadjusted`: efek, CI, p mentah; tanpa kontrol multiplisitas dan
  tanpa klaim konfirmatori. Menambah keluarga konfirmatori harus didaftarkan sebelum test dibuka.
- **Data hilang/non-finite/trace tidak berpasangan/outer run tidak lengkap = error**, bukan imputasi atau penghapusan diam-diam.
- **Makna praktis:** energi dinamis (J) = `zE × 50 J × N` per trace (energi idle sama untuk semua metode pada satu trace), selisih
  violation dan reliability dalam poin persentase, dan perbaikan relatif Dglobal ≥ 1% sebagai *konvensi pelaporan*.

## Penggunaan

```bash
# Laporan mini end-to-end (namespace validation, fixture P09; label metode hanyalah placeholder)
venv/bin/python -m research_v2.analysis.report mini --study-dir results/research_v2/<studi mini> --output-dir <baru>

# Protocol lock
venv/bin/python -m research_v2.analysis.lock create --output <lock.json> --fidelity-evidence results/research_v2/P08_fidelity_extension_1 \
    --resource-estimate <json> --deviations <json>
venv/bin/python -m research_v2.analysis.lock verify --lock <lock.json> [--deep]
```

P11 membangun `Table` dengan `loader.rows_to_table` dari baris evaluasi per-episode (skema yang sama dengan `episodes.jsonl` validasi).
Pemuat hanya menerima split `validation`; evaluator test (P11) memakai loader dengan `allowed_splits=('test',)` setelah lock terverifikasi.

## Protocol lock

`protocol_lock.json` membekukan: hash setiap file source/test/schema/config/requirements, JAR dan build receipt, hash config kanonik, versi
dependency dan lingkungan, K terpilih beserta bukti fidelity (dan catatan bahwa gerbang asli gagal), budget S/V/F/B per outer run, seed dan
split, normalisasi, manifest trace validasi dan **hash input** 400 trace test (disiapkan, tanpa hasil), registri hipotesis (3 primer, 60
sekunder, aturan eksploratif dan larangan), aturan sensitivitas, estimasi sumber daya, bukti P09, dan perubahan dari v0.2.

`verify_lock` menghitung ulang semuanya dari disk. File terkunci yang berubah/hilang adalah pelanggaran; file yang **ditambahkan** setelah
lock (mis. evaluator test P11) hanya diberi peringatan dan wajib masuk audit P12. Split test hanya dapat dibuka lewat
`trace_access.unseal_test(lock)` (role `test_evaluator`), yang menolak lock tidak valid; role lain tetap tidak dapat membaca test.
