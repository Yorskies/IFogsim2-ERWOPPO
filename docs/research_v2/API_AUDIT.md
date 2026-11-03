# Audit API native iFogSim2/CloudSim — P00

Audit memakai source yang ada di repository, bukan asumsi API CloudSim versi
lain. Perubahan core legacy belum dilakukan.

| Source/API lokal | Temuan | Keputusan dan pemilik |
|---|---|---|
| `core/CloudSim.java`: `init(..., double minTimeBetweenEvents)` | Overload minimum spacing tersedia; default .01 terlalu besar untuk sebagian kasus | P02 selalu init dengan1e-6; probe P00 membuktikan event pada1e-6; validasi beban aktual masih P02 |
| `core/CloudSim.java`: `startSimulation/run/finishSimulation` | State queue/entity/clock direset pada akhir; mengandung banyak static | Probe P00 membuktikan dua episode sederhana; reset seluruh FogDevice/TimeKeeper/counter belum terbukti; P02 wajib regression multi-episode |
| `core/SimEntity.java`: `schedule`, `processEvent` | Entity dan event native tersedia; tag bertipe `CloudSimTags` interface, bukan int | V2 gunakan enum implementasi CloudSimTags; tidak menambah int tag ke core |
| `core/EventQueue.java`, `SimEvent.compareTo` | Urutan time lalu serial penyisipan; bukan prioritas semantik | P02 coordinator harus mengendalikan urutan dan zero-delay closure; tidak cukup mengirim timeout sesudah arrival di source |
| `CloudletScheduler.java`: `updateCloudletsProcessing` | Mengakumulasi progress Cloudlet native; minimum next-event spacing; mutasi list MIPS share | P02 kirim mutable defensive copy list MIPS dan sinkronkan update sebelum admission/cancel |
| `CloudletSchedulerSpaceShared.java`: `cloudletSubmit` | Satu task satu PE dapat dipakai; waiting list tidak dibatasi; tidak ada RAM admission | Adapter P02 menegakkan Qwait/RAM sebelum native submit; tidak memakai stock scheduler sebagai engine final |
| `CloudletSchedulerSpaceShared.updateWaitingCloudlets` | Memindahkan paling banyak satu task per update | P02 harus mengisi semua PE bebas sambil mempertahankan FCFS dan PE-ID terkecil; uji multi-PE wajib |
| `CloudletScheduler.cloudletCancel` versus `SpaceShared.usedPes` | Cancel aktif yang belum selesai menghapus exec list, tetapi tidak mengurangi usedPes; waiting cancel tidak menulis terminal status | P00 probe mereproduksi hazard; P02 adapter harus melepas PE, RAM, queue dan membuat outcome konsisten; P00 tidak memperbaiki scheduler legacy |
| `SpaceShared.cloudletSubmit(cl,fileTransferTime)` | Menambah transfer ke panjang cloudlet | P03 transport sendiri; selalu fileTransferTime0, jika tidak latency dihitung dua kali |
| `FogDevice.java`, contoh `DCNSFog.java`, `VmScheduler*` | Jalur default module dan periodic resource management memakai asumsi lain; native counter energi dapat berjalan | Factory P02 memilih host/VM/PE nyata dan adapter eksplisit, tidak mengaktifkan time-sharing default; P04 satu ledger, jangan tambah counter default |
| `FogLinearPowerModel.getPower(0)` | Mengembalikan daya idle; constructor(maxPower,staticPower) memakai W absolut | Model sesuai; P00 IoT .5/2.5 memberi idle34.5J selama69s; ledger menyeluruh P04 |
| `PowerModelLinear.getPower(0)` | Mengembalikan0; constructor staticPowerPercent berbeda | Tidak dipakai tanpa koreksi; jangan menukar parameter dengan FogLinearPowerModel |
| `TimeKeeper`, `FogUtils`, `NetworkUsageMonitor` | Singleton/map/counter global tidak seluruhnya direset CloudSim.init | P02 miliki SimulationContext/ID/ledger per episode; audit ulang saat memasukkan FogDevice; jangan bergantung statistik global lama |

Rujukan source berada di `ifogsim/src/org/cloudbus/cloudsim/` dan
`ifogsim/src/org/fog/`. Receipt build merekam SHA-256 input yang diaudit.
Native probe hanya membuktikan integrasi API event dasar, **belum** eksekusi
Cloudlet melalui host/VM/PE lengkap, CPU cancellation yang benar, jaringan,
atau kesiapan training.
