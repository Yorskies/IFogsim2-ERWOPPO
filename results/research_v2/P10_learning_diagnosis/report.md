# P10 — diagnosis stabilitas pembelajaran PPO

Protokol diagnostik `P10-stability-diagnosis-1`, skrip `run_ablation.py`, data `ablation.json`. **Namespace pilot** (outer 100–102 × repeat 0/1 = 6 seed); tidak ada seed
konfirmatori 0–19, split `validation` milik search, atau trace test yang dipakai. Config simulasi tidak berubah; hanya learner PPO yang divariasikan satu faktor per varian.
F = 102.400 keputusan, bobot equal, evaluasi deterministik pada 20 trace `pilot_validation`. 36 run, 12 worker paralel.

## Sebelum ablasi (data 26 run P10_learning_check, tanpa training baru)

- Runtuh ke always-cloud **bukan** perilaku yang diminta reward: biaya linear (yang dioptimalkan reward equal) always-cloud 0,379, lebih buruk dari always-local 0,247 dan
  Greedy-EFT 0,206; peringkat linear dan D konsisten. Ini kegagalan optimisasi.
- Critic fit baik (EV median ≈ 0,99), KL ≈ 0,008, clip ≈ 5%: bukan update yang terlalu agresif.
- Policy stokastik di akhir training (linear 0,30–0,40) masih lebih buruk dari always-local; dua dari lima seed memburuk. Hipotesis: dengan gamma = 1 dan episode ±1.000 langkah,
  return-to-go didominasi biaya sisa episode (mudah diprediksi, sehingga EV tinggi), sementara efek satu aksi tenggelam dalam derau.

## Hasil ablasi

Referensi pada trace yang sama: Greedy-EFT 0,260; always-local 0,370; always-cloud 0,475.

| Varian | D_F mean (SD) | < always-local | runtuh ke 1 aksi | membaik vs base (berpasangan) | linear on-policy awal → akhir |
|---|---:|---:|---:|---:|---|
| base (gamma 1,0) | 0,443 (0,034) | 0/6 | 1/6 | — | 0,367 → 0,379 |
| gamma 0,99 | 0,376 (0,089) | 2/6 | 0/6 | 5/6 | 0,363 → 0,298 |
| **gamma 0,97** | **0,250 (0,051)** | **6/6** | **0/6** | **6/6** | **0,366 → 0,207** |
| ent_coef 0,03 | 0,408 (0,100) | 2/6 | 1/6 | 4/6 | 0,364 → 0,383 |
| rollout 2048 / batch 512 | 0,496 (0,087) | 0/6 | 2/6 | 2/6 | 0,397 → 0,371 |
| learning rate 1e-4 | 0,484 (0,068) | 0/6 | 4/6 | 1/6 | 0,357 → 0,394 |

- **Gamma adalah faktor penentu, dengan dosis-respons monoton** (1,0 → 0,99 → 0,97: 0,443 → 0,376 → 0,250). Gamma 0,97 memperbaiki keenam seed (selisih berpasangan
  −0,12 s/d −0,29), tidak ada yang runtuh, seluruhnya mengalahkan always-local, 3 dari 6 lebih baik dari Greedy-EFT (mean 0,250 vs 0,260), dan biaya on-policy turun selama training.
- Entropi lebih besar, rollout lebih besar, dan learning rate lebih kecil **tidak** memperbaiki; dua yang terakhir memperburuk.
- Status inferensi: eksploratif. Sign-flip exact pada 6 selisih yang semuanya negatif memberi p = 2/64 = 0,031 (mentah); dengan lima varian yang diuji, Holm memberi 0,156.
  Konsistensi 6/6 dan pola dosis-respons lebih informatif daripada p ini.

## Konsekuensi untuk protokol

1. Schema v0.2 mengunci gamma = 1,0. Memakai gamma < 1 adalah **revisi protokol** (objektif training terdiskon; evaluasi D tetap tidak terdiskon) dan membatalkan lock P10.
2. K = 30.720 dipilih (P08) dengan learner gamma = 1 → gerbang fidelity harus diulang dengan learner baru; budget S/V/C/B ikut berubah.
3. Pemeriksaan sensitivitas bobot (yang tidak konsisten antar-seed) dilakukan dengan learner yang tidak stabil; premis RQ1 perlu diuji ulang dengan learner gamma 0,97.
4. Gamma 0,97 belum tentu optimal (0,95 atau 0,98 belum diuji); pilihan akhir sebaiknya ditetapkan pada namespace pilot sebelum lock baru, bukan dari hasil konfirmatori.

## Lanjutan: rentang gamma dan sensitivitas bobot dengan learner stabil

Skrip `run_followup.py`, data `followup.json` (54 run; namespace pilot; 22 run diulang setelah saya sendiri menghentikan orkestratornya — tidak ada data
yang tercampur, run parsial dihapus).

**Rentang gamma (bobot equal, 6 seed):**

| gamma | D_F mean (SD) | < always-local | < Greedy-EFT |
|---:|---:|---:|---:|
| 1,00 | 0,443 (0,034) | 0/6 | 0/6 |
| 0,99 | 0,376 (0,089) | 2/6 | 1/6 |
| 0,98 | 0,266 (0,045) | 6/6 | 2/6 |
| **0,97** | **0,250 (0,051)** | **6/6** | **3/6** |
| 0,95 | 0,293 (0,109) | 4/6 | 3/6 |

Optimum berada di 0,97–0,98; 0,95 lebih buruk dan kurang stabil (horizon efektif ±20 keputusan, lebih pendek dari jeda outcome heavy ±45).

**Delapan bobot pilot dengan gamma 0,97 (6 seed):**

| Bobot | D_F mean (SD) | selisih vs equal | seed lebih baik dari equal |
|---|---:|---:|---:|
| **vertex2** (0,92 pada zD/deadline) | **0,205 (0,022)** | **−0,045** | **4/6** |
| equal | 0,250 (0,051) | — | — |
| manual | 0,272 (0,038) | +0,022 | 2/6 |
| vertex3 (zB) | 0,308 (0,104) | +0,058 | 2/6 |
| simplex | 0,314 (0,062) | +0,064 | 2/6 |
| vertex1 (zE) | 0,340 (0,075) | +0,090 | 1/6 |
| vertex4 (zQ) | 0,365 (0,093) | +0,115 | 1/6 |
| vertex0 (zL) | 0,368 (0,043) | +0,118 | 0/6 |

- Dengan learner stabil, **efek bobot melampaui derau seed**: SD antar-bobot dalam satu seed 0,078 vs SD antar-seed equal 0,051. Kesepakatan peringkat antar seed
  naik dari ≈ 0 (gamma 1) menjadi Spearman rata-rata 0,36 (rentang −0,17 s/d 0,88; 15 pasangan) — sedang, belum kuat.
- **Seleksi lintas seed mentransfer:** memilih bobot terbaik dari tiga model repeat 0 dan menilainya pada model repeat 1 (seed segar) memilih vertex2 dengan keuntungan
  +0,014 terhadap equal; arah sebaliknya juga vertex2, +0,076. Seleksi dari **satu** model per outer run tidak andal: keuntungan pada seed saudara −0,04 / −0,19 / −0,03 / 0 / +0,11 / +0,08.
- Batas: 6 seed, satu budget F, 20 trace `pilot_validation` yang sama dipakai untuk memilih dan menilai (seed segar, trace tidak). Eksploratif; vertex2 **tidak** boleh
  dijadikan bobot konfirmatori — bobot konfirmatori tetap harus berasal dari pencarian.

**Implikasi:** dengan gamma 0,97 premis RQ1 menjadi masuk akal (ada bobot yang konsisten lebih baik dari equal dan seleksinya mentransfer ke seed baru jika didasarkan pada
beberapa model). Seleksi berbasis sedikit model rawan derau, sehingga gerbang fidelity v0.3 sebaiknya menambahkan kriteria kesepakatan **antar seed independen**, bukan hanya prefix.
