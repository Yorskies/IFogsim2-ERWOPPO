# Rencana penelitian lanjutan ERWO-PPO

Tanggal penyusunan: 3 November 2026.

Dokumen ini merangkum audit percobaan terakhir dan menetapkan urutan penelitian berikutnya. Hasil lama dipertahankan sebagai bukti eksperimen pendahuluan; dokumen ini tidak mengubah hasil, kode, atau konfigurasi training yang sudah dijalankan.

## 1. Keputusan penelitian

**Prioritas berikutnya adalah memperbaiki validitas model dan skenario, kemudian menguji manfaat optimasi bobot dengan pembanding yang adil.** Belum perlu mengulang seluruh matriks dengan timestep lebih besar.

Batch terakhir telah selesai secara teknis. Namun, klaim superioritas umum ERWO-PPO pada empat profil beban iFogSim2 belum didukung oleh bukti yang tersedia. Kesiapan publikasi dinilai dari kontribusi, validitas eksperimen, besarnya manfaat, dan transparansi pelaporan. Penerimaan jurnal Q1 tidak dapat dipastikan dari jumlah eksperimen atau signifikansi statistik saja.

## 2. Dasar evaluasi

Suite yang direview: `results/suite_20261102T151556_158373Z/`.

| Komponen | Hasil audit |
|---|---|
| Percobaan | 80/80 selesai |
| Matriks | 4 workload × 4 anggaran akhir × 5 seed |
| Training kandidat | 5.000 timestep per kandidat |
| NSGA-II | Populasi 10, generasi 4; 40 evaluasi kandidat per run |
| Anggaran akhir | 5.000, 25.000, 50.000, 100.000 timestep |
| Seed training | 0, 1, 2, 3, 4 |
| Evaluasi | 100 episode per metode, seed 1000–1099 |
| Data mentah | 56.000 baris episode benchmark |
| Model | 400 file model tersedia dan tidak kosong; tidak dideserialisasi saat audit |
| Konsistensi agregasi | Rata-rata per-run dan agregat antar-seed cocok dengan sumber data |

Artefak audit lokal:

- [Laporan hasil](results/suite_20261102T151556_158373Z/Data_final.md).
- [Review lengkap](results/suite_20261102T151556_158373Z/Review_final.md).
- [Rincian audit numerik](results/suite_20261102T151556_158373Z/review_audit.json).

Direktori `results/` diabaikan oleh Git. Tautan tersebut memerlukan salinan artefak lokal; arsip hasil harus dibagikan terpisah dari repository kode.

## 3. Temuan yang menentukan langkah berikutnya

### 3.1 ERWO membantu pada training akhir singkat, dengan tambahan biaya pencarian

Pada anggaran akhir 5.000 timestep, ERWO-PPO mengurangi violation terhadap PPO-Equal sekitar **16,21–27,61 poin persentase**, tergantung workload.

Namun, setiap run ERWO terlebih dahulu melatih 40 kandidat × 5.000 timestep. Anggaran training nominal menjadi 205.000 timestep untuk ERWO versus 5.000 untuk PPO-Equal, sebelum memperhitungkan evaluasi dan pembulatan rollout. Pada anggaran akhir 100.000, perbandingannya menjadi 300.000 versus 100.000 timestep.

**Implikasi:** hasil mendukung manfaat optimasi bobot dengan tambahan komputasi. Hasil belum membuktikan efisiensi sampel yang lebih baik.

### 3.2 Keunggulan akhir terhadap PPO-Equal kecil

Violation pada 100.000 timestep, semakin rendah semakin baik:

| Workload | PPO-Equal | ERWO-PPO | Least Fog |
|---|---:|---:|---:|
| Light | 18,00% | 17,85% | **17,44%** |
| Moderate | 17,78% | 17,66% | **17,34%** |
| Heavy | 18,46% | 18,16% | **17,75%** |
| Dynamic | 17,78% | 17,66% | **17,34%** |

Perbaikan ERWO-PPO terhadap PPO-Equal hanya sekitar **0,12–0,30 poin persentase**. Least Fog juga lebih baik pada skor latensi, ketimpangan beban, dan QoS di anggaran ini. Waktu keputusan Least Fog sekitar 0,0025 ms, sedangkan ERWO sekitar 0,095–0,098 ms.

**Implikasi:** jelaskan kondisi yang memerlukan kebijakan belajar dan manfaat praktisnya. Least Fog harus tetap menjadi pembanding utama. Skenario baru perlu berasal dari kebutuhan sistem, bukan dipilih untuk membuat baseline tertentu kalah.

### 3.3 Empat nama workload belum menjadi empat profil beban

Seluruh 20 pasangan anggaran/seed moderate–dynamic menghasilkan bobot, benchmark selain timing, dan CSV episode yang identik. Source Java membedakan panjang episode: light 50, moderate/dynamic 100, heavy 150 langkah. Distribusi tugas belum dibedakan menurut workload.

**Implikasi:** hasil saat ini lebih tepat dibaca sebagai sensitivitas panjang episode. Moderate dan dynamic tidak boleh dianggap dua bukti kondisi berbeda atau digabung sebagai replikasi independen.

### 3.4 Engine socket masih merupakan simulator custom

`IFogSimSocketServer` menghitung transisi state dan metrik melalui rumus custom. Kode tersebut belum menjalankan simulasi offloading melalui event engine CloudSim dan objek `FogDevice`.

**Implikasi:** kompilasi source iFogSim2 dan keberadaan JAR tidak membuktikan bahwa episode PPO menjalankan event engine iFogSim2. Dasar simulator perlu ditentukan sebelum memperluas klaim.

### 3.5 Metrik dan satuan perlu diperjelas

Skor latensi, efisiensi energi, deadline, dan QoS merupakan jumlah sub-reward per episode. Nilai tersebut bukan latensi dalam ms, konsumsi energi dalam Joule, atau persentase efisiensi fisik. Panjang episode berbeda juga mengubah skala jumlah skor.

**Implikasi:** pisahkan reward untuk training dari metrik sistem untuk evaluasi. Jangan memperoleh satuan fisik hanya dengan mengganti judul kolom.

### 3.6 Statistik per-model belum menjawab ketahanan antar-training

Kode menjalankan Wilcoxon atas episode berpasangan dan koreksi Holm atas 20 perbandingan dalam satu run. Ini menilai dua model tertentu pada skenario evaluasi, dengan asumsi uji yang sesuai.

Untuk pertanyaan tentang algoritma ketika dilatih ulang, unit replikasi utamanya adalah seed training. Audit memakai uji paired sign-flip exact dua sisi terhadap lima rata-rata seed ERWO versus PPO-Equal. Nilai p terkecil adalah 0,0625. Dengan lima pasangan terdapat 32 pembalikan tanda; resolusi uji tersebut terbatas.

**Implikasi:** belum ada bukti signifikan antar-seed pada uji audit tersebut. Ini tidak membuktikan kesetaraan. Jangan memperlakukan 5 × 100 episode sebagai 500 training independen, menggabungkan p-value dengan rata-rata, atau mengubah prosedur hanya untuk memperoleh p < 0,05.

### 3.7 Pencatatan teknis perlu dirapikan

Seluruh `result.json` menyimpan snapshot status `running`, sementara manifest, model, dan summary menunjukkan selesai. Terdapat pula variasi antar-seed besar pada DDPG.

**Implikasi:** perbaiki finalisasi metadata dan periksa stabilitas baseline. Kesalahan status ini tidak membatalkan hasil agregat yang sudah diverifikasi. Pemeriksaan stabilitas harus didokumentasikan dan tidak menjadi alasan membuang seed yang buruk.

## 4. Pertanyaan penelitian

| ID | Pertanyaan | Bukti yang diperlukan |
|---|---|---|
| RQ1 | Apakah workload menghasilkan perbedaan beban sistem yang terukur? | Statistik arrival rate, demand komputasi, antrean, utilisasi, serta burst per profil |
| RQ2 | Apakah optimasi bobot meningkatkan PPO dibanding bobot tetap? | Ablation equal/manual/optimized pada konfigurasi dan seed yang sebanding |
| RQ3 | Apakah NSGA-II memberi manfaat melebihi pencarian bobot sederhana? | Random search dengan anggaran pencarian dan protokol validasi sama |
| RQ4 | Apakah manfaat ERWO bertahan ketika biaya total dihitung? | Perbandingan anggaran interaksi lingkungan dan biaya waktu total yang sebanding |
| RQ5 | Apakah hasil konsisten pada kondisi sistem lain yang relevan? | Evaluasi pada intensitas, heterogenitas, atau perubahan jaringan yang ditetapkan sebelumnya |

## 5. Tahapan pelaksanaan dan kriteria lanjut

### Tahap A — Bekukan bukti dan protokol

- [ ] Arsipkan suite lama, kode, konfigurasi, log, serta checksum artefak; jangan menimpa data lama.
- [ ] Catat versi Python, Java, pustaka, OS, perangkat keras, dan identitas build server yang benar-benar dijalankan.
- [ ] Tentukan klaim utama dan kontribusi yang membedakan penelitian dari penggunaan gabungan NSGA-II dan PPO.
- [ ] Tetapkan satu metrik utama, arah perbaikan, serta manfaat minimum yang dianggap berarti berdasarkan kebutuhan aplikasi.
- [ ] Tentukan keluarga pengujian multipel dan cara memilih konfigurasi sebelum evaluasi konfirmatori.

**Kriteria lanjut:** protokol eksperimen tertulis dan versi awalnya diarsipkan. Perubahan berikutnya diberi alasan serta tanggal.

### Tahap B — Tentukan dan validasi dasar simulator

Pilih salah satu jalur penelitian secara eksplisit:

| Jalur | Pekerjaan | Konsekuensi pelaporan |
|---|---|---|
| Integrasi event engine iFogSim2 | Bangun topologi, aliran tugas, penjadwalan kejadian, dan jembatan keputusan PPO ke komponen simulator | Klaim iFogSim2 didukung bukti eksekusi dan validasi integrasi |
| Simulator custom yang tervalidasi | Spesifikasikan model antrean, komputasi, jaringan, energi, waktu, dan asumsi; validasi terhadap perhitungan/rujukan atau pengukuran | Nyatakan sebagai simulator custom; jelaskan bagian iFogSim2 yang benar-benar digunakan |

Jika judul dan kontribusi tetap menekankan simulasi iFogSim2, prioritaskan jalur integrasi event engine. Simulator custom juga dapat menjadi dasar penelitian, tetapi memerlukan justifikasi dan validasi sendiri.

- [ ] Sediakan kasus sederhana dengan hasil analitis yang dapat diperiksa.
- [ ] Periksa konsistensi satuan, waktu selesai tugas, antrean, deadline, serta neraca energi.
- [ ] Verifikasi bahwa kenaikan kapasitas atau penurunan bandwidth memberi respons sesuai model pada kondisi terkendali.
- [ ] Simpan identitas source dan binary server, bukan hanya source Python.

**Kriteria lanjut:** ada bukti validasi model dan dokumentasi asumsi. Endpoint socket yang merespons PONG saja belum cukup.

### Tahap C — Implementasikan workload berbeda dan metrik sistem

Rancangan awal berikut merupakan usulan untuk dikalibrasi melalui pilot, bukan profil yang sudah tersedia pada kode saat ini:

| Profil | Definisi yang diusulkan | Pemeriksaan |
|---|---|---|
| Light | Demand masuk rendah relatif terhadap kapasitas sistem | Arrival rate rendah, antrean cenderung pendek |
| Moderate | Demand masuk menengah pada konfigurasi kapasitas yang sama | Ada kontensi yang terukur |
| Heavy | Demand mendekati atau melampaui kapasitas pada interval tertentu | Antrean, drop, atau violation meningkat dengan mekanisme yang dijelaskan |
| Dynamic | Arrival rate/demand berubah menurut waktu, termasuk transisi atau burst | Perubahan profil tampak pada trace dan respons sistem |

- [ ] Pisahkan generator tugas dari kebijakan; gunakan trace eksternal yang sama untuk pembanding pada satu skenario.
- [ ] Catat arrival time, data size, kebutuhan komputasi, deadline, prioritas, dan perangkat asal setiap tugas.
- [ ] Untuk mengisolasi intensitas, gunakan durasi observasi sebanding. Jika jumlah tugas/durasi berbeda, dokumentasikan alasannya.
- [ ] Kalibrasi profil sebelum mengevaluasi algoritma usulan; jangan memilih profil berdasarkan kemenangan ERWO.
- [ ] Simpan jumlah tugas yang datang, diterima, selesai, terlewat deadline, serta hilang/ditolak.

Metrik evaluasi yang perlu disediakan:

| Metrik | Bentuk pelaporan |
|---|---|
| Latensi | Mean dan persentil yang relevan, misalnya p95, dalam satuan waktu yang tervalidasi |
| Energi | Joule per tugas dan/atau total; jelaskan apakah hanya baterai IoT atau seluruh infrastruktur |
| Deadline | Persentase violation dengan denominator dan kebijakan tugas yang belum selesai dinyatakan |
| Throughput dan drop | Tugas per satuan waktu serta persentase drop/rejection |
| Antrean/utilisasi | Definisi dan cara agregasi terhadap waktu/node |
| QoS | Definisi operasional; bedakan skor reward dan kepatuhan layanan |
| Keputusan | Waktu inferensi dengan prosedur pengukuran yang sama |
| Reward | Diagnostik training; jika perlu, laporkan per langkah untuk membandingkan episode berbeda |

**Kriteria lanjut:** moderate dan dynamic tidak identik secara desain; trace menunjukkan distribusi/pola yang ditargetkan; metrik mentah memiliki satuan dan denominator yang jelas.

### Tahap D — Pilot kecil sebelum batch besar

- [ ] Gunakan tiga seed eksplorasi dan satu anggaran akhir yang dipilih untuk memeriksa kelayakan, bukan untuk klaim konfirmatori.
- [ ] Mulai dengan Least Fog, PPO-Equal, dan ERWO-PPO agar jalur utama cepat diperiksa.
- [ ] Periksa kurva belajar, aksi terpilih, antrean, utilisasi, violation, dan biaya inferensi.
- [ ] Pastikan fallback Python dinonaktifkan dan kegagalan socket menghentikan run.
- [ ] Periksa apakah kapasitas, topologi, dan kondisi berubah memang membutuhkan keputusan adaptif.
- [ ] Evaluasi stabilitas baseline dan penyebab seed gagal; pertahankan semua hasil serta aturan kegagalan yang ditetapkan.

**Kriteria lanjut:** model bekerja sesuai asumsi, log lengkap, dan pertanyaan penelitian dapat diuji. Jika Least Fog tetap dominan, analisis penyebabnya dan revisi klaim; tidak perlu memaksakan kemenangan ERWO.

### Tahap E — Ablation dan perbandingan biaya yang adil

| Pembanding | Tujuan |
|---|---|
| Least Fog | Mengukur manfaat tambahan dibanding kebijakan sederhana yang kuat |
| PPO-Equal | Mengisolasi manfaat optimasi bobot dibanding PPO dasar |
| PPO-Manual | Membandingkan optimasi terhadap bobot berbasis kebutuhan aplikasi, ditetapkan sebelum test |
| Random-search weights + PPO | Mengisolasi manfaat NSGA-II dari manfaat mencari bobot dengan cara apa pun |
| NSGA-II weights + PPO | Metode ERWO-PPO |
| Baseline RL relevan lainnya | Menguji posisi metode terhadap alternatif dengan representasi aksi dan tuning yang dijelaskan |

Pisahkan dua pertanyaan biaya:

1. **Training akhir sama:** mengukur manfaat bobot yang sudah dipilih; biaya pencarian tetap dilaporkan terpisah.
2. **Anggaran total sebanding:** mengukur manfaat setelah memperhitungkan pencarian dan training akhir. Sebagai ilustrasi nominal, ERWO dengan 200k pencarian + 100k final dibanding PPO-Equal dengan 300k training; jumlah aktual rollout dan biaya validasi harus tetap dicatat.

- [ ] Catat interaksi lingkungan pada training kandidat, validasi kandidat, training akhir, dan benchmark secara terpisah.
- [ ] Samakan anggaran dan aturan pemilihan konfigurasi untuk NSGA-II dan random search.
- [ ] Tuning baseline memakai data validasi, bukan data test.
- [ ] Periksa sensitivitas jumlah episode validasi kandidat; tiga episode saat ini berpotensi memberi estimasi bervariansi tinggi.
- [ ] Jika meneliti anggaran kandidat 5k/10k/20k, nyatakan sebagai eksperimen terpisah dengan biaya totalnya.

**Kriteria lanjut:** klaim efisiensi mempunyai pembanding anggaran total yang sesuai; keunggulan NSGA-II dapat dipisahkan dari efek tambahan komputasi.

### Tahap F — Evaluasi konfirmatori dan statistik

Usulan konfigurasi awal setelah tahap sebelumnya selesai:

| Komponen | Rencana |
|---|---|
| Seed training | Mulai 10 run independen per konfigurasi utama; evaluasi kebutuhan tambahan melalui perencanaan presisi/daya, bukan menambah sampai signifikan |
| Validasi kandidat | Set terpisah, misalnya seed lingkungan 10000–10029 |
| Test akhir | Set yang dikunci, misalnya seed lingkungan 20000–20099, sama untuk metode yang dibandingkan |
| Anggaran akhir | Tetapkan satu konfigurasi utama melalui pilot/validasi; konfigurasi lain menjadi analisis sensitivitas |
| Unit analisis utama | Rata-rata metrik per training run, kemudian perbandingan antar-run/seed |
| Pelaporan | Selisih performa, interval kepercayaan, mean/SD antar-run, serta biaya total |
| Pengujian multipel | Keluarga hipotesis ditetapkan sesuai klaim sebelum evaluasi |

Nomor seed merupakan label pengulangan, bukan jaminan statistik. Gunakan RNG/trace yang terpisah sesuai perannya; dokumentasikan pairing antar-metode. Seed training yang sama tidak otomatis menghasilkan pengalaman training identik pada algoritma berbeda.

- [ ] Tetapkan prosedur uji sesuai asumsi data; metode exact dengan lima pasangan memiliki resolusi terbatas.
- [ ] Bila memakai bootstrap bertingkat, resample pada tingkat run training dan episode dengan struktur pairing yang dijaga.
- [ ] Jangan merata-ratakan p-value atau menggandakan observasi moderate/dynamic lama.
- [ ] Jangan mengganti uji secara oportunistis ketika hasil tidak signifikan. Fallback otomatis Wilcoxon ke paired t-test pada kode perlu diganti dengan prosedur yang ditetapkan serta kegagalan yang tercatat.
- [ ] Definisikan effect size secara eksplisit; nilai absolut pada kode saat ini menyembunyikan arah efek.
- [ ] Hasil yang tidak signifikan tetap dilaporkan. Kesetaraan memerlukan rancangan dan margin kesetaraan tersendiri.
- [ ] Pemilihan konfigurasi terbaik dilakukan pada validasi; set test akhir tidak dipakai berulang untuk tuning.

**Kriteria selesai:** seluruh run yang direncanakan terlapor, ketidakpastian antar-training dianalisis, dan kesimpulan mengikuti ukuran efek serta intervalnya. Nilai p < 0,05 bukan syarat untuk menyimpan atau melaporkan hasil.

## 6. Batas klaim dan kesiapan manuskrip

| Klaim | Status sekarang |
|---|---|
| Batch otomatis berjalan dan artefak lengkap | Didukung audit |
| Optimasi bobot membantu PPO pada training akhir singkat dalam engine saat ini | Didukung secara deskriptif, dengan tambahan biaya pencarian |
| ERWO lebih efisien dalam total sampel/komputasi | Belum didukung |
| ERWO konsisten unggul terhadap PPO-Equal ketika training diulang | Belum terkonfirmasi pada audit lima seed |
| ERWO unggul atas seluruh baseline | Tidak didukung hasil saat ini |
| Telah diuji pada empat pola beban berbeda | Belum didukung implementasi workload |
| Episode PPO menjalankan event engine iFogSim2 penuh | Belum didukung source server saat ini |

Sebelum memilih target jurnal, pastikan:

- [ ] Kontribusi ilmiah dan keterbatasannya dinyatakan secara spesifik.
- [ ] Studi terkait terbaru menunjukkan celah yang benar-benar diatasi; penilaian kebaruan belum diselesaikan dalam audit ini.
- [ ] Dasar simulator, workload, satuan metrik, serta biaya pembanding tervalidasi.
- [ ] Analisis statistik mengikuti struktur replikasi dan ketidakpastian.
- [ ] Code, konfigurasi, dependency, trace, dan hasil mentah dapat direproduksi.
- [ ] Klaim positif maupun hasil negatif dilaporkan secara seimbang.
- [ ] Kecocokan scope dan panduan jurnal diperiksa saat pemilihan target. Tidak ada jaminan penerimaan berdasarkan kuartil.

## 7. Paket pekerjaan terdekat

| Urutan | Pekerjaan | Artefak yang diharapkan |
|---|---|---|
| 1 | Bekukan hasil lama dan tetapkan klaim/RQ/metrik utama | Arsip suite dan protokol awal |
| 2 | Putuskan jalur simulator; desain model waktu, tugas, dan sumber daya | Spesifikasi simulator dan kasus validasi |
| 3 | Implementasikan workload nyata serta metrik mentah | Generator trace, definisi satuan, dan hasil pilot |
| 4 | Perbaiki provenance build dan finalisasi status | Metadata run yang konsisten dan identitas binary server |
| 5 | Tambahkan random search dan pencatatan biaya interaksi total | Rancangan ablation dan tabel anggaran |
| 6 | Lakukan pilot lalu kunci konfigurasi konfirmatori | Kurva belajar serta keputusan konfigurasi terdokumentasi |
| 7 | Jalankan evaluasi multi-seed dan susun manuskrip | Dataset baru, analisis ketidakpastian, dan batas klaim |

## 8. Rujukan metodologi

- [Mahmud dkk., iFogSim2, Journal of Systems and Software (2022)](https://clouds.cis.unimelb.edu.au/papers/iFogSim2.pdf): dasar kemampuan dan model simulator iFogSim2.
- [Agarwal dkk., Deep Reinforcement Learning at the Edge of the Statistical Precipice, NeurIPS (2021)](https://proceedings.neurips.cc/paper_files/paper/2021/hash/f514cec81cb148559cf475e7426eed5e-Abstract.html): ketidakpastian evaluasi RL pada sedikit run.
- [Dokumentasi Wilcoxon SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wilcoxon.html): asumsi, pairing, dan penanganan selisih pada uji signed-rank.

Temuan numerik pada dokumen ini berasal dari audit artefak lokal. Tahap, konfigurasi seed masa depan, dan kriteria lanjut merupakan rancangan penelitian yang diusulkan; belum merupakan eksperimen yang sudah dijalankan.
