# Laporan Teknis: Analisis Dinamika Inferensi Model PPO pada Skenario Beban Dinamis dan Berat

**Dokumen**: Laporan Investigasi dan Audit Inferensi RL  
**Proyek**: Evolutionary Reward Weight Optimization with Proximal Policy Optimization (ERWO-PPO)  
**Lingkungan**: iFogSim2 Simulator Wrapper (46-D State Space, Discrete(7) Action Space)  
**Model Teruji**: `models/ppo_ifogsim2_erwo.zip`  
**Tanggal Audit**: 24 Oktober 2026  

---

## 1. Ringkasan Eksekutif

Dalam pengujian evaluasi dan visualisasi inferensi sistem *task offloading* pada skenario beban dinamis (*dynamic*) dan berat (*heavy*), teramati anomali perilaku di mana model ERWO-PPO yang tersimpan secara konsisten mengarahkan tugas komputasi ke **Node 5 (Fog Node E)**. Fenomena ini menyebabkan utilisasi CPU dan panjang antrean pada Node 5 mencapai saturasi maksimal ($1.00$), sementara Fog Nodes lainnya (Node 1 hingga Node 4) berada dalam kondisi menganggur (*idle*, utilisasi $\le 0.05$).

Investigasi teknis dilakukan dengan membedah bobot jaringan neural kebijakan (*policy network*), distribusi probabilitas output, sensitivitas gradien masukan terhadap keluaran, serta perumusan fungsi reward pada *environment*. Laporan ini mendokumentasikan temuan empiris, akar penyebab (*root causes*), dan rekomendasi solusinya.

---

## 2. Metodologi Investigasi

Investigasi dilakukan melalui lima tahapan audit empiris:
1. **Inspeksi Arsitektur & Metadata Model**: Pembacaan parameter internal dari checkpoint model Stable-Baselines3.
2. **Evaluasi Logit & Distribusi Aksi**: Analisis nilai logit $\mathbf{z}$ dan probabilitas softmax $\pi(a|s) = \text{Softmax}(\mathbf{z})$ pada observasi awal dan observasi tersaturasi.
3. **Analisis Sensitivitas Gradien Autograd**: Perhitungan turunan parsial keluaran logit terhadap seluruh 46 fitur observasi:
   $$\mathbf{J}_{a, i} = \frac{\partial z_a}{\partial s_i}$$
4. **Komparasi Mode Inferensi**: Uji coba 50 langkah berurutan dengan membandingkan inferensi deterministik ($\text{argmax}$) dan inferensi stokastik (*probabilistic sampling*).
5. **Dekomposisi Fungsi Reward**: Simulasi respon sub-reward numerik saat tugas ditempatkan pada node yang sedang menganggur versus node yang sedang jenuh.

---

## 3. Temuan Kunci dan Analisis Akar Masalah

### 3.1. Efek Operasi Argmax pada Inferensi Deterministik (`deterministic=True`)

Pada modul eksekusi [`run_demo.py`](file:///C:/Projects/erwo_ppo_project/run_demo.py) dan *worker* dashboard [`dashboard/server.py`](file:///C:/Projects/erwo_ppo_project/dashboard/server.py), inferensi dijalankan menggunakan parameter:
```python
action, _ = model.predict(obs, deterministic=True)
```
Dalam pustaka Stable-Baselines3, parameter `deterministic=True` pada ruang aksi diskret tidak melakukan sampling dari distribusi probabilitas, melainkan mengeksekusi operasi pemilihan deterministik:
$$a^* = \arg\max_{a \in \{0, \dots, 6\}} z_a$$

Hasil ekstraksi logit dan probabilitas softmax dari model pada observasi awal lingkungan adalah sebagai berikut:

| Indeks Aksi ($a$) | Identitas Node | Logit Output ($z_a$) | Probabilitas Kebijakan $\pi(a\|s)$ |
| :---: | :--- | :---: | :---: |
| 0 | Local Device (Node 0) | -3.039 | 4.79% |
| 1 | Fog Node A (Node 1) | -1.717 | 17.96% |
| 2 | Fog Node B (Node 2) | -2.509 | 8.13% |
| 3 | Fog Node C (Node 3) | -1.582 | 20.56% |
| 4 | Fog Node D (Node 4) | -1.624 | 19.71% |
| **5** | **Fog Node E (Node 5)** | **-1.376** | **25.25% (Maksimum)** |
| 6 | Cloud Server (Node 6) | -3.324 | 3.60% |

Dari tabel di atas terlihat bahwa distribusi probabilitas di antara Fog Nodes (Node 1, 3, 4, 5) sebenarnya terdistribusi relatif seimbang di rentang $18\% - 25\%$. Namun, karena logit untuk Node 5 ($-1.376$) sedikit lebih tinggi daripada Node 3 ($-1.582$), operasi `argmax` selalu memenangkan Node 5.

Tabel perbandingan frekuensi pemilihan aksi selama 50 langkah simulasi:

| Mode Inferensi | Node 0 (Local) | Node 1 (Fog A) | Node 2 (Fog B) | Node 3 (Fog C) | Node 4 (Fog D) | Node 5 (Fog E) | Node 6 (Cloud) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Deterministik (`True`)** | 0 | 0 | 0 | 12 (24%) | 0 | **38 (76%)** | 0 |
| **Stokastik (`False`)** | 6 | 8 | 5 | 10 | 8 | **12 (24%)** | 1 |

*Kesimpulan Bagian 3.1*: Mode deterministik memicu fenomena *winner-takes-all* yang mengeliminasi Fog Nodes lainnya meskipun probabilitas dasarnya signifikan.

---

### 3.2. Kondisi Under-Training pada Checkpoint Model

Audit metadata internal pada checkpoint [`models/ppo_ifogsim2_erwo.zip`](file:///C:/Projects/erwo_ppo_project/models/ppo_ifogsim2_erwo.zip) menunjukkan data berikut:
- `num_timesteps`: $5.120$
- `_total_timesteps`: $5.000$
- Arsitektur: Multi-Layer Perceptron (MLP) dengan 2 lapisan tersembunyi $[128, 128]$ dan fungsi aktivasi Tanh.

Jumlah $5.120$ timestep hanya mencakup 20 siklus pembaruan gradien PPO (dengan konfigurasi `n_steps=256`). Untuk ruang observasi berdimensi 46 dan ruang aksi 7 kelas, jumlah iterasi ini belum mencapai konvergensi.

Hasil analisis gradien autograd $\frac{\partial z_a}{\partial s_i}$ mengonfirmasi hal ini:
- Sensitivitas logit terhadap utilisasi CPU node ($\text{index } 0 \dots 6$): $\approx 0.001 - 0.065$.
- Sensitivitas logit terhadap antrean node ($\text{index } 28 \dots 34$): $\approx 0.004 - 0.069$.

Karena gradien sensitivitas berada pada orde magnitudo $10^{-2}$, perubahan utilisasi CPU Node 5 dari $0.05$ (kosong) menjadi $1.00$ (penuh) hanya mereduksi nilai logit sebesar:
$$\Delta z_5 \approx 0.065 \times 0.95 \approx 0.061$$
Penurunan dari $-1.376$ menjadi $-1.437$ masih menempatkan logit Node 5 di atas Node 1 ($-1.717$) dan Node 4 ($-1.624$). Akibatnya, model tidak memiliki kapasitas respon yang cukup kuat untuk beralih ke node lain saat saturasi terjadi.

---

### 3.3. Karakteristik Fisik Lingkungan dan Asimetri Sub-Reward

Struktur fungsi reward multi-objektif didefinisikan sebagai:
$$R_{\text{total}} = \alpha \cdot r_{\text{latency}} + \beta \cdot r_{\text{energy}} + \lambda \cdot r_{\text{deadline}} + \gamma \cdot r_{\text{qos}}$$
dengan vektor bobot optimal $w^* = [0.2791, 0.1598, 0.3092, 0.2518]$.

Berdasarkan formulasi fisik di [`env_ifogsim2.py`](file:///C:/Projects/erwo_ppo_project/env_ifogsim2.py):
1. **Eksekusi Lokal (Node 0)**: Menghasilkan konsumsi energi tinggi pada baterai perangkat sumber ($E = 1.25 \times \text{task\_mi}$), menekan sub-reward energi ke level rendah ($\approx 0.16$).
2. **Offloading Cloud (Node 6)**: Menghadapi latensi jaringan WAN tinggi ($65 - 85\text{ ms}$), menyebabkan pelanggaran batas waktu SLA secara konsisten.
3. **Offloading Fog (Node 1–5)**: Sangat efisien dalam konsumsi energi baterai ($E = 0.25$) dan memiliki latensi transmisi nirkabel rendah.

Pengujian numerik respon reward pada profil tugas rata-rata ($\text{data} = 0.5, \text{MI} = 0.5, \text{deadline} = 0.5$):

| Kondisi Node Target | Total Latensi | Pelanggaran SLA | Sub-Reward $[r_{\text{lat}}, r_{\text{energy}}, r_{\text{dead}}, r_{\text{qos}}]$ | Reward Total ($R_{\text{total}}$) |
| :--- | :---: | :---: | :---: | :---: |
| **Node 1 (Idle, CPU=0.05, Queue=0.00)** | $0.455\text{ s}$ | Tidak Melanggar | $[0.553, 0.896, 1.000, 0.792]$ | **$0.8064$** |
| **Node 5 (Saturated, CPU=1.00, Queue=1.00)** | $1.019\text{ s}$ | Melanggar | $[0.266, 0.896, 0.000, 0.000]$ | **$0.2174$** |

Meskipun reward saat saturated ($0.2174$) jauh lebih rendah dibandingkan saat idle ($0.8064$), nilainya **tetap bernilai positif** karena kontribusi sub-reward energi ($0.896 \times 0.1598 = 0.143$) dan sisa sub-reward latensi. Karena tidak ada penalti langsung terhadap ketidakseimbangan beban (*load imbalance penalty*) dalam MDP, model yang masih dalam fase *under-training* tidak menerima sinyal gradien negatif yang cukup tajam untuk meninggalkan Node 5.

---

### 3.4. Dinamika Beban Asimetris pada Skenario Dynamic dan Heavy

Pada skenario beban dinamis dan berat, frekuensi kedatangan tugas tinggi. Begitu sebuah node dipilih pada langkah awal:
1. Beban CPU dan antrean node terpilih meningkat secara kumulatif:
   $$\mathbf{u}^{\text{cpu}}_{a_t} \leftarrow \min(1.0, \mathbf{u}^{\text{cpu}}_{a_t} + 0.20 \cdot c_{\text{task}})$$
2. Node yang tidak dipilih mengalami peluruhan alami (*decay*):
   $$\mathbf{u}^{\text{cpu}}_i \leftarrow \max(0.05, \mathbf{u}^{\text{cpu}}_i - 0.08)$$
3. Karena mode deterministik terus memilih Node 5, Node 5 terkunci pada kapasitas $100\%$, sedangkan Node 1 s/d 4 mengalami peluruhan penuh hingga utilisasi dasar ($5\%$).

Sebagai perbandingan, metode baseline heuristik [`LeastLoadedFogPolicy`](file:///C:/Projects/erwo_ppo_project/agent_baselines.py) yang menggunakan aturan berbasis kondisi eksplisit:
$$a^* = \arg\min_{i \in \{1, \dots, 5\}} (\mathbf{u}^{\text{cpu}}_i + \mathbf{q}^{\text{len}}_i)$$
menghasilkan urutan aksi yang terdistribusi secara seimbang: `[4, 5, 1, 3, 2, 4, 3, 1, 2, 4, ...]`.

---

## 4. Matriks Perbandingan Karakteristik Model

| Aspek Evaluasi | ERWO-PPO (Checkpoint Saat Ini) | Least-Loaded Fog (Baseline) | Target ERWO-PPO Setelah Optimalisasi |
| :--- | :---: | :---: | :---: |
| **Jumlah Timestep Latih** | $5.120$ langkah | Tanpa Pelatihan (Heuristik) | $30.000 - 50.000$ langkah |
| **Mode Inferensi** | Deterministik (`argmax`) | Berbasis Aturan Minimum Beban | Stokastik atau PPO Konvergen |
| **Distribusi Aksi** | Terkonsentrasi di Node 5 & 3 | Merata di Node 1, 2, 3, 4, 5 | Terdistribusi adaptif sesuai kondisi |
| **Load Imbalance ($\sigma_{\text{CPU}}$)** | Tinggi ($\approx 0.3160$) | Sangat Rendah ($\approx 0.0383$) | Rendah ($\le 0.0500$) |
| **Tingkat Pelanggaran SLA** | $\approx 73.40\%$ | $\approx 20.80\%$ | $\le 20.00\%$ |

---

## 5. Rencana Tindak Lanjut dan Rekomendasi Solusi

Untuk mengatasi kendala ini secara sistematis, diusulkan pendekatan bertahap:

### 5.1. Solusi Jangka Pendek (Implementasi Segera pada Dashboard & Demo)
Mengonfigurasi mode inferensi pada [`dashboard/server.py`](file:///C:/Projects/erwo_ppo_project/dashboard/server.py) dan [`run_demo.py`](file:///C:/Projects/erwo_ppo_project/run_demo.py) agar mendukung parameter `deterministic=False` atau *temperature-scaled sampling*.
- **Dampak Langsung**: Beban seketika terdistribusi secara proporsional ke Node 1 hingga Node 5 sesuai distribusi probabilitas model tanpa perlu melatih ulang checkpoint.

### 5.2. Solusi Jangka Menengah (Pelatihan Ulang Model PPO Penuh)
Menjalankan kembali prosedur pelatihan PPO penuh dengan parameter yang memadai:
- Meningkatkan timesteps pelatihan dari $5.000$ menjadi $30.000 - 50.000$ timesteps.
- Mempertahankan koefisien entropi `ent_coef=0.03` untuk menjaga eksplorasi aktif selama pelatihan.
- Menggunakan skenario `dynamic` sebagai lingkungan pelatihan utama agar model terlatih menghadapi variasi beban heterogen.

### 5.3. Solusi Jangka Panjang (Perbaikan Perumusan Reward MDP)
Menyertakan penalti eksplisit terhadap standar deviasi beban CPU ($\sigma_{\text{CPU}}$) langsung ke dalam reward total:
$$R_{\text{total}} = \mathbf{w}^T \mathbf{r}_{\text{sub}} - \kappa \cdot \sigma_{\text{CPU}}$$
dengan koefisien penalti $\kappa \approx 0.15 - 0.25$. Penambahan suku penalti ini menjamin bahwa setiap aksi yang memicu penumpukan beban pada satu node akan menerima sinyal gradien negatif yang kuat.

---

**Penyusun Dokumen**: Antigravity Assistant (AI Pair Programmer)  
**Tinjauan Berkas Terkait**:
- [`env_ifogsim2.py`](file:///C:/Projects/erwo_ppo_project/env_ifogsim2.py)
- [`agent_ppo.py`](file:///C:/Projects/erwo_ppo_project/agent_ppo.py)
- [`agent_baselines.py`](file:///C:/Projects/erwo_ppo_project/agent_baselines.py)
- [`dashboard/server.py`](file:///C:/Projects/erwo_ppo_project/dashboard/server.py)
- [`run_demo.py`](file:///C:/Projects/erwo_ppo_project/run_demo.py)
- [`Data.md`](file:///C:/Projects/erwo_ppo_project/Data.md)
