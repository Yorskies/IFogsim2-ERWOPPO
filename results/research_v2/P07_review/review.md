# Peninjauan P07: mengapa hasil belum memuaskan?

Masalah yang paling kuat didukung bukti berada pada pembelajaran reward tertunda dan perubahan perilaku saat argmax digunakan. Ada pula perbedaan tujuan antara reward linear dan skor RMS D. Penyebab kausal tunggal belum terbukti; perlu ablation terkontrol sebelum pencarian bobot P08. Menambah timestep saja belum menjadi solusi yang terbukti.

Review menambah **0 keputusan training**. Bukti: 30.720 keputusan pilot tersimpan, 60 update, replay 28 episode training lengkap, pemeriksaan 31 snapshot awal terhadap Java, serta kontrol Greedy-EFT pada 20 trace pilot validation yang sama (19.397 keputusan evaluasi tambahan). Config, reward, simulator dan protokol test tidak berubah.

## 1. Reward tertunda dibanding propagasi langsung GAE

Source SB3 terpasang menghitung `A[t] = delta[t] + gamma*lambda*A[t+1]`. Gamma=1 mempertahankan objektif episodik tetapi tidak menjadikan GAE sama dengan return Monte Carlo ketika lambda=0,95. Kontribusi langsung residual TD sejauh k keputusan berbobot `0,95^k`: sekitar 0,077 pada 50 keputusan dan 0,0059 pada 100 keputusan.

Replay aksi tersimpan memberikan jeda dari aksi sampai **outcome terminal**:

| Seed | Heavy median lag | Heavy p95 lag | Heavy lag >20 | Critic EV negatif |
|---|---:|---:|---:|---:|
| 100 | 49 | 165,0 | 87,0% | 10/20 update |
| 101 | 45 | 157,0 | 84,9% | 10/20 update |
| 102 | 43 | 149,0 | 83,2% | 8/20 update |

Mean explained variance per seed -0,177 / -0,051 / 0,045. Ini statistik value terhadap target return GAE dalam rollout, bukan pengukuran value sejati. Critic belum andal pada target training tersebut.

**Interpretasi:** reward yang jauh dan bootstrap critic lemah merupakan kandidat penyebab utama. Ini belum ablation kausal. Koefisien GAE bukan persentase informasi yang pasti hilang: value bootstrap bisa membawa informasi jangka panjang. Jeda diukur untuk outcome terminal (CL dan CQ), bukan semua komponen reward; energi/imbalance bisa muncul lebih cepat dan deadline bisa lebih awal.

## 2. Sampling dan argmax menghasilkan closed loop berbeda

Pada evaluasi deterministik akhir, r101 memilih F5 pada 100% tugas, r102 cloud pada 100%, r100 sekitar 90–98% lokal. Namun pada **snapshot training yang sama**, model akhir r101 memiliki argmax F5 pada 79,1% snapshot dan r102 argmax cloud pada 60,3%. Actor masih mampu memilih tujuan lain.

Ini mendukung perubahan distribusi state: sampling membagi beban; argmax memusatkan trafik, antrean berubah, dan policy menghadapi keadaan berbeda dari data training. Bukan bukti fungsi predict selalu mengembalikan aksi tetap atau actor tidak membaca observasi. Hubungan kausal spesifik perubahan antrean masih perlu diuji.

Evaluasi sampling diagnostik memperbaiki D r101 dari 0,6706 menjadi 0,4502 dan r102 dari 0,4749 menjadi 0,4227. R100 justru memburuk dari 0,3626 menjadi 0,4083 karena kenaikan zB mengimbangi perbaikan violation. Mengganti argmax dengan sampling tidak menyelesaikan semua masalah; jangan diam-diam mengganti protokol evaluasi utama.

## 3. Reward yang dipelajari berbeda dari skor D

Reward equal-weight meminimalkan `mean(z)`. Skor utama memakai `sqrt(mean(F²))` setelah macro-average workload. Keduanya berbeda secara matematis.

| Seed | Biaya linear 512 → 10.240 | D 512 → 10.240 |
|---|---|---|
| 100 | 0,2117 → 0,2690 | 0,3195 → 0,3626 |
| 101 | 0,5980 → 0,6099 | 0,6560 → 0,6706 |
| 102 | 0,3903 → 0,3702 | 0,4431 → 0,4749 |

R102 memperbaiki biaya linear sekitar **5,2%**, sementara D memburuk sekitar **7,2%**. Jadi klaim bahwa semua seed sama sekali tidak belajar terlalu kuat: r102 membaik menurut objektif linear pada checkpoint evaluasi ini. Dua seed lain memburuk pada kedua ukuran. Ini pengamatan dua checkpoint, bukan bukti konvergensi atau signifikansi.

Always-cloud/local mendapat zB=0 karena tidak memakai fog. Cloud konstan bisa menghapus biaya imbalance walaupun reliability heavy runtuh. Pada episode training lengkap, zB menyumbang 27,7–29,4% biaya linear dan energi 4,9–5,8%, meskipun bobot nominal sama. Ini mengikuti spesifikasi; bukan bug ledger atau alasan mengubah normalisasi setelah melihat test.

## 4. Cakupan pilot masih sedikit dan exposure tidak merata

Hanya 9–10 episode lengkap per model, yaitu 2–3 episode per workload. Heavy mengisi 47–52% keputusan; light hanya 5–9%. Evaluasi memberikan bobot 25% per workload. Round-robin berjalan benar dan ketidaksamaan jumlah keputusan memang diperkirakan oleh protokol, tetapi cakupan ini masih sedikit bagi policy campuran dan critic.

Menambah timestep belum terbukti menyelesaikannya: r100 pada 102.400 keputusan tetap always-cloud pada evaluasi dan D=0,4749. Satu seed ini tidak membuktikan semua training panjang gagal, tetapi menolak anjuran menaikkan budget tanpa diagnosis.

## 5. Masih ada ruang perbaikan policy pada sistem fisik yang sama

Greedy-EFT tanpa training, memakai 20 trace pilot validation yang persis sama:

- Dglobal **0,2603**, dibanding PPO akhir 0,3626 / 0,6706 / 0,4749.
- Reliability heavy **96,0%**, dibanding PPO r100 85,0%; r101 4,2%; r102 9,9%.
- Violation heavy masih **61,6%**. Reliability tinggi tidak sama dengan memenuhi deadline.

Kegagalan PPO bukan semata karena semua tugas tidak mungkin diselesaikan. Kontrol ini bukan perbandingan konfirmatori lintas training seed.

## Pemeriksaan yang mempersempit diagnosis

- Replay cocok dengan final cost pada seluruh 28 episode lengkap; transformasi snapshot awal cocok dengan Java pada 31 kasus. Ini tidak membuktikan seluruh simulator bebas bug.
- Reward/delta biaya konsisten, terminal drain tidak hilang, policy berubah, seed dan prefix checkpoint identik.
- Semua 20 update per pilot menjalankan total 200 epoch. Pengurangan epoch karena early stopping KL tidak menjelaskan hasil ini.
- Transisi terminal rata-rata memuat 2,1–2,4% biaya episode, walau reward-nya 24–43 kali median step pada episode. Ada potensi variasi target, tetapi drain bukan mayoritas biaya dan tidak boleh dihapus/clipping begitu saja.
- Observasi agregat dan N trace tidak tersedia kepada actor/critic, sementara sebagian reward dinormalisasi oleh N. Ini bisa menyulitkan estimasi value; kausalitasnya belum dibuktikan. Jangan membuka future/N kepada actor sebagai perbaikan cepat.
- Bug ringkasan D sebelumnya sudah dikoreksi dari data episode mentah. Bug tersebut tidak mengubah reward atau training; hasil D di atas memakai RMS yang benar.

## Tindak lanjut yang disarankan — belum dijalankan

1. Tambahkan diagnosis rollout: value, advantage, return serta besar gradient/clip.
2. Ablation pilot **lambda=0,95 vs 1,0**, gamma tetap 1, seed 100/101/102, atribut trace, bobot dan budget sama. Lambda=1 mengurangi filter residual GAE tetapi dapat meningkatkan varians; rollout parsial tetap bootstrap, sehingga ini bukan jaminan perbaikan.
3. Ukur deterministic dan sampling secara terpisah, action share, reliability, violation, mean(z) dan D pada kedua kondisi. Jangan memilih seed terbaik atau mengganti metrik utama sesudah hasil diketahui.
4. Jika policy tetap menyebar tetapi argmax selalu satu tujuan, tinjau protokol deployment sebelum menambah budget/search. Perubahan entropy coefficient atau pendekatan lain merupakan eksperimen terpisah, jangan digabung dengan perubahan lambda.
5. Pertahankan reward/engine pada diagnosis pertama. Tinjau imbalance dan objektif linear versus D sebagai isu protokol terpisah, dengan versi dan alasan sebelum P08/test.

Perubahan lambda membutuhkan effective config/provenance baru yang konsisten dengan validasi/build. Jangan menimpa bukti v0.2 atau mengubah kwargs tanpa pencatatan. Semua diagnosis menggunakan namespace pilot dan test konfirmatori tetap tertutup. Pencarian besar P08 sebaiknya menunggu hasil diagnosis ini.

## Artefak dan reproduksi

- `review.json`: exposure, critic, lag outcome, drain, policy pada snapshot yang sama.
- `conclusions.json`: ringkasan dan accounting review.
- `greedy_eft_same_validation.json`: 20 episode kontrol dan metriknya.
- `research_v2/learning_review.py`: audit/replay tanpa optimizer atau learn().
- Tiga tes review lulus; 14 tes persiapan P07 sebelumnya lulus.

```bash
venv/bin/python -m research_v2.learning_review --evidence-dir results/research_v2/P07_completion_20261107T205826Z --output-dir results/research_v2/P07_review_reproduced --jdk-home /usr/lib/jvm/java-21-openjdk-amd64
venv/bin/python -m research_v2.learning_review --evidence-dir results/research_v2/P07_completion_20261107T205826Z --output-dir results/research_v2/P07_review_reproduced --baseline-only --jdk-home /usr/lib/jvm/java-21-openjdk-amd64
```

Sumber teknis yang diperiksa: source SB3 terpasang (`common/buffers.py`, `common/on_policy_algorithm.py`, `ppo/ppo.py`), `ObservationBuilder.java`, reward Gym v2, serta spesifikasi penelitian §§16–19. Tidak ada klaim berbasis versi pustaka lain.
