# P05 — Socket v2, Gymnasium, observasi, dan reward

Status: **complete — verifikasi lokal**.
Tanggal: 8 November 2026. Spesifikasi penelitian v0.2; wire `research-v2.1`.
Git HEAD awal `c67682200eae5f67fa96777c545b164d00dee318`; perubahan P05 masih di working tree,
belum commit/push.

## Tujuan dan batas perubahan

Kontrak Java–Python untuk hasil tertunda dan horizon fisik: satu aksi per kedatangan, observasi publik 108 fitur,
dan reward dari kejadian aktual di antara dua keputusan. Tidak ada PPO, pencarian bobot, atau kalibrasi (P06–P08).
Semua pengujian memakai aksi tetap atau acak agar kesalahan simulator tidak tersamar oleh pembelajaran.
Source dan hasil legacy tidak diubah.

## Deliverable

| Deliverable | Lokasi |
|---|---|
| Server socket JSON Lines pada loopback, handshake, idempotensi, timeout, heartbeat | `ifogsim/src/org/fog/erwo/v2/V2SocketServer.java` |
| 108 fitur (mentah dan tertransformasi) dalam urutan kontrak | `ObservationBuilder.java` |
| Biaya kumulatif `[CL,CE,CD,CB,CQ]` pada waktu mana pun, beban node saat ini, hook keputusan | `EngineCoordinator.java` |
| Energi dinamis kumulatif stateless dan estimasi rute dari antrean saat ini | `NetworkModel.java`, `ComputeNode.java` |
| Satu jalur pembangunan episode untuk driver headless dan server | `EngineMain.java` |
| Perluasan aditif kontrak: operasi `hello`, field `trace`/`options` pada reset, definisi `rpc_response` | `research_v2/schema_definitions.py`, `contracts.py`, `schemas/research_v2/contracts.schema.json` |
| Klien, manajemen proses server, verifikasi handshake | `research_v2/rpc_client.py` |
| Environment Gymnasium, penolakan konfigurasi legacy | `research_v2/gym_env.py` |
| 28 tes | `tests/research_v2/test_gym.py` |
| Audit milestone | `research_v2/verify_gym.py`, [P05_verification.json](P05_verification.json) |
| Pin dependency environment | `requirements-v2-gym.txt` |

## Protokol

UTF-8 JSON Lines, satu objek per baris, maksimum 16 MiB per frame, hanya pada `127.0.0.1`, port sesuai
`execution.allowed_ports`. Satu JVM melayani satu klien dan satu simulasi (state statis CloudSim).

| Operasi | Fungsi |
|---|---|
| `hello` | Handshake identitas: `jar_sha256`, `config_file_sha256`, `wire_contract_file_sha256`, hash config terikat, dimensi 108, tujuh aksi |
| `reset` | Membawa trace lengkap dan opsi; mengembalikan observasi kedatangan pertama |
| `step` | Satu aksi (0–6) untuk tugas yang menunggu; jawabannya adalah observasi keputusan **berikutnya** |
| `heartbeat` | Menjaga timer RPC server tetap hidup |
| `close` | Mengakhiri sesi |

Episode berjalan di dalam `CloudSim.startSimulation()`; `decide` dipanggil pada setiap kedatangan dan memblokir pada
soket, jadi jam simulasi berhenti selama Python menunggu. Setelah kedatangan terakhir, simulasi berjalan sampai H tanpa
aksi palsu, dan respons terminal (`terminated=true`, `truncated=false`) membawa seluruh sisa biaya.

## Observasi 108 fitur

Setiap fitur dihitung dengan nama, lalu disusun menurut `observation_features` pada kontrak (tidak ada urutan yang
disalin manual). Dua representasi dikembalikan: vektor tertransformasi (untuk PPO) dan snapshot mentah (untuk heuristik
dan audit, dengan `null` sebagai nilai mentah sentinel node kosong).

- **Node (7 × 9)**: fraksi PE sibuk, `q/Qwait`, waktu sampai PE pertama bebas, MI antre / MIPS node, MIPS/PE, jumlah
  PE, Joule/MI CPU, sisa MI total / MIPS node, sisa deadline minimum. Blok pertama adalah IoT asal tugas.
- **Rute (7 × 4)**: estimasi delay input dan hasil (serialization tugas, propagasi, dan byte residual + antre pada
  setiap server jalur saat ini), bandwidth bottleneck, estimasi energi komunikasi. Jalur lokal bernilai nol.
- **Tugas (8), sumber (5), global (4)**: termasuk EMA laju kedatangan yang kausal
  (`ema = ema_sebelumnya × exp(−Δt/5) + 1/5`) dan `t/T`.

Observasi tidak memuat label workload, seed, bobot reward, jumlah tugas, ID perangkat mentah, atau kedatangan masa depan.
Selang sejak keputusan sebelumnya pada keputusan pertama dihitung dari `t = 0`.

## Reward

Java melaporkan biaya kumulatif; Python menghitung `r = −100 × Σ wⱼ ΔCⱼ`. Kumulatif bertambah pada kejadian nyata:
`CL` saat hasil diterima atau tugas gagal (penalti berlabel), `CD` saat deadline pertama kali terlewati atau saat gagal
bila belum terhitung (maksimum sekali), `CQ` saat gagal. `CE` dan `CB` kontinu terhadap waktu: energi dinamis
dihitung stateless sampai waktu keputusan (termasuk bagian pesan yang sedang diserialisasi) dan integral std
utilisasi fog diintegrasikan pada setiap event. Pada H vektor ini sama dengan lima biaya `z` bagian 16.

## Keputusan desain

1. **Hanya Python yang tahu bobot.** Java tidak menerima bobot, jadi konfigurasi empat bobot dapat ditolak di
   `validate_weights` sebelum server tersentuh. Model 46 fitur ditolak oleh `check_policy_interface`, dan request dengan
   `schema_version` lain ditolak server (`UNSUPPORTED_SCHEMA`).
2. **Hash.** Java tidak menghitung ulang hash kanonik config/trace (representasi float Python dan Java berbeda). Server
   diikat pada `--config-sha256` saat start, memeriksa bahwa `trace_sha256` permintaan sama dengan `payload_sha256` yang
   dideklarasikan trace, dan bahwa setiap `step` membawa identitas episode yang sama. Klien memverifikasi hash JAR dan
   file config terhadap build receipt dan file di repo.
3. **Kegagalan bersifat keras.** Pelanggaran invariant engine menghasilkan `ENGINE_ERROR` tanpa hasil parsial dan tanpa
   mesin pengganti. Koneksi putus, timeout, atau server mati membuat klien melempar `ConnectionLostError`; environment
   tetap rusak sampai dibuat ulang dan tidak pernah melaporkan `terminated`.
4. **Idempoten.** Permintaan ulang dengan `request_id` yang sama menerima byte jawaban yang sama dan tidak diterapkan dua kali.
5. **Skema aditif.** `hello`, `trace`, `options`, dan `rpc_response` ditambahkan tanpa mengubah field `rpc_request`
   yang sudah ada; tes P00 tetap valid. Versi wire tetap `research-v2.1` karena belum ada konsumen luar.
6. **Observasi terminal adalah placeholder nol** dengan `observation_valid=false`, karena Gymnasium mensyaratkan observasi
   dan nilai sebenarnya tidak ada.

## Verifikasi dan hasil aktual

```powershell
$jdk = "$env:USERPROFILE\.jdks\jdk-21.0.13.0.2+1"
venv\Scripts\python.exe ifogsim\build_v2.py --jdk-home $jdk --self-test
venv\Scripts\python.exe -m research_v2.verify_gym --jdk-home $jdk
```

**28 tes lulus; 0 failure, 0 error, 0 skip.** Regresi pada build yang sama: P00 23/23, P01 49/49, P02 21/21,
P03 17/17, P04 16/16.

- **Pemeriksa resmi Gymnasium** (`check_env`) lulus dengan peringatan dijadikan error.
- **Satu langkah per kedatangan**; episode berakhir pada H dengan `terminated=true, truncated=false`.
- **Semua 108 fitur** dihitung ulang dari spesifikasi pada sistem idle untuk dua tugas berbeda, ditambah node yang
  terbebani (dua PE sibuk, satu tugas antre) dan backlog link yang sedang berjalan, semuanya dengan aritmetika tangan.
- **Identitas return**: untuk empat workload dan empat vektor bobot (equal, manual, miring, dan dasar 0,02),
  `Σ r = −100 · w·z` hingga 1e-9; biaya kumulatif akhir sama dengan `z`; pada satu run penuh per workload, evaluator
  independen P04 sepakat dengan catatan mentah episode itu.
- **Biaya per jenis hasil**: tugas ditolak saat tiba, tepat waktu, terlambat, dan timeout masing-masing menaikkan
  `CD` dan `CQ` tepat sekali (`zD = 3/4`, `zQ = 2/4`).
- **Tertunda dan kausal**: biaya latensi muncul pada keputusan setelah hasil diterima; sisa drain berada pada transisi
  terakhir; mengubah isi tugas yang belum datang tidak mengubah satu pun observasi atau biaya sebelumnya.
- **Ekuivalen**: episode lewat soket identik (tugas, node, link, transfer, energi, metrik) dengan run headless yang
  memakai aksi yang sama.
- **Isolasi dan determinisme**: dua episode berurutan, episode yang ditinggalkan di tengah, dan dua server terpisah
  menghasilkan transkrip identik.
- **Protokol**: JSON rusak, schema legacy, hash tidak cocok, aksi tidak valid, `step` tanpa episode, retry idempoten,
  `reset` di tengah episode, klien hilang tanpa `close`, server dibunuh, timeout RPC, dan heartbeat.

### Pemeriksaan efektivitas tes (mutation)

Dua belas bug disuntikkan satu per satu, lalu dikembalikan (source diverifikasi identik) dan JAR dibangun ulang:

| Mutan | Hasil |
|---|---|
| Biaya deadline dihitung dua kali saat gagal | **Selamat pada percobaan pertama**; tes baru "setiap jenis hasil menaikkan biaya sekali" menutupnya dan kini membunuhnya |
| Energi transfer yang sedang berjalan diabaikan | Dibunuh |
| EMA kedatangan tanpa peluruhan | Dibunuh |
| Estimasi rute mengabaikan backlog | Dibunuh |
| Sentinel node kosong bernilai 0 | Dibunuh |
| Drain setelah kedatangan terakhir dibuang dari transisi akhir | Dibunuh |
| Retry diterapkan ulang | Dibunuh |
| `reset` di tengah episode ditolak | Dibunuh |
| Penyebut `queue_fraction` memakai jumlah PE | Dibunuh |
| PE bebas pertama memakai `max` | Dibunuh |
| Reward mengabaikan bobot | Dibunuh |
| Biaya latensi tidak dihitung saat hasil diterima | Dibunuh |

Mutan yang selamat menunjukkan celah nyata: cabang "gagal sebelum deadline" tidak pernah terjadi pada trace kalibrasi dengan
aksi acak. Sebelum itu saya juga menemukan sendiri bahwa fitur beban node hanya diuji pada sistem idle (semuanya nol atau
sentinel); tes dengan node terbebani ditambahkan sebelum menjalankan mutasi.

### Throughput

Pada trace heavy (1.812 keputusan, aksi acak, loopback): sekitar 1.100 langkah/detik tanpa validasi schema (0,91 ms
per langkah) dan sekitar 600 langkah/detik dengan validasi (1,67 ms). Ini patokan awal untuk anggaran P09, bukan klaim
kinerja training.

## Risiko dan keterbatasan tersisa

- Observasi adalah snapshot agregat, bukan state Markov lengkap; transfer yang sedang berjalan dan deadline antrean
  hanya diringkas. Kebijakan MLP feed-forward adalah asumsi yang harus disebut dalam laporan.
- Estimasi rute memakai antrean saat ini, bukan hasil; outcome selalu dari engine.
- Hash kanonik tidak dihitung ulang di Java (keputusan 2). Perlindungan terhadap config/trace yang salah mengandalkan
  pengikatan hash saat start, kesamaan hash trace dengan deklarasinya, dan verifikasi JAR di sisi klien.
- Satu klien per server; dukungan beberapa worker memerlukan JVM dan port terpisah (P09).
- Koneksi yang putus kehilangan episode; tidak ada resume parsial.
- Hanya aksi tetap atau acak; tidak ada klaim pembelajaran.
- Verifikasi hanya di Windows, Python 3.12.6, Microsoft OpenJDK 21.0.13. Ubuntu belum diuji. State statis
  `FogDevice`/`TimeKeeper`/`NetworkUsageMonitor` masih belum diinstansiasi.
- Fingerprint source di `P02`–`P04_verification.json` bersifat historis; regresi pada build P05 lulus.

## Keputusan dan phase berikutnya

- [x] Tujuan, batas, dan keputusan desain dicatat.
- [x] Kriteria lulus P05 dijalankan dengan hasil tersimpan, termasuk `check_env`.
- [x] Identitas reward diuji lintas workload dan bobot, dan sepakat dengan evaluator independen.
- [x] Efektivitas tes diperiksa dengan bug yang disuntikkan; satu celah ditemukan dan ditutup.
- [x] Regresi P00–P04 lulus; legacy dan trace P01 tidak diubah.
- [x] Keterbatasan dinyatakan.

**Lanjut ke P06 — baseline deterministik dan kalibrasi fisik:** always-local, nearest-fog, Least Fog dan Greedy-EFT dari
snapshot publik yang sama, 20 trace kalibrasi per workload pada konfigurasi homogen dan heterogen, gerbang kelayakan
solo-task, dan laporan kalibrasi. Temuan P03 bahwa CPU saja sudah melebihi deadline untuk sebagian tugas di fog akses
adalah masukan langsung untuk gerbang itu.
