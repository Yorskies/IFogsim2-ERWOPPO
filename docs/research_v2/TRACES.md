# P01 — trace eksternal dan reproduksibilitas

Generator tidak menjalankan policy atau simulator. Inputnya config dan
`TraceKey(master, split, outer_run, model_repeat, trace_id, workload)`.
Nama metode, aksi, bobot reward kandidat, dan outcome tidak menjadi input RNG.
Config disalin sebagai bytes saat generator dibuat agar perubahan object milik
pemanggil tidak mengubah generator yang sedang digunakan.

## Algoritma dan satuan

Untuk setiap komponen `arrival/source/class/cpu_mi/input_bytes/deadline`, seed:

```text
text = master|split|outer_or_-|repeat_or_-|trace_id|workload|component
seed = uint64_little_endian(SHA256(UTF8(text))[0:8])
rng = numpy.random.Generator(numpy.random.PCG64(seed))
```

Contoh tetap: `20261103|calibration|-|-|0|light|arrival` menghasilkan
`10715774301338505746`. Generator tidak memakai `numpy.random` global. Versi
NumPy teruji dipin di `requirements-v2-traces.txt`; trace ekspor adalah sumber
kebenaran dan Java tidak menggambar ulang atribut.

Arrival dihasilkan dari penjumlahan Exp(1) pada ruang cumulative hazard dan
diinversikan melalui integral laju piecewise-constant. Residual hazard melewati
batas fase, tanpa menggambar ulang exponential atau menambahkan tugas di batas.
Arrival window `[0,T)`; tugas pertama tidak dipaksa pada t0. Task count nol
ditolak dengan error, tanpa seed ulang atau task tambahan.

Kelas mengikuti probabilitas .50/.35/.15. MI uniform integer **termasuk** kedua
batas; input uniform kontinu MiB, dikonversi `ceil(value*2^20)` byte; output
`ceil(.05*input_bytes)`. Deadline uniform kontinu detik dan timeout=k*deadline.
Working set64MiB ditambah buffer pada admission di P02. Source uniform integer
0..99; `source//20+1` memberi fog akses1..5. ID bertambah mulai0 per trace.

Timestamp tetap binary64, diekspor melalui JSON round-trip tanpa pembulatan
display. Probe Java tambahan memeriksa bit arrival/deadline/timeout dan hasil
penjumlahan waktu absolut. P01 belum menjadwalkan event task; semantik completion
tepat deadline/timeout masih harus dibuktikan P02.

## Split dan role

| Split | Role | Namespace/ID | Akses pada P01 |
|---|---|---|---|
| calibration | calibrator | trace0..19; outer/repeat=null | Generate, read, describe |
| pilot_train | pilot_trainer | outer100/101/102, repeat0..1; trace counter mulai0 | Generate, read, describe |
| pilot_validation | pilot_validator | trace10000..10004; outer/repeat=null | Generate, read, describe |
| train_candidate | candidate_trainer | outer0..19, repeat0..1; trace counter mulai0 | Generate, read, describe |
| validation | search_validator | trace10000..10004; outer/repeat=null | Generate, read, describe |
| train_final | final_trainer | outer0..19, repeat0; trace counter mulai0 | Generate, read, describe |
| test | holdout_preparer | trace20000..20099; outer/repeat=null | Generate sebagai sealed; read/describe ditolak |

Final memakai repeat0 sebagai representasi eksplisit field model repeat untuk
training. Tidak ada method ID dalam key, sehingga model dengan peran/run/repeat
yang sama menerima task stream sama. Pilot validation terpisah melalui string
split walaupun ID numeriknya sama dengan validation utama. Counter trace
training tidak dibatasi jumlah episode; runner P09 wajib mempertahankan urutan.

Role yang salah ditolak saat generate, read, dan describe. P01 belum menyediakan
role final evaluator atau flag pembuka test; implementasinya harus bergantung
protocol freeze P10. Ini guard aplikasi untuk mencegah kebocoran tidak sengaja,
**bukan** enkripsi atau pembatasan OS terhadap pengguna yang mengedit source.
Unit test boleh membuat trace test sementara untuk membuktikan seal; tidak
menggunakannya untuk membandingkan metode atau memilih parameter.

## Bundle immutable

Bundle berada di:

```text
<root>/<full_config_sha256>/<split>/outer-<r_or_->/repeat-<m_or_->/<workload>/trace-<id>/
  trace.json
  config.json
  manifest.json
```

- Trace memakai schema P00 yang tetap; field unit/config lengkap disimpan dalam
  config dan sidecar, sehingga tidak menggandakan wire contract.
- Payload SHA-256 adalah canonical envelope tanpa field `payload_sha256` sendiri.
  Config hash memakai canonical seluruh config. File hash sidecar memakai byte
  file aktual, termasuk field payload hash pada trace.
- Sidecar memakai `trace_bundle.schema.json`, mencatat seed tiap komponen,
  producer Python/NumPy/source hash, unit, task count, serta status ready/sealed.
- Publish dilakukan melalui staging directory lalu rename setelah file selesai
  di-flush. Konsumen tidak melihat bundle setengah selesai. Penulisan identik
  idempotent; isi yang berbeda/korup tidak ditimpa. `Trace.to_dict()` memberi
  salinan, sedangkan penyimpanan internal berupa bytes immutable.
- Hash mendeteksi perubahan; file tidak dibuat read-only oleh OS. Mengganti
  semua hash secara manual bukan operasi valid dalam protokol penelitian.
- Config hash meliputi parameter penelitian lengkap. Mengubah metadata reward
  dapat mengubah identitas config/trace, tetapi **tidak** atribut tugas jika
  physical config dan namespace sama. Bobot per kandidat tidak ditulis sebagai
  perubahan config generator; satu protokol config dipakai bersama semua metode.

Contoh dari root repository, dengan virtual environment aktif:

```text
python -m pip install -r requirements-v2-traces.txt
python -m research_v2 generate-traces --split calibration --role calibrator --trace-id 0
```

Perintah tersebut menulis empat workload sekaligus ke
`results/research_v2/traces/`. Ini belum menjalankan empat training. Untuk ringkas
satu bundle gunakan `python -m research_v2 describe-trace <bundle_path> --role calibrator`.
Hasil berisi task count, min/mean/median/max atribut, proporsi kelas, sumber,
distribusi fog akses, dan jumlah arrival per interval15s.

## Kriteria distribusi yang ditetapkan sebelum pemeriksaan

Laporan milestone menggunakan seluruh20 trace calibration per workload,
bukan memilih seed yang lolos. Tidak memakai split validation/test untuk
menyetel laju atau distribusi.

Ada468 pemeriksaan dengan family error budget .001, memakai union bound:
4 workload × (1 total count +4 interval count +3 class count +9 conditional
attribute mean +100 source count). Ini pemeriksaan distribusi generator,
bukan uji signifikansi manfaat ERWO.

Untuk count, batas deviasi konservatif:
`sqrt(2*variance*log(2M/alpha)) + 2*log(2M/alpha)/3`. Poisson memakai variance
expected count, binomial kelas/source memakai `n*p*(1-p)` bersyarat pada n.
Mean uniform terbatas memakai Hoeffding:
`(high-low)*sqrt(log(2M/alpha)/(2*n))`; input diberi allowance1 byte untuk ceil.
Semua task tetap harus memenuhi batas keras schema/kontrak. Gate gagal berhenti
untuk diagnosis, tanpa sampling ulang sampai hasil terlihat sesuai.

Moderate/dynamic juga dibandingkan berdasarkan atribut tugas, bukan hanya hash
envelope yang memang memuat label workload berbeda. Profil waktu dynamic harus
menunjukkan laju5/15/35/5 pada interval yang ditetapkan. Jumlah expected keduanya
900 bukan berarti actual count setiap pasangan trace harus identik.

Fixture handwritten di `tests/research_v2/fixtures/` sengaja mempunyai arrival
bersamaan dan tepat batas fase. Sidecar expected memberi label **hypothetical**
outcome deadline/timeout untuk P02. Fixture tidak diekspor ke namespace bundle
random biasa dan tidak dimasukkan laporan distribusi calibration.

Jalankan audit lengkap setelah build JAR:

```text
python ifogsim/build_v2.py --self-test
python -m research_v2.verify_traces
```

JAVA_HOME harus menunjuk JDK yang tersedia. Untuk mesin pengembangan ini dapat
menambahkan `--jdk-home "C:/Program Files/Java/jdk-27"` ke kedua perintah.
Verifier menolak audit selesai yang melewati tes Java. Bukti distribusi dan tes
tersimpan di `docs/research_v2/milestones/P01_verification.json`; calibration
bundle calibration disimpan di `results/research_v2/P01_calibration/traces/`
(default `verify_traces --trace-root`; CLI `generate-traces` memakai
`results/research_v2/traces/`). Sejak `667eb42` direktori `results/` tidak lagi
di-ignore Git dan bundle calibration tersebut ikut ter-commit.
