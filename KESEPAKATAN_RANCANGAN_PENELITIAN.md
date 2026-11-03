# Kesepakatan rancangan penelitian ERWO-PPO

Tanggal: 3 November 2026. Versi: **0.2 — spesifikasi teknis untuk ditinjau sebelum implementasi**.

Prinsip penelitian pada bagian 1–10 berasal dari kesepakatan diskusi. Pilihan numerik dan teknis pada bagian 11 dan seterusnya ditetapkan asisten atas delegasi pengguna. Angka tersebut merupakan **parameter awal simulasi sintetis yang dapat direproduksi**, bukan hasil pengukuran perangkat nyata atau konfigurasi yang telah terbukti optimal. Kalibrasi dan perubahan hanya mengikuti prosedur pilot yang ditulis di sini, sebelum membuka hasil test.

Dokumen ini mencatat keputusan yang telah disepakati setelah review percobaan awal. Dokumen ini menjadi pendamping [Rencana Penelitian Lanjutan](RENCANA_PENELITIAN_LANJUTAN.md). Keputusan di sini menggantikan usulan awal pada rencana tersebut apabila terdapat perbedaan. Hasil eksperimen lama tetap merupakan bukti untuk implementasi lama, bukan hasil validasi rancangan baru.

### Ringkasan untuk tinjauan

| Keputusan teknis | Pilihan v0.2 |
|---|---|
| Sistem | 100 IoT, 5 fog, 1 cloud; event engine iFogSim2/CloudSim |
| CPU | FCFS multi-PE, tugas satu PE, tanpa overbooking; antrean bounded |
| Waktu | Kedatangan 60 s; k timeout 3; pengamatan sampai 69 s |
| Beban | Poisson 5/15/30 tugas/s; dynamic 5→15→35→5 tugas/s |
| Energi | CPU-IT, radio, AP, LAN/WAN, termasuk idle; parameter sintetis berlabel |
| Penilaian | Lima biaya ternormalisasi, kepentingan 1/5, jarak ke ideal |
| Policy | Satu PPO campuran empat workload; observasi 108 fitur |
| Pencarian | 80 kandidat × 2 seed/model; K awal 5.120, gerbang fidelity pilot |
| Model akhir | 102.400 keputusan; checkpoint 51.200 untuk sensitivitas |
| Replikasi | 20 outer run; 100 trace test per workload |
| Efisiensi | Validasi pencarian ikut biaya; baseline total-budget dapat jauh lebih lama |
| Status | Hanya spesifikasi; kode dan hasil lama belum diubah |

Bagian yang perlu dibaca terlebih dahulu: [parameter fisik](#14-komputasi-antrean-dan-admission), [lima biaya](#16-metrik-dan-normalisasi-yang-dibekukan), [reward tertunda](#18-reward-lima-komponen-dan-hasil-yang-tertunda), [anggaran adil](#21-anggaran-eksperimen-dan-efisiensi), dan [gerbang pilot](#24-pilot-dan-gerbang-sebelum-eksperimen-utama).

## 1. Fokus dan tujuan penelitian

Fokus utama adalah **manfaat dan efisiensi optimasi bobot reward**, dengan NSGA-II sebagai metode pencarian bobot dan PPO sebagai algoritma pembelajaran kebijakan offloading.

Tujuan substantifnya adalah memperoleh kompromi lima objektif secara keseluruhan:

1. Meminimalkan latensi.
2. Meminimalkan energi total sistem IoT–fog–cloud.
3. Meminimalkan pelanggaran deadline.
4. Meminimalkan ketimpangan beban antar-node fog.
5. Memaksimalkan QoS berupa keberhasilan/keandalan layanan.

**Kelima objektif sama penting dalam evaluasi.** Penelitian tidak diarahkan untuk mengoptimalkan satu objektif dengan mengabaikan objektif lain.

Pertanyaan utama:

> Apakah pencarian bobot reward offline menggunakan NSGA-II menghasilkan kompromi lima objektif yang lebih baik daripada konfigurasi bobot sederhana dan pencarian acak, dengan biaya pencarian yang dapat dibenarkan?

## 2. Pertanyaan penelitian

| ID | Pertanyaan |
|---|---|
| RQ1 — Manfaat | Apakah bobot hasil optimasi memperbaiki kompromi kinerja PPO dibanding bobot equal dan manual? |
| RQ2 — Nilai tambah NSGA-II | Apakah NSGA-II lebih efektif daripada random search pada anggaran pencarian yang sama? |
| RQ3 — Efisiensi | Apakah manfaat tetap ada ketika biaya pencarian dan training akhir diperhitungkan bersama? |

Optimasi bobot dilakukan **secara offline** sebelum training akhir PPO. Adaptasi bobot online atau perubahan preferensi selama operasi belum menjadi bagian rancangan yang disepakati.

## 3. Dasar simulator dan cakupan sistem

| Aspek | Kesepakatan |
|---|---|
| Dasar simulator | Event engine iFogSim2/CloudSim |
| Peran PPO | Menentukan lokasi pemrosesan setiap tugas |
| Peran simulator | Mengeksekusi kejadian dan menghasilkan waktu selesai, antrean, penggunaan sumber daya, serta energi sesuai model |
| Struktur tugas | Tugas independen |
| Granularitas offloading | Tugas di-offload secara utuh |
| Sumber daya | Kapasitas komputasi dan antrean terbatas |
| Mobilitas dan migrasi | Tidak dimasukkan pada model awal |

Keputusan ini memerlukan integrasi yang berbeda dari engine socket custom pada percobaan lama. Keberadaan source/JAR iFogSim2 atau respons socket saja tidak dianggap bukti integrasi event engine telah selesai.

## 4. Topologi dan konektivitas

### 4.1 Jumlah komponen

| Komponen | Jumlah |
|---|---:|
| Perangkat IoT | 100 |
| Node fog | 5 |
| Cloud | 1 |

Angka satu cloud menyatakan satu komponen tujuan logis. Bagian 14 menetapkan satu host ekuivalen delapan PE untuk komponen tersebut; bukan klaim bahwa seluruh pusat data nyata hanya memiliki satu host.

### 4.2 Hubungan jaringan

- Setiap perangkat IoT terhubung ke satu fog akses.
- Distribusi awal adalah 20 perangkat IoT per fog akses.
- Antar-fog terhubung melalui jaringan backbone.
- Cloud dijangkau melalui jaringan fog.
- Tujuan pemrosesan dapat berupa perangkat IoT asal, salah satu dari lima fog, atau cloud.
- Waktu dan energi komunikasi mengikuti jalur yang dilalui, termasuk pengiriman hasil ke perangkat asal.

### 4.3 Homogenitas dan pemerataan beban

- **Fog homogen** digunakan untuk validasi awal dan kondisi dasar yang terkendali.
- **Fog heterogen** digunakan sebagai skenario utama penelitian.
- Parameter heterogenitas ditentukan sebelum melihat metode mana yang unggul dan harus mempunyai dasar yang dapat dijelaskan.
- Ketimpangan beban diukur berdasarkan utilisasi relatif terhadap kapasitas node fog, bukan semata jumlah tugas yang diberikan ke setiap node.
- Ketimpangan menggunakan simpangan baku utilisasi fog dan diintegrasikan terhadap waktu, sesuai bagian 16.

## 5. Model tugas dan status layanan

Tugas merupakan campuran kelas ringan, sedang, dan berat. Distribusi ukuran data, kebutuhan komputasi, dan deadline dibuat sama antar-workload pada eksperimen awal. Parameter kelas ditetapkan pada bagian 12.

Setiap tugas sekurangnya perlu memiliki waktu kedatangan, perangkat asal, ukuran data, kebutuhan komputasi, dan deadline. Ukuran hasil perlu ditentukan agar komunikasi balik dapat dimodelkan.

Status layanan dibedakan sebagai berikut:

| Status | Berhasil dilayani? | Melanggar deadline? |
|---|---|---|
| Selesai tepat waktu | Ya | Tidak |
| Selesai terlambat | Ya | Ya |
| Gagal atau ditolak | Tidak | Ya dalam metrik deadline end-to-end yang disepakati |

Keberhasilan layanan dibedakan dari ketepatan waktu. Tugas terlambat yang akhirnya selesai tetap berhasil dilayani, tetapi tercatat sebagai pelanggaran deadline.

Kapasitas antrean terbatas dan mekanisme penolakan harus mencerminkan sistem yang diteliti. Tidak semua tugas diasumsikan selalu diterima dan berhasil selesai. Deadline yang terlewati tidak membatalkan tugas. Batas layanan proporsional, FCFS, aturan penolakan, serta akhir pengamatan ditetapkan pada bagian 13–14. Semua tugas tetap masuk denominator evaluasi.

## 6. Definisi lima objektif

| Objektif | Definisi yang disepakati | Arah |
|---|---|---|
| Latensi | Waktu sejak tugas datang sampai hasil diterima perangkat asal, mencakup transmisi, antrean, komputasi, dan pengiriman hasil | Minimum |
| Energi | Energi total komponen sistem yang dimodelkan selama periode pengukuran | Minimum |
| Pelanggaran deadline | Persentase seluruh tugas datang yang tidak berhasil selesai tepat waktu; tugas gagal/ditolak tetap diperhitungkan | Minimum |
| Ketimpangan beban | Variasi utilisasi komputasi relatif terhadap kapasitas antar-node fog selama periode pengukuran | Minimum |
| QoS/keandalan | Proporsi seluruh tugas datang yang berhasil selesai, termasuk tugas yang selesai terlambat | Maksimum |

Latensi tugas selesai dilaporkan bersama tingkat kegagalan layanan. Latensi rata-rata tidak boleh ditafsirkan tanpa memperhatikan tugas yang gagal/ditolak. Bagian 16 menetapkan penalti latensi bagi kegagalan khusus untuk fungsi kompromi; nilai tersebut dipisahkan dari latensi fisik yang terukur.

### 6.1 Cakupan energi

Energi bukan hanya baterai perangkat IoT. Batas model energi mencakup:

| Komponen | Konsumsi yang diperhitungkan |
|---|---|
| IoT | Komputasi lokal, idle, pengiriman dan penerimaan data |
| Fog | Pemrosesan, idle, dan komunikasi yang dimodelkan |
| Cloud | Pemrosesan, idle, dan komunikasi yang dimodelkan |
| Infrastruktur jaringan | Gateway, router, atau link apabila dimodelkan secara eksplisit |

Secara konseptual:

\[
E_{\mathrm{sistem}} = E_{\mathrm{IoT}} + E_{\mathrm{fog}} + E_{\mathrm{cloud}} + E_{\mathrm{jaringan}}.
\]

- Energi komunikasi mempunyai batas komponen yang jelas agar tidak dihitung dua kali.
- Infrastruktur yang tidak dimodelkan harus dinyatakan sebagai pengecualian; istilah energi total merujuk pada batas sistem yang dijelaskan.
- Energi idle ikut diperhitungkan.
- Energi total dilaporkan dalam Joule, disertai Joule per tugas berhasil selesai dan jumlah tugas datang/selesai/gagal.
- Semua metode memakai durasi pengukuran dan aturan penanganan tugas tersisa yang sama.

## 7. Empat profil workload

| Workload | Pola kedatangan | Sasaran pengujian |
|---|---|---|
| Light | Laju rendah, relatif stabil | Kondisi sumber daya masih longgar |
| Moderate | Laju menengah, relatif stabil | Kondisi mulai terjadi kontensi |
| Heavy | Laju tinggi, relatif stabil | Kondisi sumber daya tertekan |
| Dynamic | Laju berubah sepanjang waktu, termasuk transisi dan burst | Respons kebijakan terhadap perubahan beban |

Prinsip eksperimennya:

- Durasi simulasi sama antar-workload pada eksperimen awal.
- Karakteristik kelas tugas dipertahankan sama; pembeda awal adalah laju dan pola kedatangan.
- Workload berat menghasilkan lebih banyak kedatangan dalam durasi yang sama, bukan sekadar episode dengan lebih banyak langkah.
- Untuk pasangan skenario dan seed yang sama, semua metode menerima trace eksternal tugas yang sama.
- Nilai laju kedatangan dan profil burst dikalibrasi melalui pilot berdasarkan kapasitas sistem, lalu dikunci sebelum perbandingan metode utama.
- Moderate dan dynamic harus berbeda secara desain dan terverifikasi pada trace.

Distribusi kedatangan, panjang simulasi, proporsi kelas tugas, dan parameter numeriknya ditetapkan pada bagian 12–14. Profil dynamic mempunyai rata-rata laju yang sama dengan moderate, dengan pola temporal yang berbeda.

## 8. Pemilihan kompromi lima objektif

### 8.1 Preferensi evaluasi

Kelima objektif mempunyai kepentingan evaluasi yang sama, masing-masing **1/5**. Keberhasilan metode dinilai menggunakan aturan evaluasi bersama, bukan total reward dengan bobot berbeda milik masing-masing metode.

Untuk menyamakan arah, QoS diubah menjadi tingkat kegagalan. Jika \(Q\) merupakan rasio keberhasilan pada rentang 0–1, biaya QoS adalah \(1-Q\).

Kelima biaya kemudian dinormalisasi menjadi \(z_L,z_E,z_D,z_B,z_Q\), dengan nilai lebih kecil menunjukkan hasil lebih baik. Aturan dan batas normalisasi berasal dari spesifikasi atau data pilot/validasi dan dibekukan sebelum evaluasi test.

### 8.2 Aturan pemilihan solusi

Solusi dipilih menggunakan jarak terhadap titik ideal pada ruang biaya ternormalisasi:

\[
D = \sqrt{\frac{1}{5}\left(z_L^2 + z_E^2 + z_D^2 + z_B^2 + z_Q^2\right)}.
\]

- Titik ideal pada representasi tersebut adalah biaya nol pada kelima dimensi; ini titik acuan pemilihan, bukan jaminan solusi yang dapat dicapai.
- Solusi dengan \(D\) terkecil pada **data validasi** dipilih untuk pengujian akhir.
- NSGA-II dan random search menggunakan normalisasi, preferensi, serta aturan seleksi yang sama.
- Pareto front tetap dilaporkan agar trade-off antar-solusi terlihat.
- Data test tidak digunakan untuk memilih bobot, mengubah batas normalisasi, atau memilih konfigurasi terbaik.

Nilai di luar rentang tidak dipotong untuk menyembunyikan hasil buruk. Aturan lengkap, termasuk solusi seri, ditetapkan pada bagian 16 dan 20.

### 8.3 Bobot reward dan bobot evaluasi mempunyai peran berbeda

| Jenis bobot | Peran |
|---|---|
| Bobot evaluasi | Sama penting, tetap 1/5 per objektif; digunakan bersama untuk menilai metode |
| Bobot reward PPO | Membentuk proses belajar; dicari oleh NSGA-II atau random search, atau ditetapkan pada baseline equal/manual |

Kepentingan evaluasi yang sama tidak mengharuskan bobot reward optimal semuanya 0,2. Bentuk reward dan ruang pencarian bobot ditetapkan pada bagian 18–20.

## 9. Pembanding utama

| Metode | Tujuan pembandingan |
|---|---|
| PPO-Equal | Bobot reward sama untuk lima objektif sebagai baseline |
| PPO-Manual | Bobot ditentukan terlebih dahulu dengan alasan yang didokumentasikan |
| Random Search + PPO | Menguji manfaat pencarian bobot dan menjadi pembanding anggaran pencarian NSGA-II |
| NSGA-II + PPO | Metode ERWO-PPO yang diteliti |
| Least Fog | Pembanding praktis yang sederhana dan kuat pada eksperimen lama |

Perbandingan bobot menggunakan algoritma PPO, arsitektur policy, dan konfigurasi pembelajaran yang sama agar efek cara memilih bobot lebih mudah diidentifikasi. Bagian 19–21 menetapkan hyperparameter, baseline, dan anggarannya.

Baseline RL tambahan dapat dibahas kemudian, tetapi belum menjadi syarat utama yang disepakati pada tahap ini.

## 10. Dua protokol perbandingan anggaran

### 10.1 Training akhir sama

Semua varian PPO menerima anggaran training akhir yang sama. Biaya pencarian bobot dilaporkan terpisah.

Tujuannya menilai manfaat bobot terpilih terhadap proses pembelajaran akhir. Hasil protokol ini tidak langsung menjadi bukti efisiensi komputasi total.

### 10.2 Anggaran total sebanding

Biaya pencarian bobot dan training akhir diperhitungkan bersama. Protokol ini menjadi dasar utama untuk menilai klaim efisiensi.

Komponen yang dicatat terpisah mencakup training kandidat, validasi kandidat, training akhir, evaluasi test, serta waktu komputasi. Anggaran utama yang disamakan adalah jumlah keputusan/interaksi lingkungan, termasuk validasi pencarian. Menyamakan interaksi tidak otomatis menyamakan waktu wall-clock; rinciannya pada bagian 21.

Random search dan NSGA-II menerima anggaran pencarian yang sebanding serta protokol validasi dan seleksi yang sama.

Parameter awal dan aturan pengunciannya tersedia pada bagian 19–24. Matriks 80 percobaan lama tidak otomatis menjadi protokol final rancangan baru. Eksperimen utama hanya boleh dimulai setelah gerbang validasi dan pilot lulus.

## 11. Satuan, ruang lingkup, dan sumber parameter

| Besaran | Satuan internal |
|---|---|
| Waktu | Detik; tabel latensi juga menyertakan ms |
| Pekerjaan CPU | MI, juta instruksi; panjang tugas dibulatkan menjadi MI integer |
| Kapasitas CPU | MIPS per PE; kapasitas node = MIPS per PE × jumlah PE |
| Data | Byte; 1 MiB = 1.048.576 byte |
| Laju jaringan | bit/s; 1 Mbps = 1.000.000 bit/s |
| Daya dan energi | Watt dan Joule; energi = integral daya terhadap detik |

Referensi skala komputasi berasal dari contoh lokal [DCNSFog.java](ifogsim/src/org/fog/test/perfeval/DCNSFog.java) dan publikasi iFogSim2. Konfigurasi PE, profil daya baru, jaringan, kelas tugas, dan arrival rate berikut adalah pilihan desain sintetis. Tidak ada klaim bahwa semuanya merupakan spesifikasi perangkat komersial tertentu.

Tidak dimodelkan pada versi awal: mobilitas, migrasi, DVFS, sleep/power-off, retransmisi paket, gangguan node acak, disk I/O, biaya uang, maupun pendinginan fasilitas. RAM dan storage mempunyai batas kapasitas, tetapi daya perangkat kerasnya tidak ditambahkan lagi secara terpisah karena profil daya node diperlakukan sebagai daya IT agregat. Energi jaringan dimodelkan eksplisit. Ruang lingkupnya adalah **energi IT sistem yang dimodelkan**, bukan konsumsi listrik fasilitas dunia nyata secara lengkap.

## 12. Konfigurasi tugas dan pembangkit beban

### 12.1 Kelas tugas

Setiap tugas menggunakan satu PE. Panjang CPU dan ukuran input diambil independen bersyarat pada kelas. Tidak ada prioritas antrean berdasarkan kelas.

| Kelas | Probabilitas | Panjang CPU, uniform integer | Input, uniform kontinu | Deadline relatif, uniform kontinu |
|---|---:|---:|---:|---:|
| Ringan | 0,50 | 100–300 MI | 0,05–0,20 MiB | 0,25–0,60 s |
| Sedang | 0,35 | 500–1.000 MI | 0,20–0,80 MiB | 0,60–1,20 s |
| Berat | 0,15 | 1.500–3.000 MI | 0,80–2,20 MiB | 1,50–3,00 s |

- Ukuran input dibulatkan ke atas menjadi byte. Hasil = `ceil(0.05 × input_bytes)`.
- Working set = 64 MiB per tugas, ditambah buffer input/hasil; dialokasikan saat tugas diterima di node komputasi dan dilepas saat selesai/gagal.
- IoT asal dipilih uniform dari 100 perangkat. Pemetaan tetap: perangkat 0–19 ke F1, 20–39 ke F2, dan seterusnya.
- Tugas tidak mempunyai dependensi, tidak dibagi, tidak direplikasi, dan tidak dicoba ulang.
- Nilai harapan panjang CPU = **700 MI/tugas**; nilai harapan input = **0,4625 MiB/tugas**.
- Semua atribut disimpan dalam trace sebelum kebijakan dievaluasi; metode tidak boleh mengubah trace atau urutan RNG generator.

### 12.2 Kedatangan

Kedatangan menggunakan proses Poisson homogen untuk profil tetap dan Poisson nonhomogen piecewise-constant untuk dynamic. Generator nonhomogen menggunakan integrated hazard; jangan menambahkan satu tugas paksa pada batas fase. Semua laju pada tabel adalah **total sistem**, bukan per perangkat.

Kapasitas referensi fog = 14.000 MIPS. Laju referensi didefinisikan sebagai `14000 / 700 = 20 tugas/s`. Ini ukuran offered demand terhadap kapasitas fog, bukan utilisasi aktual seluruh sistem yang juga memiliki IoT dan cloud.

| Profil | Laju total | Ekspektasi jumlah tugas selama 60 s |
|---|---|---:|
| Light | 5 tugas/s sepanjang periode kedatangan | 300 |
| Moderate | 15 tugas/s sepanjang periode kedatangan | 900 |
| Heavy | 30 tugas/s sepanjang periode kedatangan | 1.800 |
| Dynamic | 0–15 s: 5/s; 15–30 s: 15/s; 30–45 s: 35/s; 45–60 s: 5/s | 900 |

Moderate dan dynamic mempunyai rata-rata laju yang sama. Perbandingan keduanya mengisolasi pola temporal, bukan perubahan jumlah tugas rata-rata. Jumlah aktual tetap stokastik dan dicatat untuk setiap trace. Dynamic diawali beban rendah, mengalami burst, lalu mempunyai fase pemulihan.

Sebagai pemeriksaan kapasitas, bila semua tugas di-offload, offered traffic rata-rata per kanal akses pada heavy sekitar **1,22 kali** kapasitas kanal yang ditetapkan di bagian 15. Angka ini adalah pemeriksaan analitis, bukan hasil bahwa semua metode pasti mengalami congestion.

## 13. Waktu, deadline, timeout, dan akhir simulasi

| Parameter | Nilai utama |
|---|---:|
| Periode kedatangan `T` | 60 s |
| Faktor batas layanan `k` | 3 |
| Deadline relatif maksimum `Dmax` | 3 s |
| Akhir pengamatan `H = T + k Dmax` | 69 s |
| Toleransi perbandingan waktu | 1e-9 s |
| Minimum event spacing CloudSim yang diminta | 1e-6 s; harus diverifikasi pada validasi |

Untuk tugas i yang datang pada ai dan mempunyai deadline relatif Di:

- Deadline absolut: `ai + Di`.
- Timeout absolut: `ai + 3 Di`.
- Keberhasilan berarti **hasil sudah diterima IoT asal**, bukan hanya CPU selesai.
- Melewati deadline hanya menandai violation; tugas tetap dilayani sampai selesai atau timeout.
- Timeout membatalkan sisa komputasi, antrean, atau transfer. Resource dilepas; byte dan energi yang sudah terpakai tidak dikembalikan.
- Tidak ada tugas baru pada `t >= T`. Semua metode tetap diamati sampai H, termasuk ketika sudah tidak ada tugas aktif.
- Semua node tetap menyala sampai H; tidak ada keuntungan energi karena menghentikan simulasi lebih cepat.
- Semua tugas datang masuk denominator. Setelah H tidak boleh ada tugas dengan status belum terselesaikan; bila ada, run gagal validasi.
- Tugas tepat pada batas deadline dinyatakan tepat waktu; hasil tepat pada batas timeout dinyatakan berhasil. Toleransi di atas dipakai konsisten.

Urutan kejadian dengan timestamp sama: (1) penyelesaian CPU/transfer, delivery dan penerimaan hasil; (2) pemeriksaan deadline/timeout; (3) kedatangan tugas eksternal dan keputusan offloading. Urutan dalam kategori yang sama memakai ID tugas, lalu ID resource. Kebutuhan ini harus diterapkan melalui dispatcher/priority layer yang terdokumentasi; jangan mengasumsikan prioritas bawaan queue CloudSim sudah sesuai.

## 14. Komputasi, antrean, dan admission

### 14.1 Resource utama

`Qwait` menghitung tugas menunggu, tidak termasuk yang sedang berjalan. Storage adalah kapasitas reservasi yang tidak menjadi bottleneck pada versi awal.

| Node | Jumlah | PE/node | MIPS/PE | Total MIPS/node | RAM | Qwait | Idle/busy CPU-IT |
|---|---:|---:|---:|---:|---:|---:|---:|
| IoT | 100 | 1 | 500 | 500 | 1 GiB | 2 | 0,5 / 2,5 W |
| F1 | 1 | 2 | 700 | 1.400 | 4 GiB | 16 | 50 / 70 W |
| F2 | 1 | 2 | 1.050 | 2.100 | 4 GiB | 16 | 65 / 88 W |
| F3 | 1 | 2 | 1.400 | 2.800 | 8 GiB | 16 | 83,4333 / 107,339 W |
| F4 | 1 | 2 | 1.750 | 3.500 | 8 GiB | 16 | 100 / 135 W |
| F5 | 1 | 2 | 2.100 | 4.200 | 16 GiB | 16 | 120 / 155 W |
| Cloud | 1 logis | 8 | 5.600 | 44.800 | 64 GiB | 64 | 100 / 200 W |

Storage: IoT 8 GiB, fog 64 GiB, cloud 1 TiB. Profil IoT/cloud dan F1/F2/F4/F5 adalah asumsi sintetis. Pasangan daya F3 diadopsi dari contoh source lokal, bukan pengukuran hardware penelitian ini. Total kapasitas fog heterogen = 14.000 MIPS.

Pada kondisi homogen, seluruh fog memakai konfigurasi F3, termasuk RAM, Qwait, dan daya; total kapasitas fog tetap 14.000 MIPS. Heterogenitas utama mengubah kapasitas dan profil energi bersama. Jangan mengklaim efeknya hanya berasal dari heterogenitas CPU. Analisis kapasitas-saja dapat memakai daya semua fog seperti F3 sebagai sensitivitas tambahan.

### 14.2 Penjadwalan

- Satu host dan satu VM/module komputasi per node; PE dipin dan kapasitas tidak di-overbook.
- FCFS nonpreemptive, satu tugas per PE. Saat beberapa PE bebas, pilih PE ber-ID terkecil.
- Tugas menunggu dilayani sebelum tugas baru. Timeout merupakan satu-satunya pembatalan paksa pada versi awal.
- Adaptasi `CloudletSchedulerSpaceShared` dengan tugas satu PE dapat dipakai, tetapi harus dibuktikan memenuhi antrean FCFS bounded, cancellation, dan resource accounting yang dirancang.
- Jangan memakai scheduler time-shared default dan tetap menyebut eksperimen FCFS.
- Transfer input dimodelkan terpisah; jangan sekaligus menambahkan transfer time ke panjang Cloudlet karena akan menghitung latensi dua kali.
- Admission CPU dilakukan ketika input tiba di node tujuan, bukan dengan reservasi saat PPO memilih node. Jika tidak ada PE bebas dan antrean penuh, atau RAM tidak cukup, tugas ditolak.
- Penolakan tidak memicu rerouting otomatis. Energi transfer input yang sudah terjadi tetap dihitung.
- CPU pada IoT memproses tugas lokal perangkat itu sendiri; tidak menerima offloading dari IoT lain.

## 15. Jaringan dan energi komunikasi

### 15.1 Topologi transport

| Segmen | Kapasitas | Propagasi satu arah | Queue transfer menunggu |
|---|---:|---:|---:|
| IoT–AP/fog akses | 20 Mbps per kelompok 20 IoT | 2 ms | 64 per kanal, dua arah digabung |
| Masing-masing fog–switch pusat | 1 Gbps | 0,5 ms | 64 per arah |
| Switch/gateway–cloud | 50 Mbps | 20 ms | 64 per arah |

- Lima kanal akses wireless terpisah. Setiap kanal half-duplex: upload dan download berbagi 20 Mbps; bukan 20 Mbps khusus untuk setiap IoT.
- Link kabel full-duplex: kedua arah mempunyai server dan antrean terpisah.
- Transfer mengikuti FCFS, store-and-forward, satu transfer serial per server link. Ini abstraksi transfer pesan, bukan simulasi paket/radio PHY.
- Serialization time = `8 × bytes / bit_per_second`. Server link bebas setelah serialization; propagasi tidak menahan server link.
- Antrean link penuh menghasilkan `NETWORK_QUEUE_FULL`, suatu kegagalan layanan. Transfer aktif hanya dipotong jika tugas timeout.
- Saat pembatalan transfer, jumlah byte yang sudah terkirim dihitung dari laju × waktu serialization yang sudah berlangsung.
- Pemrosesan di fog akses hanya melewati wireless. Fog lain melewati wireless → link fog asal → switch → link fog tujuan. Cloud melewati wireless → link fog asal → WAN cloud. Hasil memakai jalur balik.
- Pemrosesan lokal tidak mengirim data tugas melalui jaringan. Tidak ada trafik kontrol jaringan tambahan pada versi awal; overhead controller/RPC diukur dalam wall-clock terpisah.

### 15.2 Model daya

CPU-IT menggunakan `P(u) = Pidle + (Pbusy-Pidle)u`, dengan `u = busy_PE / total_PE`. Semua PE mempunyai kapasitas sama di dalam satu node dan berjalan pada frekuensi tetap. Integrasi dilakukan pada setiap perubahan utilisasi dan ditutup tepat pada H.

Untuk idle, [FogLinearPowerModel.java](ifogsim/src/org/fog/utils/FogLinearPowerModel.java) mempertahankan Pidle pada u=0. [PowerModelLinear.java](ifogsim/src/org/cloudbus/cloudsim/power/models/PowerModelLinear.java) pada source ini mengembalikan nol pada u=0, sehingga tidak boleh dipakai tanpa koreksi. Ledger energi baru harus menghindari penambahan ulang counter energi default `FogDevice`.

| Komponen komunikasi | Daya idle | Tambahan daya saat aktif |
|---|---:|---:|
| Radio IoT | 0,1 W/perangkat | TX +1,3 W; RX +0,9 W |
| AP | 3 W/AP | TX +2 W; RX +1,5 W |
| Switch pusat | 20 W | Digabung ke koefisien bit-hop kabel |
| Gateway WAN | 10 W | Digabung ke koefisien bit-hop WAN |

- Transfer wireless memakai tambahan daya TX pengirim + RX penerima selama serialization. Upload: IoT TX dan AP RX; download: AP TX dan IoT RX.
- Energi dinamis satu hop LAN: **5 nJ per bit-hop**, sudah mencakup port/NIC yang dimodelkan; tidak ditambah lagi pada endpoint.
- Energi dinamis hop WAN: **20 nJ per bit-hop**, dengan cakupan port/transit agregat yang sama. Ini asumsi energi jaringan, bukan model seluruh router Internet.
- Daya idle komunikasi tetap terpisah dari daya CPU-IT dan dihitung sepanjang H. Komputasi dan komunikasi dapat berlangsung bersamaan.
- Pada batas model ini, profil CPU-IT tidak mencakup tambahan daya transmisi yang dicatat di ledger jaringan. Budget idle 20 W LAN dan 10 W WAN mencakup perangkat/port kabel yang dimodelkan secara agregat; jangan menambahkan idle NIC kabel sekali lagi pada tiap hop.
- Tidak ada retransmisi; tidak ada daya dinamis tambahan pada masa propagasi setelah serialization. Asumsi ini harus dinyatakan.
- Energi total dihitung sekali dalam ledger per komponen. Untuk per-task reporting, energi dinamis dapat diatribusikan ke task; energi idle hanya dipecah melalui aturan pelaporan yang dinyatakan, bukan dihitung ulang.
- IoT tidak dimatikan karena baterai habis pada versi awal. Fokusnya energi total, bukan battery survival.

Seluruh nilai radio, jaringan, dan daya sintetis harus diberi label asumsi. Sebelum klaim hardware atau penghematan fasilitas nyata, diperlukan pengukuran atau parameter perangkat yang tervalidasi.

## 16. Metrik dan normalisasi yang dibekukan

Untuk satu trace dengan N tugas dan akhir pengamatan H, catat satu terminal outcome per tugas: `ON_TIME`, `LATE_SUCCESS`, atau `FAILED` dengan alasan terpisah. Penolakan/timeout tidak dihitung dua kali dalam numerator yang sama.

### 16.1 Metrik fisik

- Latensi mean, median, dan p95 untuk tugas selesai; jumlah kegagalan selalu disertakan. Jika tidak ada tugas selesai, latensi tersebut `N/A`, bukan nol.
- Energi total Joule, energi idle/dinamis dan breakdown komponen; Joule per tugas datang serta per tugas selesai. Jika tidak ada tugas selesai, Joule per keberhasilan `N/A`.
- Violation = `(Nlate + Nfailed)/N`; laporkan juga persen.
- Reliability = `Nsuccess/N`, dengan `Nsuccess = Nontime + Nlate`.
- Throughput = jumlah hasil diterima/H; jumlah task yang selesai selama 0–T dan T–H disajikan terpisah.
- Utilisasi CPU, backlog, rejection, timeout, serta utilisasi/queue jaringan dicatat sebagai diagnostik.

### 16.2 Lima biaya untuk evaluasi kompromi

| Biaya | Definisi | Acuan |
|---|---|---|
| zL | Rata-rata latensi efektif seluruh tugas / 9 s | Tugas selesai memakai latensi aktual; tugas gagal mendapat penalti 9 s |
| zE | `(Etotal - Eidle) / (50 J × N)` | Eidle = H × jumlah daya idle seluruh komponen |
| zD | `(Nlate + Nfailed)/N` | 0 ideal, 1 seluruh tugas tidak tepat waktu |
| zB | `integral_0^H std(uF1,...,uF5) dt / (H × sqrt(0.24))` | Simpangan baku populasi, bukan estimator sampel |
| zQ | `Nfailed/N = 1 - reliability` | 0 ideal, 1 seluruh layanan gagal |

- Pada konfigurasi utama, latensi sukses tidak melebihi 9 s. Penalti 9 s pada tugas gagal adalah **konvensi evaluasi**, bukan latensi yang terukur. Laporkan keduanya terpisah agar rejection tidak memperoleh nilai latensi nol.
- Untuk lima utilisasi antara 0 dan 1, batas simpangan baku populasi adalah `sqrt(0.24) ≈ 0.489898`. B diintegrasikan per interval event, bukan dirata-ratakan tanpa bobot waktu.
- Beban masing-masing fog adalah fraksi kapasitas node tersebut. Node besar boleh menerima lebih banyak pekerjaan pada utilisasi yang sama.
- Angka 50 J/task merupakan batas skala dinamis sintetis yang konservatif: maksimum CPU dan komunikasi tugas pada tabel utama sekitar 46,06 J tanpa antrean. Menunggu tidak menambah daya dinamis pada model ini; idle sudah dihitung terpisah.
- Pengurangan Eidle adalah perubahan titik acuan yang sama untuk semua metode pada trace/topologi identik. Evaluasi tetap meminimalkan total energi; seluruh Etotal wajib dilaporkan agar persentase penghematan tidak dibesar-besarkan dengan hanya menampilkan energi dinamis.
- N dan trace lengkap hanya dipakai evaluator/normalizer reward; policy tidak menerima jumlah kedatangan masa depan atau isi trace masa depan. Ini protokol pembelajaran berbasis trace offline, bukan klaim observasi masa depan tersedia di deployment.
- N=0 ditolak pada pemeriksaan trace sebelum eksperimen, dengan error tercatat; tidak ada pembagian nol atau resampling diam-diam.
- Jangan memakai min/max dari test atau melakukan normalisasi berbeda per metode. Nilai di luar rentang dicatat tanpa clipping. Jika terjadi pada konfigurasi utama, validasi model harus dihentikan dan penyebabnya diperiksa.
- Pada sensitivitas yang mengubah k/daya, skala acuan utama tetap sama; z > 1 diperbolehkan dan diberi penanda out-of-reference. Hasil sensitivitas tidak dipakai menyesuaikan normalisasi utama.
- zD dan zQ terkait: kegagalan juga pelanggaran deadline. Ini pilihan penalti untuk membedakan kegagalan layanan dari selesai terlambat, **bukan lima variabel yang diasumsikan independen**. Penalti zL untuk gagal menambah konsekuensi evaluasi; dampaknya diperiksa pada sensitivitas normalisasi.

### 16.3 Agregasi

Hitung z per trace, lalu mean antar-trace di setiap workload. Empat workload mendapat bobot sama 1/4, meskipun heavy menghasilkan lebih banyak tugas. F adalah mean lima-biaya lintas workload tersebut, kemudian `Dglobal = sqrt(sum(Fj²)/5)`.

Normalisasi energi terhadap N dan macro-average workload adalah preferensi evaluasi yang ditetapkan di awal: workload dengan jumlah tugas besar tidak otomatis mendominasi skor gabungan. Ini berbeda dari menjumlahkan seluruh Joule lintas semua workload. Pada satu trace tetap, zE merupakan transformasi affine Etotal sehingga urutan energi antarmetode tetap sama.

Laporkan Dglobal sebagai metrik utama, Dw per workload, kelima biaya, metrik fisik, dan workload terburuk. Dglobal tidak menggantikan tabel trade-off. Jangan memakai jumlah reward episode sebagai metrik pembanding antar-bobot.

## 17. Siklus Gymnasium dan integrasi event engine

- `reset` membuat simulasi baru, menjalankan engine sampai kedatangan pertama, lalu mengembalikan observasi tugas yang sedang menunggu keputusan.
- Satu `step(action)` memberikan **satu keputusan offloading untuk satu kedatangan tugas**, termasuk tugas yang nantinya ditolak. Semua metode tetap memutuskan untuk setiap arrival.
- Setelah keputusan, CloudSim memproses event sampai arrival berikutnya; completion/timeout di antaranya tetap dieksekusi. Setelah arrival terakhir, step terakhir menyelesaikan drain sampai H.
- Pada H: `terminated=True`, `truncated=False`; timeout individual bukan akhir episode. Kegagalan program atau putus socket tidak diubah menjadi terminal episode yang terlihat berhasil.
- Tujuh aksi: 0 = IoT asal; 1–5 = F1–F5; 6 = cloud. Tidak ada action masking pada kondisi queue penuh, karena admission berlangsung pada saat input tiba; semua aksi tetap memiliki outcome yang jelas.
- Clock simulasi berhenti maju saat controller menunggu aksi Python. Waktu inferensi/RPC tidak otomatis ditambahkan ke latensi fisik; ukur terpisah dan sediakan analisis overhead bila diperlukan.
- Satu JVM memiliki satu simulasi aktif karena state statis CloudSim. Paralelisme memakai JVM/port terpisah; tidak menjalankan episode paralel melalui singleton yang sama.
- Server memakai node/host/VM/Cloudlet nyata di engine. Jangan hanya mengintegrasikan clock CloudSim sambil tetap menghitung semua outcome dengan rumus transisi custom.
- Outcome masa depan tidak boleh digunakan untuk membentuk state atau menjalankan greedy oracle. Estimasi berbasis queue saat ini diberi label estimasi dan tidak dipakai sebagai hasil simulasi.

### 17.1 Observasi awal: 108 fitur

Urutan node selalu `[IoT asal,F1,F2,F3,F4,F5,cloud]`. Model lama 46 fitur tidak dapat digunakan langsung.

| Blok | Jumlah | Isi |
|---|---:|---|
| Komputasi per node | 7 × 9 = 63 | Busy-PE fraction; q/Qwait; waktu sampai PE pertama bebas; queued MI/total MIPS; MIPS/PE; jumlah PE; tambahan Joule/MI CPU; total remaining MI running+queued/total MIPS; minimum sisa waktu deadline task aktif/menunggu |
| Jalur per tujuan | 7 × 4 = 28 | Estimasi delay input; estimasi delay hasil balik; bottleneck bandwidth; estimasi energi dinamis komunikasi |
| Tugas | 8 | MI, input, output, deadline relatif, timeout relatif, one-hot tiga kelas |
| Lokasi sumber | 5 | One-hot fog akses |
| Global | 4 | t/T; EMA laju arrival; rata-rata utilisasi CPU 100 IoT; selang sejak keputusan sebelumnya |

- Skala langsung: MIPS/PE dibagi 5600; PE dibagi 8; MI dibagi 3000; input dibagi 2,2 MiB; output dibagi 0,11 MiB; deadline dibagi 3 s; timeout dibagi 9 s; bandwidth dibagi 1 Gbps; CPU incremental Joule/MI dibagi 0,02.
- Besaran nonnegatif yang dapat melampaui acuan memakai `x/(x+r)`: waktu/backlog/selang keputusan dengan r=9 s; laju arrival dengan r=35/s; estimasi energi komunikasi dengan r=5 J.
- Sisa deadline dapat negatif: transform `x/(abs(x)+3 s)`; nilai sentinel ketika node kosong = 1, dapat dibedakan melalui u=0 dan q=0.
- EMA arrival memakai konstanta waktu 5 s dan hanya arrival yang sudah diamati: dari nilai awal nol, pada arrival baru `ema = ema_previous × exp(-delta_t/5) + 1/5`. Tidak membaca laju fase berikutnya. t/T berada pada 0–1 saat keputusan dibuat.
- Prediksi delay input/hasil menjumlahkan serialization task, propagasi, dan residual/queued bytes yang sudah ada di setiap server link jalur terkait. Prediksi hasil memakai kondisi queue saat ini, bukan queue masa depan. Jalur lokal mempunyai empat fitur jaringan nol.
- Seluruh metode menerima snapshot publik yang sama. Heuristik boleh memakai versi mentah sebelum transformasi, tetapi tidak memperoleh daftar job atau jadwal event tersembunyi yang tidak diberikan kepada PPO. Semua nilai snapshot mentah disimpan untuk audit.
- Tidak memasukkan label workload, seed, bobot reward, future arrival, target hasil, atau ID perangkat mentah ke policy. Bobot reward tetap untuk satu policy yang dilatih.
- Ini observasi agregat; tidak diklaim merupakan state Markov lengkap karena tidak memuat seluruh daftar tugas/transfer dan deadline. Sifat observabilitas parsial serta penggunaan MLP feed-forward harus disebut sebagai asumsi/batasan. Recurrent policy bukan bagian v0.2.

## 18. Reward: lima komponen dan hasil yang tertunda

Jangan memberi reward menggunakan outcome prediksi seolah-olah tugas sudah selesai. Gunakan kejadian aktual antara dua waktu keputusan.

Definisikan cumulative cost Cj(t) sehingga pada H nilainya sama dengan zj di bagian 16:

- CL bertambah ketika tugas mencapai outcome terminal, sebesar latensi efektif/(9N).
- CE bertambah sesuai energi dinamis interval/(50N).
- CD bertambah 1/N saat deadline pertama kali terlewati, atau saat gagal bila belum pernah dihitung. Maksimum satu kali per tugas.
- CB bertambah sesuai integral ketimpangan interval dibagi `H sqrt(0.24)`.
- CQ bertambah 1/N saat tugas gagal; tidak bertambah pada late success.

Reward satu transisi: `r = -100 × sum_j(wj × [Cj(tnext)-Cj(t)])`.

- Faktor 100 sama untuk semua bobot/metode/trace. Tidak ada bonus tersembunyi, penalti di luar lima komponen, atau clipping reward.
- Reward terkait completion dapat diterima beberapa keputusan setelah aksi penyebabnya. Bagian drain dimasukkan pada transisi terakhir, bukan dibuang.
- Dengan discount 1, total reward episode harus tepat `-100 × sum(wj zj)` dalam toleransi numerik. Identitas ini menjadi acceptance test.
- Tidak menggunakan total reward sebagai pembanding kualitas antar-policy dengan bobot berbeda; pembanding tetap Dglobal dan metrik bersama.
- Tidak ada reward normalization adaptif yang berbeda antar-run. Normalisasi advantage PPO tetap diperbolehkan dan sama untuk semua metode.

## 19. PPO dan strategi training

### 19.1 Konfigurasi awal

| Parameter | Nilai |
|---|---|
| Policy | MLP actor dan critic terpisah, masing-masing 128–128, Tanh |
| Action/observation | Discrete(7), vektor 108 fitur |
| Device | CPU |
| Environments per model | 1 |
| Learning rate | 3e-4, konstan |
| n_steps | 512 keputusan |
| batch_size | 128 |
| n_epochs | 10 |
| gamma | 1,0; objektif episodik tanpa diskonto antar-arrival |
| gae_lambda | 0,95 |
| clip_range | 0,2 |
| ent_coef | 0,01, konstan |
| vf_coef | 0,5 |
| max_grad_norm | 0,5 |
| target_kl | 0,03 |
| normalize_advantage | True |
| Evaluasi policy | Deterministic argmax |
| Torch threads | 1 per worker; interop 1 |

Gamma 1 dipilih agar perubahan jarak waktu antar-arrival tidak otomatis mengubah preferensi objektif melalui diskonto per-keputusan. GAE tetap estimator aproksimasi; konvergensi diperiksa pada pilot. Tidak ada early stopping berdasarkan hasil test.

### 19.2 Satu policy untuk empat workload

Untuk setiap bobot, model dilatih pada campuran episode light/moderate/heavy/dynamic dengan urutan round-robin dan offset awal seimbang. PPO tidak menerima label workload. Kandidat dan policy akhir memakai pola campuran yang sama, tetapi trace/seed training terpisah. Karena episode heavy lebih panjang, jumlah keputusan per workload tidak sama; ini dicatat. Evaluasi dan pemilihan solusi menggunakan macro-average sama penting antar-workload.

Offset kandidat pada outer run r, model repeat m adalah `(r+m) mod 4`; offset policy akhir `r mod 4`. Urutan dasar `[light,moderate,heavy,dynamic]`. Counter episode/trace tidak digambar ulang karena perubahan aksi; semua metode pada peran training yang sama memakai stream eksternal yang sama.

Tujuan keputusan ini adalah menilai satu konfigurasi bobot/kebijakan yang bekerja pada empat profil, mengurangi pencarian ulang identik, dan memungkinkan pengujian adaptasi state. Ini berbeda dari empat model khusus workload pada batch lama. Klaim generalisasi tetap terbatas pada distribusi yang diuji.

| Tahap | Anggaran aktual yang direncanakan |
|---|---:|
| Smoke test | 512 keputusan/model; untuk jalur teknis saja |
| Pilot utama | 10.240 keputusan/model |
| Kandidat awal K | 5.120 keputusan/model, sekitar 5.000 |
| Referensi ranking kandidat pada pilot | 51.200 keputusan/model |
| Training akhir utama F | 102.400 keputusan/model |
| Sensitivitas training akhir | Checkpoint 51.200 dari lintasan training yang sama |

Semua angka adalah kelipatan rollout 512. Jangan menyebut 5.120 persis 5.000 atau membandingkan jumlah timestep yang hanya diminta. Training budget berhenti setelah update yang sesuai; task unresolved pada rollout terakhir dicatat, tidak dimasukkan sebagai keberhasilan palsu. Evaluasi selalu memakai episode lengkap.

## 20. Pencarian bobot dan baseline

### 20.1 Ruang bobot

Urutan bobot `[latency,energy,deadline,imbalance,reliability]`. Gunakan simplex `sum(w)=1` dan `wj >= 0.02`. Batas bawah mencegah objektif training hilang sepenuhnya; tidak menyatakan kepentingan evaluasinya berubah. Maksimum satu bobot = 0,92.

- Equal = `[0.20,0.20,0.20,0.20,0.20]`.
- Manual = `[0.30,0.15,0.25,0.10,0.20]`, suatu baseline tetap yang menekankan respons/deadline. Ini pilihan desain pembanding, bukan bobot aplikasi yang diklaim optimal.
- Sampling uniform pada simplex berbatas: `w = 0.02 + 0.90 × Dirichlet(1,1,1,1,1)`.
- Repair crossover/mutation memakai proyeksi ke simplex berbatas tersebut; bukan clipping yang membiarkan jumlah bobot berubah.

### 20.2 NSGA-II dan random search

| Parameter | Keputusan |
|---|---|
| Populasi NSGA-II | 20 |
| Generasi termasuk populasi awal | 4 |
| Evaluasi kandidat | 80 training-evaluation bundles |
| Crossover | SBX, probability 0,9, eta 15 |
| Mutation | Polynomial, probability 1 per kandidat, probability 1/5 per variabel, eta 20 |
| Survival | Nondominated sorting dan crowding distance |
| Candidate PPO repeats | 2 seed training per bobot |
| Candidate budget | K, awal 5.120, ditetapkan lewat gerbang ranking fidelity pada pilot |
| Validasi kandidat | 5 trace/workload/model; total 40 episode per bobot dengan dua model |

Populasi awal memasukkan equal dan manual plus 18 sampel simplex. Random search memakai 20 titik awal yang sama, lalu 60 sampel simplex independen. RNG titik awal = `300000+r`, RNG variasi NSGA-II = `400000+r`, dan RNG tambahan random search = `500000+r`. Kedua pencarian menghabiskan 80 slot evaluasi. Duplikasi bobot tidak di-cache gratis: evaluasi ulang tetap memakai slot dan dicatat, agar biaya tidak diam-diam berbeda. Simpan archive nondominated dari seluruh kandidat yang dievaluasi, bukan hanya populasi terakhir.

Masing-masing bobot memperoleh dua PPO baru dari awal dengan seed dan stream training yang sama antar-bobot dalam satu outer run. F kandidat adalah mean z lintas dua model, trace validasi, dan empat workload; NSGA-II meminimalkan kelima komponennya. Pilih minimum D dari archive nondominated menggunakan mean F tersebut. Random search memakai archive dan aturan seleksi sama. Model akhir selalu dilatih ulang dari awal, bukan warm-start dari kandidat terbaik.

Toleransi D seri = 1e-9. Tie-break: (1) mean failure lebih kecil; (2) violation lebih kecil; (3) tuple bobot secara leksikografis. Tie-break hanya dipakai untuk nilai D yang sama dalam toleransi, bukan mengubah preferensi utama.

NSGA-II pada lima objektif bukan jaminan mencapai Pareto optimum global. Karena tekanan dominasi dapat lemah, random search beranggaran sama adalah pembanding wajib. Catat hypervolume validasi sebagai hasil sekunder dengan reference point `[1.1,1.1,1.1,1.1,1.1]`, normalisasi tetap, dan algoritma yang sama. Jika titik utama keluar batas yang dirancang, jangan mengganti reference point setelah melihat hasil. Hypervolume kandidat bukan hypervolume policy akhir yang telah dilatih lebih lama.

### 20.3 Heuristik praktis

- **Least Fog**: pilih fog dengan estimasi waktu pengosongan pekerjaan `(remaining_MI_running + queued_MI)/total_MIPS` terkecil. Tie: jalur transfer lebih singkat, lalu ID node. Hanya mempertimbangkan lima fog, tanpa rerouting saat admission gagal.
- **Greedy-EFT** ditambahkan sebagai pembanding kuat: pilih di antara tujuh tujuan berdasarkan perkiraan waktu hasil diterima paling awal dari snapshot publik. Tidak memakai future arrival; tidak ada oracle jadwal job tersembunyi.
- Untuk tujuan j, gunakan prediksi input Tin dan hasil Tout dari fitur jalur. Estimasi antrean CPU saat input tiba adalah `W = max(0, earliest_PE_free_delay + queued_MI/total_MIPS - Tin)`. Skor EFT = `Tin + W + MI/MIPS_per_PE + Tout`. Ini pendekatan berbasis statistik queue, bukan prediksi outcome pasti. Pilih skor terkecil tanpa mask admission. Queue masa depan tidak dibaca dan kapasitas tidak direservasi. Tie waktu 1e-9 s memakai ID tujuan terkecil.
- Always-local dan nearest-fog dipakai untuk validasi/kalibrasi, bukan dasar tunggal klaim superioritas metode.

## 21. Anggaran eksperimen dan efisiensi

Anggaran utama adalah jumlah keputusan lingkungan **training + validasi pencarian + training akhir**. Setiap tugas datang tetap menghasilkan keputusan meskipun ditolak. Test akhir adalah biaya pengukuran bersama, dilaporkan terpisah dan tidak digunakan untuk melatih baseline.

Untuk satu pencarian pada satu outer run:

- Training kandidat `S = 80 × 2 × K`; dengan K=5.120, S=819.200 keputusan.
- Validasi kandidat `V = 80 × 2 × sum(Ntrace)` untuk 20 trace validasi yang sama, yaitu lima trace per workload.
- Training akhir F=102.400 keputusan.
- Total `Csearch_method = S + V + F`. Validasi tidak dianggap gratis.
- Baseline total-budget memakai `B = 512 × ceil(Csearch_method/512)` keputusan training. Selisih pembulatan paling banyak 511 keputusan, dilaporkan sebagai toleransi satu rollout.

Jumlah Ntrace dihitung sebelum eksperimen dari trace validasi, sehingga B tidak bergantung pada algoritma yang menang atau hasil test. NSGA-II dan random search mempunyai jumlah evaluasi dan trace yang sama, sehingga kuota interaksinya sama.

**Konsekuensi sumber daya:** berdasarkan ekspektasi arrival pada tabel, 20 trace validasi memuat sekitar 19.500 tugas. V sekitar 3.120.000 keputusan dan B sekitar **4.041.728 keputusan per baseline total-budget**, bukan 102.400. Angka aktual bergantung pada Ntrace. Ini biaya yang disengaja untuk pembandingan total yang memasukkan validasi. Runner nantinya harus menampilkan estimasi ini sebelum batch; pilot tidak langsung menjalankan seluruh 20 run. Jika sumber daya tidak memadai, revisi anggaran/ukuran studi melalui versi protokol baru sebelum test, bukan menghapus biaya validasi dari laporan.

| Protokol | Perbandingan utama |
|---|---|
| A — F sama | NSGA-II+PPO(F), Random+PPO(F), PPO-Equal(F), PPO-Manual(F) |
| B — Total sama | NSGA-II+PPO(S+V+F), Random+PPO(S+V+F), PPO-Equal(B), PPO-Manual(B) |

Pencarian dan model akhir metode search boleh dipakai kembali pada analisis A dan B; jangan membebankan biaya pencarian dua kali untuk satu hasil yang sama. Equal/manual dapat dilatih sampai B dengan checkpoint pada F dan 51.200, karena learning rate dan entropy konstan; implementasi harus memvalidasi bahwa checkpoint F identik dengan training berhenti pada F untuk seed/stream yang sama. Jika tidak identik, latih terpisah dan catat biaya studi tambahan.

Waktu wall-clock, CPU time, jumlah gradient updates, RSS peak, waktu inferensi, RPC, startup, serta simulasi per episode dilaporkan. Sampling, validasi, dan evaluasi dicatat terpisah. Pengembangan, pilot, dan kalibrasi tidak dimasukkan diam-diam ke biaya deployment salah satu metode; laporkan totalnya sebagai biaya penelitian tambahan.

## 22. Seed, data split, dan reproduksibilitas

| Komponen | Keputusan |
|---|---|
| Master experiment seed | 20261103 |
| Outer run training | 20 run: r=0–19; semuanya wajib dilaporkan |
| Smoke/pilot | Namespace terpisah; outer pilot r=100,101,102, tidak masuk hasil konfirmatori |
| Kalibrasi fisik | 20 trace/workload, ID 0–19, namespace calibration |
| Validasi pencarian | Trace ID 10000–10004 per workload |
| Test final | Trace ID 20000–20099 per workload; dikunci sampai protokol final |
| Seed inisialisasi dua kandidat pada run r | 200000+2r dan 200001+2r |
| Seed inisialisasi policy akhir pada run r | 100000+r, sama antar-metode yang dibandingkan |

Trace generator Python memakai PCG64 dengan seed yang diturunkan dari SHA-256 atas tuple `(master, split, outer_run_if_training, model_repeat_if_training, trace_id, workload, component)`. Tentukan byte encoding UTF-8, separator `|`, dan unsigned 64-bit dari delapan byte pertama digest dalam little-endian. Komponen RNG dipisah untuk arrival, source, class, MI, data, dan deadline. Trace ekspor adalah sumber kebenaran; Java memutar ulang trace, tidak menggambar ulang tugas dengan RNG yang berbeda.

Nama split baku: `calibration`, `pilot_train`, `pilot_validation`, `train_candidate`, `train_final`, `validation`, dan `test`. Field outer/model repeat yang tidak digunakan diisi literal `-`, bukan dihilangkan. Component baku: `arrival`, `source`, `class`, `cpu_mi`, `input_bytes`, `deadline`. Pilot validation memakai ID 10000–10004 per workload pada namespace pilot, sehingga terpisah dari validasi pencarian utama walaupun nomor ID sama. Stream final sama antar-metode dalam satu outer run; nama metode tidak dimasukkan ke seed trace final.

- Training kandidat memakai stream yang sama antar-bobot untuk model repeat yang sama; final memakai namespace berbeda. Policy tidak diberi seed sebagai input.
- Test trace yang sama digunakan untuk semua metode dan outer run. Ini menahan variasi skenario; tidak berarti episode menjadi training replicate independen.
- Namespace workload berbeda; moderate/dynamic harus lolos pemeriksaan bahwa trace bukan duplikat dan memiliki profil waktu yang benar.
- Satu set test tidak dipakai sebagai validasi setelah hasilnya dilihat. Jika rancangan diubah berdasarkan test, set berikutnya menjadi evaluasi baru yang dipisahkan dan diberi versi.
- Simpan lock dependency beserta hash paket yang benar-benar berhasil diuji, versi OS/CPU, Python 3.12.x, OpenJDK 21.x, Git SHA, SHA-256 source/JAR, trace, dan konfigurasi. Versi patch dependency ditetapkan dari lingkungan yang lolos validasi, bukan diasumsikan kompatibel tanpa uji.
- Default satu worker. Eksekusi server besar boleh empat worker independen dengan port 5555–5558, masing-masing satu JVM, satu proses training, dan satu Torch thread; jangan membandingkan wall-clock paralel dan serial tanpa pelabelan.

## 23. Analisis statistik yang ditetapkan sebelumnya

Unit utama adalah **outer training run**, bukan tiap task atau episode. Untuk setiap run, rata-ratakan trace per workload, macro-average workload, lalu hitung Dglobal. Pertahankan pairing seed dan trace antar-metode.

Tiga perbandingan primer, satu keluarga Holm dengan alpha 0,05:

1. RQ1: Dglobal NSGA-II versus PPO-Equal pada F sama.
2. RQ2: Dglobal NSGA-II versus Random Search pada anggaran pencarian/final sama.
3. RQ3: Dglobal NSGA-II versus PPO-Equal pada total budget sama.

- Pakai paired sign-flip dua sisi terhadap 20 selisih outer-run; enumerasi exact 2^20 pembalikan tanda. Nyatakan asumsi exchangeability/sign symmetry selisih di bawah null; jangan menganggap pairing menjamin asumsi tersebut.
- Laporkan raw p, Holm-adjusted p, selisih bertanda `Dcomparator - DNSGA`, dan interval kepercayaan. Nilai positif berarti NSGA lebih baik.
- Interval 95% memakai 10.000 bootstrap berpasangan dua tingkat/crossed: resample outer-run indices dan trace indices per workload; trace indices yang terambil dipakai bersama pada semua model/run yang terpilih. Hitung ulang normalisasi/agregasi yang tetap, bukan hanya mengambil mean p-value. Simpan RNG seed bootstrap 20261105.
- Untuk effect size opsional, laporkan paired dz bertanda beserta definisinya. Bila SD selisih nol tetapi mean tidak nol, tandai undefined, jangan menggantinya dengan nol.
- Perbandingan sekunder lima biaya × empat workload × tiga pasangan primer = 60 hipotesis, dikoreksi Holm sebagai keluarga sekunder tersendiri. Uji sign-flip Monte Carlo 100.000 draws dengan correction `(b+1)/(M+1)` dan seed tetap 20261106. Seluruh 60 hasil dilaporkan, bukan hanya yang signifikan.
- Manual, heuristik, sensitivitas, dan perbandingan lain dilaporkan sebagai analisis sekunder/eksploratif beserta effect/CI. Jangan menggabungkannya sebagai bukti konfirmatori tanpa mendaftarkan keluarga hipotesis tambahan sebelum test.
- Tidak ada fallback otomatis dari Wilcoxon ke t-test, pemilihan satu sisi setelah melihat arah, atau penambahan seed sampai signifikan.
- Dua puluh seed adalah rencana sumber daya dan peningkatan replikasi, bukan jaminan daya uji/penerimaan jurnal. Tidak signifikan berarti bukti belum cukup; kesetaraan memerlukan margin dan protokol tersendiri.
- Makna praktis: laporkan Dglobal absolut/relatif, Joule total, poin persentase violation/reliability, dan biaya tambahan. Ambang screening pelaporan yang dipilih adalah perbaikan relatif Dglobal ≥1%; ini konvensi studi, bukan SLA atau bukti otomatis bahwa manfaat cukup bagi aplikasi nyata.

## 24. Pilot dan gerbang sebelum eksperimen utama

### 24.1 Validasi deterministik

| Kasus | Kriteria penerimaan |
|---|---|
| Satu tugas, CPU kosong | Waktu CPU = MI/MIPS per PE dalam toleransi max(1e-6 s, 1e-4 relatif) |
| Dua/lebih tugas FCFS | Urutan benar, PE tidak melebihi kapasitas, task tidak menyalip antrean |
| Transfer satu link | Waktu = serialization + propagasi; contoh 1 MiB pada 20 Mbps = 0,4194304 s serialization |
| Transfer multihop | Setiap hop, queue, hasil balik, dan energi terhitung sekali |
| Queue penuh | Tepat satu penolakan/outcome, resource/denominator konsisten |
| Deadline versus timeout | Hasil terlambat tetap sukses; timeout membatalkan pekerjaan; batas timestamp konsisten |
| Idle 69 s | Energi = total Pidle × 69; tidak nol, tidak dihitung dua kali |
| Timeout saat transfer/CPU | Energi parsial dihitung; event lama tidak menghidupkan task kembali |
| Konservasi task | N = Nontime + Nlate + Nfailed; tidak ada task unresolved pada H |
| Identitas reward | Jumlah reward = -100 sum(wj zj), toleransi 1e-8 absolut atau 1e-6 relatif |
| Replay | Trace + policy deterministik + seed identik menghasilkan event/outcome/energi identik; wall-clock boleh berbeda |

### 24.2 Kalibrasi model

Jalankan always-local, nearest-fog, Least Fog, dan Greedy-EFT pada 20 trace kalibrasi per workload, tanpa memakai ERWO untuk memilih skenario.

Gerbang:

- Distribusi empiris MI/data/deadline dan arrival count konsisten dengan konfigurasi; dynamic menunjukkan empat fase yang benar dan tidak identik dengan moderate.
- Dalam perhitungan solo-task tanpa antrean, ≥95% tugas mempunyai sekurangnya satu rute yang dapat memenuhi deadline. Jika gagal, masalah mungkin infeasible secara struktural dan harus diperiksa sebelum belajar.
- Heavy menunjukkan tekanan resource terukur pada sedikitnya satu baseline referensi; pada sedikitnya satu kondisi heavy ada kegagalan >1% tetapi reliability tetap >50%, agar QoS tidak seluruhnya konstan atau seluruh layanan runtuh.
- Jangan menjadikan urutan kemenangan metode sebagai kriteria kalibrasi. Jika gerbang gagal, hentikan dan revisi parameter melalui alasan model yang tercatat; buat versi konfigurasi baru dan ulangi kalibrasi. Tidak ada penyesuaian otomatis berulang sampai ERWO menang.

### 24.3 Pilot learning dan fidelity kandidat

- Tiga outer pilot seed, workload campuran, anggaran 10.240 untuk smoke learning; periksa finite loss, action histogram, queue, outcome, dan reward.
- Uji delapan bobot yang ditetapkan sebelum pilot: equal, manual, lima titik dengan 0,92 pada masing-masing objektif dan 0,02 pada lainnya, serta satu sampel simplex dengan seed 20261107.
- Bandingkan ranking D validasi pada K=5.120 dengan referensi 51.200 keputusan, memakai dua training seed dan data validasi pilot terpisah.
- Pada masing-masing dari tiga outer pilot, ranking dihitung dari mean dua model per bobot; ties memakai average rank. Gerbang fidelity: median tiga korelasi Spearman minimal 0,60 dan tidak ada korelasi negatif. Jika belum tercapai, ulangi pada K=10.240, lalu 20.480; pilih K terkecil yang lulus. Jika semuanya gagal atau ranking tak terdefinisi karena semua policy identik, berhenti untuk diagnosis, jangan menjalankan batch konfirmatori.
- Prosedur ini memilih resolusi kandidat, bukan membuktikan konfigurasi global optimal. Semua biaya pilot dicatat dan tidak dicampur ke hasil test utama.
- Setelah lulus, bekukan K, spesifikasi, dependency lock, normalisasi, dan protokol statistik sebelum test dibuka.

## 25. Sensitivitas dan batas interpretasi

Eksperimen utama menggunakan parameter default. Analisis tambahan satu faktor per waktu memakai model utama yang sudah dibekukan, tanpa pencarian ulang, untuk menilai robustness zero-shot:

- Faktor timeout k = 2 dan 4 dibanding default 3; H mengikuti rumus dan sama antar-metode dalam skenario itu.
- Kapasitas antrean fog = 8 dan 32 dibanding default 16.
- Propagasi WAN = 10 dan 40 ms satu arah dibanding default 20 ms.
- Tambahan daya dinamis seluruh komponen ×0,75 dan ×1,25; idle tidak berubah.
- Daya fog homogen pada kapasitas heterogen untuk memisahkan sensitivitas kapasitas dari profil energi.
- Rehitung ranking pada **data validasi** dengan acuan penalti latensi gagal dan skala energi ±20%, tanpa memilih hasil test yang paling menguntungkan. Definisi utama tetap dilaporkan.

Kondisi homogen adalah kontrol validasi; hasil utama heterogen. Analisis dengan training ulang per skenario, perubahan jumlah perangkat/node, recurrent policy, NSGA-III, atau adaptasi bobot online bukan bagian wajib v0.2 dan harus menjadi protokol baru jika ditambahkan.

## 26. Artefak, monitoring, resume, dan batas run

Rancangan implementasi harus menulis:

- `protocol.json`, `system.yaml`, `training.yaml`, dan dependency lock dengan versi/hashes.
- Trace manifest dan hash setiap trace; training/validation/test tidak bercampur.
- Task log: ID, source, kelas, arrival/deadline/timeout, action, jalur, admission, start/end CPU, hasil diterima, terminal outcome, alasan gagal, dan energi dinamis teratribusi.
- Event/resource ledger: utilisasi, queue, byte transfer, cancellation, dan integral energi/imbalance.
- Candidate archive: bobot, seed, seluruh lima biaya, D, slot evaluasi, biaya aktual, dan model checkpoint.
- Model final, metrik per-trace/per-run, bootstrap/test output, serta laporan agregat dengan mean/SD/CI antar-run.
- Status `pending/running/complete/failed/interrupted`; result baru ditandai complete setelah semua artefak dan invariants valid.

Setiap run terisolasi. Resume hanya melanjutkan bagian belum selesai pada konfigurasi/source/build/trace hash yang sama; tidak menimpa hasil lama. Checkpoint partial training harus menyimpan optimizer, RNG, penghitung, simulator, pending task, dan urutan trace. Jika state lengkap tidak tersedia, run yang terputus diulang dari awal dengan label attempt; jangan mengklaim resume identik.

Kegagalan teknis boleh dicoba ulang maksimal dua kali setelah attempt awal, dengan seed/trace yang sama dan alasan tercatat. Nonfinite loss atau kegagalan algoritmik tidak diganti dengan seed yang lebih mudah. Batch dihentikan untuk diagnosis jika hasil valid tidak dapat diperoleh; analisis primer lengkap menunggu seluruh 20 run yang direncanakan, dan daftar kegagalan tetap disertakan.

Socket memakai JSON Lines dengan versi protokol, request ID, episode ID, schema/observation dimension, dan handshake hash simulator/config. Java wajib; tidak ada fallback Python. Connect/read wall-clock timeout awal 120 s, progress heartbeat 10 s; timeout komunikasi adalah kegagalan teknis, bukan QoS task. Angka wall-clock dapat dinaikkan melalui konfigurasi sebelum run jika server lambat, dengan log perubahan.

Dashboard dimatikan pada pengukuran performa. Warm-up inferensi 1.000 pemanggilan, lalu ukur 10.000 observasi tersimpan yang sama per metode pada CPU thread sama. Simpan median/p95 dan mean; pisahkan inferensi murni dari RPC. Jangan menyimpulkan efisiensi deployment hanya dari waktu forward pass.

## 27. Urutan implementasi setelah dokumen disetujui

1. Bekukan v0.2 sebagai protokol awal dan arsipkan suite lama; tidak memodifikasi atau mengganti label hasil lama.
2. Implementasikan event engine minimum, satu tugas, satu rute, clock, dan cancellation; lulus validasi deterministik.
3. Tambahkan resource bounded, jaringan, serta ledger energi dan metric invariants.
4. Tambahkan generator trace dan empat workload; jalankan kalibrasi model.
5. Tambahkan Gymnasium 108 fitur, reward lima komponen, serta baseline deterministik.
6. Tambahkan PPO, simplex search NSGA-II/random search, accounting biaya, dan pilot fidelity.
7. Bekukan konfigurasi hasil pilot, lalu jalankan 20 outer run konfirmatori dan analisis yang sudah ditetapkan.
8. Lakukan sensitivitas, arsip reproduksibilitas, dan penulisan manuskrip dengan batas klaim yang sesuai.

**Belum ada implementasi kode, perubahan hyperparameter runtime, atau eksperimen baru yang dijalankan oleh pembaruan dokumen ini.** Nilai yang ditetapkan adalah keputusan desain untuk ditinjau. Revisi yang dipicu pilot diberi versi dan alasan; hasil negatif tetap dipertahankan.

Penilaian kebaruan terhadap studi reward-weight optimization/MORL terdekat tetap harus diselesaikan sebelum klaim state of the art atau pemilihan target jurnal. Spesifikasi yang rinci maupun jumlah seed tidak menjamin penerimaan publikasi.

## 28. Rujukan dan jejak keputusan

- [Publikasi iFogSim2](https://clouds.cis.unimelb.edu.au/papers/iFogSim2.pdf): konteks simulator dan skala contoh sumber daya, bukan validasi angka sintetis penelitian ini.
- [DCNSFog.java lokal](ifogsim/src/org/fog/test/perfeval/DCNSFog.java): contoh pembuatan host serta anchor kapasitas dan pasangan daya fog.
- [FogLinearPowerModel.java lokal](ifogsim/src/org/fog/utils/FogLinearPowerModel.java): semantik daya idle yang sesuai kebutuhan model.
- [CloudletSchedulerSpaceShared.java lokal](ifogsim/src/org/cloudbus/cloudsim/CloudletSchedulerSpaceShared.java): titik awal scheduler yang masih memerlukan admission/cancellation dan acceptance test.
- [Dokumentasi PPO Stable-Baselines3](https://stable-baselines3.readthedocs.io/en/master/modules/ppo.html): parameter algoritma, CPU untuk MLP, dan semantik training. Nilai pilihan studi bukan klaim default terbaik pustaka.
- [Dokumentasi NSGA-II pymoo](https://pymoo.org/algorithms/moo/nsga2.html): nondominated sorting/crowding serta operator yang akan dikonfigurasi.
- [Agarwal dkk., NeurIPS 2021](https://proceedings.neurips.cc/paper_files/paper/2021/hash/f514cec81cb148559cf475e7426eed5e-Abstract.html): motivasi pelaporan ketidakpastian antar-training.

Pilihan FCFS, k=3, T=60 s, daya sintetis, normalisasi, penalti kegagalan, bobot manual, matriks seed, anggaran, dan ambang pilot adalah rancangan penelitian pada dokumen ini. Sumber di atas tidak diklaim menetapkan seluruh pilihan tersebut.
