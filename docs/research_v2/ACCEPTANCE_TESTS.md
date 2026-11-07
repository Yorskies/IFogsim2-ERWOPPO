# Acceptance catalog v2 — ditetapkan pada P00

Nilai di bawah adalah hasil yang **diharapkan**, bukan laporan bahwa simulator
offloading sudah lulus. Kasus P02–P10 harus dijalankan pada engine/adapter nyata
pada phase pemiliknya. Fixture nol jaringan tidak boleh menjadi benchmark utama.
Toleransi waktu fisik: `max(1e-6 s, 1e-4 × expected_s)` kecuali disebut lain.
Energi dibandingkan dengan `max(1e-8 J, 1e-6 × expected_J)`.

| ID | Phase pemilik | Fixture/input | Hasil yang diharapkan |
|---|---|---|---|
| F01 | P00 | Config default v0.2 | Valid; fog total 14.000 MIPS; expected count light/moderate/heavy/dynamic = 300/900/1.800/900 |
| F02 | P00 | Config waktu ms, byte negatif, unit salah, unknown key, horizon salah, NaN/Infinity, gamma 0,99, candidate 5.000 | Ditolak sebelum run, dengan alasan; tidak diperbaiki/resampling diam-diam |
| F03 | P00 | Export schema dibanding definisi; Java `--describe` dibanding Python | Object identik; 5 objektif, 7 aksi, 108 nama fitur unik, urutan sama |
| F04 | P00 | Dua probe native CloudSim dalam JVM yang sama | Clock awal 0; event pada 0,000001 dan 0,4194304 s; replay identik |
| F05 | P00 | Model daya IoT `idle=.5, busy=2.5`, u=0 selama 69 s | 34,5 J, bukan nol; ini pemeriksaan model daya, belum ledger seluruh sistem |
| F06 | P00 | Cancel cloudlet aktif pada scheduler upstream | Hazard direproduksi: `usedPes` tetap 1; dicatat untuk adapter P02, bukan diterima sebagai perilaku engine v2 |
| T01 | P01 | Namespace, seed, config identik; urutan metode berbeda | Byte canonical dan SHA-256 trace sama; tidak membaca RNG policy |
| T02 | P01 | Dynamic dibanding moderate pada banyak trace calibration | Expected total sama 900; dynamic empat interval 5/15/35/5, bukan trace duplikat; uji count/distribusi memakai interval probabilistik yang ditetapkan P01 |
| T03 | P01 | Source 0/19/20/99; kedatangan bersamaan | Fog 1/1/2/5; tie stabil menurut ID; tidak ada tugas paksa pada 15/30/45 s |
| C01 | P02 | Satu task 100 MI, satu PE 500 MIPS, tanpa jaringan | CPU 0,2 s; satu Cloudlet native benar-benar selesai |
| C02 | P02 | Tiga task 100 MI datang t=0, satu PE 500, Qwait=2 | Mulai 0/0,2/0,4; selesai 0,2/0,4/0,6 s; urutan ID; busy PE tidak pernah >1 |
| C03 | P02 | Dua PE 500 MIPS, tiga task sama pada t=0 | Dua task pertama mulai t=0 di PE 0/1; task ketiga mulai 0,2; selesai 0,2/0,2/0,4 s |
| C04 | P02 | Satu PE, Qwait=1, tiga task pada t=0 | Pertama running, kedua waiting, ketiga satu `CPU_QUEUE_FULL`; tidak reroute; tiga terminal outcome pada akhir |
| C05 | P02 | RAM fixture 100 byte, task working-set+buffer=101 byte | Tepat satu `RAM_EXHAUSTED`; tidak memakai PE/queue setelah ditolak |
| C06 | P02 | Arrival=0, D=.5, timeout=1.5; receipt=.5/.5001/1.5 | ON_TIME/LATE_SUCCESS/LATE_SUCCESS; receipt tepat timeout diproses lebih dulu; deadline tidak membatalkan task |
| C07 | P02 | Task 1.000 MI di PE 500, D=.2, timeout=.6 | Deadline terlewati .2; timeout .6; FAILED sekali; CPU dipotong setelah 300 MI, resource bebas; completion lama tidak menghidupkan kembali |
| C08 | P02 | Arrival terakhir <60; deadline max3, k3 | Horizon seluruh metode 69; N=Nontime+Nlate+Nfailed; tidak ada unresolved; idle tetap sampai H |
| N01 | P03 | 1 MiB, 20 Mbps, propagasi .002, link kosong | Serialization .4194304 s; diterima .4214304 s; link server bebas sejak .4194304 |
| N02 | P03 | Dua transfer satu link N01 datang bersamaan | Receipt .4214304 dan .8408608 s; tidak menahan serializer selama propagasi |
| N03 | P03 | Dua upload/download pada kanal akses yang sama vs kanal berbeda | Kanal sama berbagi satu serializer half-duplex; kanal berbeda boleh bersamaan; link LAN/WAN punya server per arah |
| N04 | P03 | 1 MiB input; output ceil(5%)=52.429 byte, ke fog akses | Outbound .4214304 s + CPU + inbound .0229716 s; tidak ada LAN/WAN atau fileTransferTime ganda |
| N05 | P03 | WAN/LAN store-forward serta jalur balik | Setiap hop: bytes*8/bps + propagation + actual queue; return membalik jalur; jumlah hop/bit-hop dihitung sekali |
| N06 | P03 | Transfer 1 MiB di20 Mbps timeout pada .1 s setelah serialization mulai | 2.000.000 bit =250.000 byte terkirim; energi hanya interval .1 s; satu failure, serializer dilepas; event arrival usang diabaikan |
| E01 | P04 | Default seluruh sistem idle sampai69 | Pidle CPU=568,4333 W; komunikasi=55 W; energi total=43.016,8977 J; dynamic=0; zE=0 untuk trace nonkosong |
| E02 | P04 | IoT task100 MI pada500 MIPS; seluruh komponen lain idle | Tambahan CPU energi (2,5−.5)*.2=.4 J; idle tetap dihitung terpisah |
| E03 | P04 | Wireless upload1 MiB tanpa queue/cancel | Tambahan energi (1,3+1,5)*.4194304=1,17440512 J; idle tidak ditambah ulang |
| E04 | P04 | Utilisasi fog [1,1,0,0,0] konstan, H69 | Population std=sqrt(.24); integral=69*sqrt(.24); zB=1 |
| M01 | P04 | N10, ontime6, late2, failed2 | Violation=.4; reliability=.8; zD=.4; zQ=.2; semua denominator10 |
| M02 | P04 | N2, satu sukses latency .2, satu gagal, dynamic energy1 J | zL=(.2+9)/(2*9)=.5111111111; zE=1/(50*2)=.01; physical latency mean=.2 s |
| M03 | P04 | Semua task gagal atau trace kosong | Semua gagal: physical latency/J-per-success=null dengan count jelas; N0: reject trace, tanpa resampling |
| G01 | P05 | Episode dengan delayed completion dan last-step drain | Satu aksi/arrival; setelah akhir terminated=true,truncated=false; semua cost drain masuk transisi terakhir |
| G02 | P05 | Bobot valid; kumpulkan reward dan biaya akhir | Sum reward = -100 dot(w,z); toleransi max(1e-8 absolut,1e-6 relatif); tidak ada bonus/clipping |
| G03 | P05 | Queue penuh, aksi cloud; socket putus atau versi/hash salah | Queue penuh tetap punya outcome; kesalahan teknis menghentikan run; tidak ada fallback Python/episode sukses palsu |
| R01 | P06 | Trace+policy deterministik sama, dua JVM/run terpisah | Event/outcome/energi sama; wall-clock diabaikan; tidak ada state static episode sebelumnya |
| L01 | P07 | Seed/trace sama, training sampai F vs checkpoint F dari lintasan B | Parameter policy/optimizer dan counters sama; jika berbeda, checkpoint reuse dilarang dan biaya training terpisah dicatat |
| S01 | P08 | Equal/manual/vertex, simplex repair, slot duplikat | Sum(w)=1; setiap w>=.02; anchor dipertahankan; duplikasi tetap memakai slot; jumlah80*2 model |
| B01 | P09 | K5120, 80 kandidat*2, sum Nval19500, F102400, rollout512 | S819200; V3120000; C4041600; B4041728; overhead128 keputusan; tidak membebankan search dua kali |
| O01 | P09 | Proses terputus sebelum outcome/artifact valid | Status tidak complete; retry run dari awal, seed sama, attempt bertambah; completed run hash sama tetap utuh |
| A01 | P10 | Semua paired difference0, tie, SD0, missing pair | p=1 untuk semua0; missing pair memblokir analisis utama; dz SD0 nonzero=undefined; tidak fallback uji atau tambah seed |

Nilai idle E01: CPU `100*.5 + 50+65+83.4333+100+120 +100`; komunikasi
`100*.1 +5*3+20+10`. Nilai tersebut hanya untuk parameter default dan horizon69.
Fidelity/calibration gates dan statistik konfirmatori mengikuti bagian24/23
spesifikasi; keberhasilan ERWO maupun p<.05 bukan kriteria kelulusan teknis.

P01 T01–T03 telah diverifikasi; protokol probabilistiknya ditetapkan pada
[TRACES.md](TRACES.md) dan hasil aktual pada
[P01_trace_validation.md](milestones/P01_trace_validation.md).

**P02 C01–C08 telah dijalankan** pada engine nyata (8 November 2026): lulus, dengan transport
fixture nol-jaringan. Hasil dan pemetaan tes: [P02_engine_validation.md](milestones/P02_engine_validation.md)
dan [P02_verification.json](milestones/P02_verification.json). Kasus C06 dijalankan dengan
node 10.000 MIPS agar waktu terima 0,5/0,5001/1,5 s dapat dibentuk dari MI integer. **P03 N01–N06 telah dijalankan** (8 November 2026) pada transport jaringan nyata: lulus. Hasil dan pemetaan tes:
[P03_network_validation.md](milestones/P03_network_validation.md) dan
[P03_verification.json](milestones/P03_verification.json). N01 dan N04 dijalankan oleh satu tes yang sama
(fog akses, 1 MiB masuk dan 52.429 byte kembali). **P04 E01–E04 dan M01–M03 telah dijalankan** (8 November 2026): lulus, termasuk perhitungan ulang oleh evaluator
independen. Hasil dan pemetaan tes: [P04_accounting_validation.md](milestones/P04_accounting_validation.md) dan
[P04_verification.json](milestones/P04_verification.json). Kasus E03 dijalankan pada mode jaringan penuh (energi hop
diperiksa pada catatan hop, idle diperiksa tidak bertambah). **P05 G01–G03 telah dijalankan** (8 November 2026) lewat soket dan environment Gymnasium: lulus. Hasil dan pemetaan tes:
[P05_gym_integration.md](milestones/P05_gym_integration.md) dan [P05_verification.json](milestones/P05_verification.json). G03 diuji pada
sisi protokol (kegagalan teknis menghentikan run tanpa pengganti); hasil antrean penuh sebagai outcome diuji pada N-kasus P03 dan
pada tes biaya per jenis hasil P05. Kasus R, L, S, B, O, dan A masih berupa spesifikasi.
