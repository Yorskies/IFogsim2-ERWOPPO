# P03 — Transport jaringan dan jalur offloading

Status: **complete — verifikasi lokal**.
Tanggal: 8 November 2026. Spesifikasi penelitian v0.2; wire `research-v2.1`.
Git HEAD awal `2df855dcf98368d99170bc127cf1341c7171d9fc`; perubahan P03 masih di working tree,
belum commit/push.

## Tujuan dan batas perubahan

Mengganti transport fixture nol-jaringan P02 dengan transport store-and-forward: keputusan tujuan
menimbulkan serialization, propagasi, antrean, dan kontensi pada link yang dapat ditelusuri. Tidak
ada ledger energi (P04), socket/Gym (P05), atau policy. Mode fixture P02 tetap ada dan tidak berubah.
Source dan hasil legacy tidak diubah.

## Deliverable

| Deliverable | Lokasi |
|---|---|
| Server link, antrean FCFS terbatas, rute, serialization terpisah dari propagasi, pembatalan parsial | `ifogsim/src/org/fog/erwo/v2/NetworkModel.java` |
| Integrasi ke koordinator: event `SERIALIZATION_DONE` dan `HOP_ARRIVED`, jalur input/hasil, `NETWORK_QUEUE_FULL`, pembatalan saat timeout, pemeriksaan idle di horizon | `EngineCoordinator.java` |
| Mode `network` pada skenario (override per jenis link untuk kasus kecil) | `EngineMain.java` |
| 17 tes: N01–N06 dan jalur kegagalan | `tests/research_v2/test_network.py` |
| Audit milestone dan laporan mesin | `research_v2/verify_network.py`, [P03_verification.json](P03_verification.json) |

## Model

| Segmen | Server | Kapasitas | Propagasi | Antrean menunggu |
|---|---|---:|---:|---:|
| IoT–AP/fog akses (5 kanal) | satu server per kanal, dua arah berbagi (half-duplex) | 20 Mbps | 2 ms | 64 |
| Fog–switch (5 link) | satu server per arah (full-duplex) | 1 Gbps | 0,5 ms | 64 per arah |
| Switch–cloud | satu server per arah | 50 Mbps | 20 ms | 64 per arah |

- Serialization = `8 × byte / bit_per_s`. Server dilepas saat serialization selesai; propagasi tidak menahan server.
- Antrean menghitung pesan menunggu, tidak termasuk yang sedang dilayani. Antrean penuh menghasilkan
  `NETWORK_QUEUE_FULL` (kegagalan layanan, tanpa rerouting dan tanpa retransmisi).
- Rute input: fog akses `[akses↑]`; fog lain `[akses↑, LAN asal↑, LAN tujuan↓]`; cloud `[akses↑, LAN asal↑, WAN↑]`.
  Hasil memakai jalur balik. Tugas yang targetnya IoT asal tidak menyentuh link.
- Tugas masuk admission CPU setelah input diterima penuh di node; tidak ada reservasi CPU saat aksi.
  Transfer time tidak ditambahkan ke panjang Cloudlet (cloudletSubmit native tetap dinonaktifkan).
- Timeout: pesan yang sedang diserialisasi telah mengirim `elapsed × laju / 8` byte dan server dilepas saat itu
  juga; pesan yang menunggu mengirim 0 byte; pesan yang sedang berpropagasi sudah dihitung penuh. Event lama
  menjadi usang lewat generasi task dan tidak menggandakan completion.
- Pencatatan: per server dan per arah `bytes_sent`, `busy_s` (detik serialization), jumlah mulai/selesai/batal/ditolak,
  dan antrean maksimum; log per hop opsional (`log_transfers`). Ini prasyarat ledger energi P04, bukan ledger.

## Keputusan desain

1. **Link adalah server di antrean event yang sama dengan P02**, bukan entity `NetworkTopology` CloudSim. Urutan waktu
   sama dan penanganan event usang tetap di satu tempat. Dua jenis event baru berbagi prioritas `TRANSFER_COMPLETE`
   (0), jadi selesai-transfer mendahului deadline/timeout dan arrival pada waktu sama.
2. **Buffer hasil tidak ditahan di RAM node** setelah CPU selesai (keputusan terbuka P02 no. 5). Batas jaringan
   untuk hasil adalah antrean link 64 pesan; hasil yang ditolak berstatus `NETWORK_QUEUE_FULL` dengan
   `cpu_finish_s` tetap tercatat, sehingga kerja CPU-nya terhitung.
3. **Kanal akses wajib half-duplex dan LAN/WAN full-duplex**; override `duplex` ditolak.
4. **Mode jaringan hanya merutekan node `F1..F5` dan `cloud`**; nama node lain ditolak. `access_fog` pada task harus
   sama dengan `source_iot // 20 + 1`.
5. **Mode `network` dan `fixture_transport` saling eksklusif.**

## Verifikasi dan hasil aktual

```powershell
$jdk = "$env:USERPROFILE\.jdks\jdk-21.0.13.0.2+1"
venv\Scripts\python.exe ifogsim\build_v2.py --jdk-home $jdk --self-test
venv\Scripts\python.exe -m research_v2.verify_network --jdk-home $jdk
```

**17 tes lulus; 0 failure, 0 error, 0 skip.** Regresi pada build yang sama: P00 23/23, P01 49/49, P02 21/21.

- **N01/N04**: 1 MiB pada 20 Mbps = serialization 0,4194304 s, diterima 0,4214304 s; hasil 52.429 byte kembali
  dalam 0,0229716 s; hanya kanal akses yang terpakai.
- **N02**: dua transfer bersamaan diterima 0,4214304 s dan 0,8408608 s; yang kedua mulai tepat saat serialization
  pertama selesai (0,4194304 s), bukan setelah propagasi.
- **N03**: hasil menunggu upload pada kanal akses yang sama, tetapi tidak pada kanal fog lain; LAN naik dan turun
  berjalan bersamaan pada server berbeda tanpa menunggu.
- **N05**: waktu menuju fog akses, fog lain (3 hop), dan cloud (3 hop) beserta jalur balik cocok dengan hitungan
  per hop; setiap hop mulai setelah hop sebelumnya tiba; bit-hop kabel dihitung sekali per hop.
- **N06**: timeout pada 0,1 s di tengah serialization mengirim 250.000 byte, server dilepas, task berikutnya mulai
  tepat 0,1 s, dan `SERIALIZATION_DONE` lama diabaikan sekali.
- **Jalur kegagalan**: antrean link penuh pada input dan pada hasil (setelah CPU), timeout saat menunggu di antrean
  link, saat propagasi, dan saat pengembalian hasil (byte parsial); skenario tidak valid ditolak.
- **Trace kalibrasi nyata** (light, moderate, heavy, dynamic): konservasi `N = ontime + late + failed`; tidak ada
  dua pesan yang tumpang tindih pada satu server; urutan layanan mengikuti urutan masuk antrean (FCFS);
  `busy_s ≤ H`; rute 3 hop tidak maju sebelum hop sebelumnya tiba; log per hop sama dengan agregat per link;
  hasil identik antar episode dalam satu JVM dan antar JVM.
- **Beban penawaran**: bila seluruh task heavy di-offload, bit input+hasil per kanal akses ≈ 1,22 kali kapasitas
  (diuji dalam 1,10–1,35), sesuai pemeriksaan analitis §12.2.

### Pemeriksaan efektivitas tes (mutation)

Empat bug disuntikkan satu per satu, lalu dikembalikan dan JAR dibangun ulang:

| Mutan | Hasil |
|---|---|
| Propagasi menahan server (serialization + propagasi) | Dibunuh oleh 6 tes berbeda (8 entri gagal): N01, N02, N03 half-duplex, N05, dan dua tes timeout |
| Antrean menerima satu pesan lebih banyak (`<=`) | Dibunuh oleh 2 tes (antrean penuh input dan hasil) |
| Pembatalan parsial menghitung byte penuh | Dibunuh oleh 2 tes (N06 dan timeout hasil) |
| Timeout tidak melepas server | Dibunuh oleh 6 tes berbeda (9 entri error), antara lain N06 dan semua tes yang berjalan sampai horizon |

### Karakterisasi pada trace kalibrasi 0 (bukan benchmark metode)

Tindakan tetap `nearest_fog`, topologi heterogen, transport jaringan, satu trace per workload:

| Workload | N | Tepat waktu | Terlambat | Gagal | Alasan gagal | Busy kanal akses maks. | Antrean akses maks. |
|---|---:|---:|---:|---:|---|---:|---:|
| light | 328 | 209 | 99 | 20 | `SERVICE_TIMEOUT` 20 | 14,3 s | 5 |
| moderate | 887 | 224 | 350 | 313 | `SERVICE_TIMEOUT` 313 | 37,7 s | 14 |
| heavy | 1.812 | 14 | 261 | 1.537 | `SERVICE_TIMEOUT` 1.537 | 62,3 s | 24 |
| dynamic | 935 | 117 | 203 | 615 | `SERVICE_TIMEOUT` 615 | 35,4 s | 25 |

Pengamatan yang terverifikasi: tidak ada kegagalan `NETWORK_QUEUE_FULL` karena antrean akses (maks. 25) tidak
mencapai batas 64; seluruh kegagalan berupa timeout. Pada light, CPU saja sudah melebihi deadline untuk 29 task
(12 medium, 12 heavy, 5 light) di fog akses masing-masing; sisanya campuran antrean CPU dan kanal yang belum
saya pisahkan. Ini input bagi gerbang kelayakan solo-task P06, bukan kesimpulan tentang metode.

## Risiko dan keterbatasan tersisa

- Tidak ada ledger energi. Detik serialization dan byte per link dan arah tercatat sebagai prasyarat P04, tetapi
  daya TX/RX, bit-hop, dan idle belum dihitung.
- Tidak ada retransmisi, model paket/PHY, backoff, atau lalu lintas kontrol (sesuai §15).
- Link bukan entity `NetworkTopology` CloudSim; ini abstraksi transfer pesan di antrean event engine.
- Mode jaringan memerlukan nama node `F1..F5` dan `cloud`.
- Verifikasi hanya di Windows, Python 3.12.6, Microsoft OpenJDK 21.0.13. Ubuntu belum diuji. State statis
  `FogDevice`/`TimeKeeper`/`NetworkUsageMonitor` masih belum diinstansiasi.
- Fingerprint source di `P02_verification.json` mencatat keadaan sebelum P03 mengubah `EngineCoordinator`
  dan `EngineMain`; bukti P02 bersifat historis, regresi P02 pada build P03 lulus 21/21.

## Keputusan dan phase berikutnya

- [x] Tujuan, batas, dan keputusan desain dicatat.
- [x] Acceptance N01–N06 dan jalur kegagalan dijalankan dengan hasil tersimpan.
- [x] Efektivitas tes diperiksa dengan bug yang disuntikkan.
- [x] Regresi P00–P02 lulus pada build yang sama; legacy dan trace P01 tidak diubah.
- [x] Keterbatasan dinyatakan.

**Lanjut ke P04 — ledger energi dan lima metrik:** integral daya CPU-IT pada setiap perubahan utilisasi, energi
radio/AP/LAN/WAN dari detik serialization dan bit-hop yang kini tercatat, daya idle komunikasi, satu ledger resmi,
latensi fisik, `zL/zE/zD/zB/zQ`, dan evaluator ulang dari ledger.
