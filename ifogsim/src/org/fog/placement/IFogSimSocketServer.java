package org.fog.placement;

import java.io.*;
import java.net.*;
import java.util.*;
import java.util.concurrent.*;

/**
 * =========================================================================================
 * KELAS: IFogSimSocketServer
 * =========================================================================================
 * Deskripsi:
 * Server TCP Socket multi-threaded yang bertindak sebagai jembatan komunikasi
 * (IPC Bridge)
 * antara simulator komputasi kabut (iFogSim2 / CloudSim berbasis Java) dan
 * algoritma AI
 * (ERWO-PPO berbasis Python/Gymnasium).
 * 
 * Fungsi Utama:
 * 1. Menerima koneksi socket dari wrapper Python (env_ifogsim2.py) pada port
 * default 5555.
 * 2. Mengelola simulasi diskrit 3-Tier Fog Computing (Local IoT, 5 Fog Nodes, 1
 * Cloud Server).
 * 3. Menerima aksi offloading diskrit (a_t: 0 s/d 6) dari agen PPO.
 * 4. Memodelkan latensi transmisi jaringan, waktu antrean, komputasi CPU, dan
 * konsumsi daya baterai.
 * 5. Menghitung 4 parameter sub-reward multi-objektif (Latensi, Energi,
 * Deadline, QoS).
 * 6. Mengupdate beban komputasi CPU & antrean secara dinamis berbasis aksi
 * (Action-Based Dynamics).
 * 7. Mengirimkan kembali vektor state observasi 46 dimensi dan metrik evaluasi
 * dalam format JSON.
 * =========================================================================================
 */
public class IFogSimSocketServer {

    // =====================================================================================
    // KONSTANTA KONFIGURASI SISTEM
    // =====================================================================================

    // Port default untuk koneksi TCP Socket IPC
    private static final int DEFAULT_PORT = 5555;

    // Jumlah total node komputasi dalam topologi 3-Tier (0=Lokal, 1..5=Fog Nodes,
    // 6=Cloud)
    private static final int NUM_NODES = 7;

    // Dimensi vektor observasi state lingkungan iFogSim2 (46 fitur ternormalisasi
    // [0.0 - 1.0])
    private static final int STATE_DIM = 46;

    // Objek ServerSocket untuk mendengarkan koneksi masuk dari client Python
    private ServerSocket serverSocket;

    // Flag status operasional server (volatile untuk thread-safety lintas core CPU)
    private volatile boolean isRunning = false;

    // Thread pool dinamis untuk menangani multi-koneksi client/kandidat evaluasi
    // NSGA-II secara paralel
    private ExecutorService threadPool = Executors.newCachedThreadPool();

    /**
     * Entry point utama eksekusi server Java.
     * Menerima argumen nomor port opsional dari baris perintah.
     * 
     * @param args Argumen baris perintah (args[0] = nomor port opsional).
     */
    public static void main(String[] args) {
        int port = DEFAULT_PORT;

        // Memeriksa apakah pengguna menentukan port khusus via argumen CLI
        if (args.length > 0) {
            try {
                port = Integer.parseInt(args[0]);
            } catch (NumberFormatException e) {
                System.err.println("[iFogSim2-Server] Port tidak valid, menggunakan port default: " + DEFAULT_PORT);
            }
        }

        // Instansiasi server dan pasang shutdown hook untuk terminasi proses yang aman
        IFogSimSocketServer server = new IFogSimSocketServer();
        Runtime.getRuntime().addShutdownHook(new Thread(server::stop));

        // Memulai siklus hidup server
        server.start(port);
    }

    /**
     * Membuka socket server TCP, mengikat port, dan menerima koneksi masuk (listen
     * loop).
     * 
     * @param port Nomor port TCP yang akan didengarkan (misal: 5555).
     */
    public void start(int port) {
        try {
            serverSocket = new ServerSocket();

            // Mengizinkan penggunaan kembali alamat port segera setelah restart (mencegah
            // Address Already in Use)
            serverSocket.setReuseAddress(true);

            // Mengikat server socket ke alamat localhost dan port target
            serverSocket.bind(new InetSocketAddress(port));
            isRunning = true;

            System.out.println("=================================================================");
            System.out.println(" [iFogSim2-Server] Server Socket aktif di port: " + port);
            System.out.println(" [iFogSim2-Server] Realistic Edge/Fog/Cloud Engine Siap Melayani PPO");
            System.out.println("=================================================================");

            // Loop utama penerimaan koneksi client
            while (isRunning) {
                try {
                    // Menunggu dan menerima koneksi baru dari Python
                    Socket clientSocket = serverSocket.accept();

                    // Menonaktifkan Nagle's Algorithm (TCP_NODELAY = true) untuk meminimalkan
                    // latensi paket IPC
                    clientSocket.setTcpNoDelay(true);

                    // Menjaga koneksi tetap hidup selama proses evaluasi episode yang panjang
                    clientSocket.setKeepAlive(true);

                    // Menyerahkan penanganan client ke worker thread di thread pool secara
                    // asynchronous
                    threadPool.submit(() -> handleClient(clientSocket));
                } catch (SocketException se) {
                    // Terjadi saat server socket ditutup secara sengaja pada method stop()
                    if (!isRunning)
                        break;
                }
            }
        } catch (IOException e) {
            if (isRunning) {
                System.err.println("[iFogSim2-Server] Error pada ServerSocket: " + e.getMessage());
            }
        } finally {
            // Pastikan pembersihan resource socket dilakukan
            stop();
        }
    }

    /**
     * Menangani sesi interaksi komunikasi per client (satu episode / serangkaian
     * episode simulasi).
     * Menerima perintah teks (RESET, STEP, CLOSE, PING) dan membalas dengan JSON
     * string.
     * 
     * @param socket Socket TCP client yang terhubung.
     */
    private void handleClient(Socket socket) {
        // Array state observasi internal 46 dimensi
        double[] currentState = new double[STATE_DIM];

        // Pelacak langkah saat ini dalam satu episode
        int currentStep = 0;

        // Batas maksimal langkah per episode (default: 100 untuk dynamic/moderate)
        int maxSteps = 100;

        // Skenario profil kedatangan beban tugas (light, moderate, heavy, dynamic)
        String currentWorkload = "dynamic";

        // Generator bilangan acak untuk simulasi stokastik
        Random random = new Random(System.nanoTime());

        // -----------------------------------------------------------------
        // PEMODELAN FLEET 100 PERANGKAT IoT (TIER 1 - BROKER BASED MODEL)
        // -----------------------------------------------------------------
        final int NUM_IOT_DEVICES = 100;
        double[] iotDeviceCpu = new double[NUM_IOT_DEVICES];
        double[] iotDeviceBattery = new double[NUM_IOT_DEVICES];
        double[] iotDeviceQueue = new double[NUM_IOT_DEVICES];
        int currentSourceDevice = 0;

        try (
                // Stream pembaca baris teks perintah dari Python
                BufferedReader in = new BufferedReader(new InputStreamReader(socket.getInputStream(), "UTF-8"));

                // Stream pengirim balasan teks JSON ke Python (auto-flush = true)
                PrintWriter out = new PrintWriter(new OutputStreamWriter(socket.getOutputStream(), "UTF-8"), true)) {
            String line;

            // Membaca perintah baris demi baris dari socket
            while ((line = in.readLine()) != null) {
                line = line.trim();
                if (line.isEmpty())
                    continue;

                // =====================================================================
                // PERINTAH 1: "RESET <workload> <seed>"
                // Menginisialisasi ulang lingkungan untuk memulai episode simulasi baru.
                // =====================================================================
                if (line.startsWith("RESET")) {
                    String[] parts = line.split("\\s+");

                    // Membaca parameter workload (parts[1]) jika disediakan
                    if (parts.length > 1)
                        currentWorkload = parts[1];

                    // Membaca parameter seed deterministik (parts[2]) untuk Paired Seed Protocol
                    if (parts.length > 2) {
                        try {
                            random = new Random(Long.parseLong(parts[2]));
                        } catch (NumberFormatException ignored) {
                        }
                    }

                    // Reset penghitung langkah episode
                    currentStep = 0;

                    // Menyesuaikan batas langkah episode berdasarkan skenario beban
                    switch (currentWorkload.toLowerCase()) {
                        case "light":
                            maxSteps = 50; // Beban ringan: 50 timestep
                            break;
                        case "heavy":
                            maxSteps = 150; // Beban padat/stres: 150 timestep
                            break;
                        case "dynamic":
                        case "moderate":
                        default:
                            maxSteps = 100; // Beban standar/dinamis: 100 timestep
                            break;
                    }

                    // -----------------------------------------------------------------
                    // Inisialisasi Fitur Observasi 46 Dimensi & Fleet 100 Perangkat IoT:
                    // -----------------------------------------------------------------

                    // Inisialisasi 100 Perangkat IoT
                    for (int d = 0; d < NUM_IOT_DEVICES; d++) {
                        iotDeviceCpu[d] = 0.10 + (0.25 * random.nextDouble());
                        iotDeviceBattery[d] = 0.65 + (0.35 * random.nextDouble());
                        iotDeviceQueue[d] = 0.08 * random.nextDouble();
                    }
                    currentSourceDevice = random.nextInt(NUM_IOT_DEVICES);

                    // 1. Inisialisasi Utilisasi CPU Awal ([0..6]):
                    // - Node 0: mewakili CPU perangkat pemohon saat ini (currentSourceDevice)
                    // - Node 1..5: Fog Nodes (20% - 40%)
                    // - Node 6: Cloud Server (10% - 30%)
                    currentState[0] = iotDeviceCpu[currentSourceDevice];
                    for (int i = 1; i < 6; i++) {
                        currentState[i] = 0.2 + (0.2 * random.nextDouble());
                    }
                    currentState[6] = 0.1 + (0.2 * random.nextDouble());

                    // 2. Inisialisasi Ketersediaan RAM ([7..13]): Nilai heterogen 0.3 - 0.7
                    for (int i = 7; i < 14; i++) {
                        currentState[i] = 0.3 + (0.4 * random.nextDouble());
                    }

                    // 3. Inisialisasi Alokasi Bandwidth Jaringan ([14..20]): Nilai 0.4 - 0.8
                    for (int i = 14; i < 21; i++) {
                        currentState[i] = 0.4 + (0.4 * random.nextDouble());
                    }

                    // 4. Inisialisasi Latensi Link Jaringan ([21..27]):
                    // - Node 0 (Lokal): Latensi link = 0.0 ms (tanpa transmisi nirkabel)
                    // - Node 1..5 (Fog): Latensi link nirkabel rendah 0.15 - 0.35 (15-35 ms)
                    // - Node 6 (Cloud): Latensi link WAN jarak jauh 0.65 - 0.85 (65-85 ms)
                    currentState[21] = 0.0;
                    for (int i = 22; i < 27; i++) {
                        currentState[i] = 0.15 + (0.2 * random.nextDouble());
                    }
                    currentState[27] = 0.65 + (0.2 * random.nextDouble());

                    // 5. Inisialisasi Panjang Antrean Awal ([28..34]):
                    currentState[28] = iotDeviceQueue[currentSourceDevice];
                    for (int i = 29; i < 35; i++) {
                        currentState[i] = 0.05 + (0.20 * random.nextDouble());
                    }

                    // 6. Inisialisasi Riwayat Konsumsi Energi ([35..41]):
                    currentState[35] = Math.max(0.0, 1.0 - iotDeviceBattery[currentSourceDevice]);
                    for (int i = 36; i < 42; i++) {
                        currentState[i] = 0.10 + (0.30 * random.nextDouble());
                    }

                    // 7. Profil Tugas Baru yang Pertama Kali Tiba ([42..45]):
                    currentState[42] = 0.2 + (0.6 * random.nextDouble()); // Ukuran data payload (task data size)
                    currentState[43] = 0.2 + (0.6 * random.nextDouble()); // Panjang komputasi MI (task computation)
                    currentState[44] = 0.3 + (0.5 * random.nextDouble()); // Batas waktu toleransi (task deadline)
                    currentState[45] = 0.2 + (0.8 * random.nextDouble()); // Derajat prioritas QoS (task priority)

                    // Hitung rata-rata baterai fleet
                    double bSum = 0.0;
                    int bDep = 0;
                    for (int d = 0; d < NUM_IOT_DEVICES; d++) {
                        bSum += iotDeviceBattery[d];
                        if (iotDeviceBattery[d] < 0.10) bDep++;
                    }
                    double meanFleetBatt = bSum / NUM_IOT_DEVICES;

                    // Membangun string balasan JSON status reset
                    StringBuilder sb = new StringBuilder();
                    sb.append("{\"status\":\"ok\",\"obs\":[");
                    for (int i = 0; i < STATE_DIM; i++) {
                        sb.append(String.format(Locale.US, "%.5f", currentState[i]));
                        if (i < STATE_DIM - 1)
                            sb.append(",");
                    }
                    sb.append("],\"step\":0,\"workload\":\"").append(currentWorkload).append("\",");
                    sb.append("\"source_device_id\":").append(currentSourceDevice).append(",");
                    sb.append("\"mean_fleet_battery\":").append(String.format(Locale.US, "%.4f", meanFleetBatt)).append(",");
                    sb.append("\"depleted_devices_count\":").append(bDep).append(",");
                    sb.append("\"devices_battery\":[");
                    for (int d = 0; d < NUM_IOT_DEVICES; d++) {
                        sb.append(String.format(Locale.US, "%.3f", iotDeviceBattery[d]));
                        if (d < NUM_IOT_DEVICES - 1) sb.append(",");
                    }
                    sb.append("]}");

                    // Mengirimkan observasi awal ke Python
                    out.println(sb.toString());

                    // =====================================================================
                    // PERINTAH 2: "STEP <action>"
                    // Menerima aksi penempatan tugas (a_t: 0-6), mengeksekusi pemodelan fisik,
                    // menghitung sub-reward, dan memperbarui state untuk langkah berikutnya.
                    // =====================================================================
                } else if (line.startsWith("STEP")) {
                    currentStep++;
                    String[] parts = line.split("\\s+");

                    // Membaca aksi offloading integer (parts[1])
                    int action = 0;
                    if (parts.length > 1) {
                        try {
                            action = Integer.parseInt(parts[1]);
                        } catch (NumberFormatException ignored) {
                        }
                    }

                    // Validasi batas indeks node target (0 s/d 6)
                    int targetNode = Math.max(0, Math.min(NUM_NODES - 1, action));

                    // Ekstraksi parameter node target dari state saat ini
                    double nodeCpuLoad = currentState[targetNode];
                    double nodeNetLatency = currentState[21 + targetNode];
                    double nodeQueueLoad = currentState[28 + targetNode];

                    // Ekstraksi atribut tugas yang sedang diproses
                    double taskDataSize = currentState[42]; // Ukuran data
                    double taskMi = currentState[43]; // Kompleksitas instruksi CPU
                    double taskDeadline = currentState[44]; // Batas waktu SLA
                    double taskPriority = currentState[45]; // Tingkat kepentingan QoS

                    // Variabel fisik simulasi yang akan dihitung
                    double transTime; // Waktu transmisi jaringan nirkabel/WAN
                    double execTime; // Waktu eksekusi komputasi pada CPU node
                    double queueTime; // Waktu tunggu di antrean buffer node
                    double energySpent; // Konsumsi daya listrik baterai perangkat IoT lokal

                    // -----------------------------------------------------------------
                    // PEMODELAN FISIK KOMPUTASI & JARINGAN 3-TIER (BROKER 100 PERANGKAT):
                    // -----------------------------------------------------------------
                    int srcDev = currentSourceDevice;

                    if (targetNode == 0) {
                        // KASUS A: Eksekusi Lokal di Perangkat IoT Pemohon (srcDev)
                        transTime = 0.0;
                        execTime = 1.60 * taskMi * (1.0 + iotDeviceCpu[srcDev]);
                        queueTime = iotDeviceQueue[srcDev] * 0.60;
                        energySpent = 1.25 * taskMi;

                        // Pengurangan baterai nyata pada perangkat pemohon
                        double drain = 0.04 * taskMi * (1.0 + iotDeviceCpu[srcDev]);
                        iotDeviceBattery[srcDev] = Math.max(0.0, iotDeviceBattery[srcDev] - drain);

                        // Penalti degradasi jika baterai kritis (< 8%)
                        if (iotDeviceBattery[srcDev] < 0.08) {
                            execTime *= 2.2;
                            energySpent *= 1.4;
                        }

                        // Kenaikan beban CPU dan antrean perangkat pemohon
                        iotDeviceCpu[srcDev] = Math.min(1.0, iotDeviceCpu[srcDev] + 0.22 * taskMi);
                        iotDeviceQueue[srcDev] = Math.min(1.0, iotDeviceQueue[srcDev] + 0.25 * taskDataSize);

                    } else if (targetNode >= 1 && targetNode <= 5) {
                        // KASUS B: Offloading ke Fog Nodes Terdistribusi (Node 1 s/d 5)
                        transTime = 0.35 * taskDataSize * (1.0 + nodeNetLatency);
                        execTime = 0.45 * taskMi * (1.0 + nodeCpuLoad);
                        queueTime = nodeQueueLoad * 0.35;
                        energySpent = 0.25 * taskDataSize * (1.0 + nodeNetLatency);

                        // Pengurangan baterai ringan untuk transmisi nirkabel
                        double drain = 0.006 * taskDataSize * (1.0 + nodeNetLatency);
                        iotDeviceBattery[srcDev] = Math.max(0.0, iotDeviceBattery[srcDev] - drain);

                        // Beban Fog Node terpilih meningkat
                        currentState[targetNode] = Math.min(1.0, currentState[targetNode] + 0.20 * taskMi);
                        currentState[28 + targetNode] = Math.min(1.0, currentState[28 + targetNode] + 0.25 * taskDataSize);

                    } else {
                        // KASUS C: Offloading ke Cloud Data Center Terpusat (Node 6)
                        transTime = 1.15 * taskDataSize * (1.0 + nodeNetLatency);
                        execTime = 0.10 * taskMi * (1.0 + nodeCpuLoad);
                        queueTime = nodeQueueLoad * 0.15;
                        energySpent = 0.45 * taskDataSize * (1.0 + nodeNetLatency);

                        // Pengurangan baterai sedang untuk transmisi WAN
                        double drain = 0.012 * taskDataSize * (1.0 + nodeNetLatency);
                        iotDeviceBattery[srcDev] = Math.max(0.0, iotDeviceBattery[srcDev] - drain);

                        // Beban Cloud meningkat
                        currentState[6] = Math.min(1.0, currentState[6] + 0.10 * taskMi);
                        currentState[28 + 6] = Math.min(1.0, currentState[28 + 6] + 0.15 * taskDataSize);
                    }

                    // -----------------------------------------------------------------
                    // PERHITUNGAN 4 PARAMETER SUB-REWARD MULTI-OBJEKTIF:
                    // -----------------------------------------------------------------

                    // 1. Total Latensi dan Sub-Reward Latensi (alpha)
                    double totalLatency = transTime + queueTime + execTime;
                    double rLatency = Math.min(1.0, Math.max(0.0, Math.exp(-1.30 * totalLatency)));

                    // 2. Sub-Reward Efisiensi Energi Baterai IoT (beta)
                    double rEnergy = Math.min(1.0, Math.max(0.0, 1.0 - (energySpent / 1.50)));

                    // 3. Sub-Reward Kepatuhan Batas Waktu SLA / Deadline (lambda)
                    boolean isViolated = totalLatency > (taskDeadline * 1.35);
                    double rDeadline = isViolated ? 0.0 : 1.0;

                    // 4. Sub-Reward Kepuasan Kualitas Layanan / QoS (gamma)
                    double qosFactor = (1.0 - nodeQueueLoad) * (1.0 - nodeCpuLoad);
                    double rQoS = isViolated ? Math.min(1.0, Math.max(0.0, 0.15 * qosFactor))
                            : Math.min(1.0, Math.max(0.0, 0.65 * qosFactor + 0.35 * taskPriority));

                    // -----------------------------------------------------------------
                    // UPDATE DINAMIKA BEBAN BERBASIS AKSI:
                    // -----------------------------------------------------------------

                    // Peluruhan alami Fog Nodes 1..5 dan Cloud yang tidak dipilih
                    for (int i = 1; i < NUM_NODES; i++) {
                        if (i != targetNode) {
                            currentState[i] = Math.max(0.05, currentState[i] - 0.08);
                            currentState[28 + i] = Math.max(0.0, currentState[28 + i] - 0.10);
                        }
                    }

                    // Peluruhan alami 99 perangkat IoT lainnya yang idle
                    for (int d = 0; d < NUM_IOT_DEVICES; d++) {
                        if (d != srcDev) {
                            iotDeviceCpu[d] = Math.max(0.05, iotDeviceCpu[d] - 0.05);
                            iotDeviceQueue[d] = Math.max(0.0, iotDeviceQueue[d] - 0.08);
                            if (iotDeviceBattery[d] < 1.0) {
                                iotDeviceBattery[d] = Math.min(1.0, iotDeviceBattery[d] + 0.0008);
                            }
                        }
                    }

                    // Pemilihan perangkat IoT yang menghasilkan tugas berikutnya
                    int nextSourceDevice = random.nextInt(NUM_IOT_DEVICES);
                    currentSourceDevice = nextSourceDevice;

                    // Update observasi indeks 0, 28, 35 dengan profil perangkat pemohon berikutnya
                    currentState[0] = iotDeviceCpu[nextSourceDevice];
                    currentState[28] = iotDeviceQueue[nextSourceDevice];
                    currentState[35] = Math.max(0.0, 1.0 - iotDeviceBattery[nextSourceDevice]);

                    // Membangkitkan karakteristik profil tugas baru yang tiba untuk timestep berikutnya
                    currentState[42] = 0.15 + 0.70 * random.nextDouble(); // Data size baru
                    currentState[43] = 0.15 + 0.70 * random.nextDouble(); // MI length baru
                    currentState[44] = 0.25 + 0.55 * random.nextDouble(); // Deadline baru
                    currentState[45] = 0.10 + 0.90 * random.nextDouble(); // Prioritas QoS baru

                    // -----------------------------------------------------------------
                    // PERHITUNGAN STANDAR DEVIASI LOAD IMBALANCE (sigma_CPU):
                    // -----------------------------------------------------------------
                    double sum = 0.0;
                    for (int i = 0; i < NUM_NODES; i++)
                        sum += currentState[i];
                    double mean = sum / NUM_NODES;

                    double varSum = 0.0;
                    for (int i = 0; i < NUM_NODES; i++) {
                        varSum += Math.pow(currentState[i] - mean, 2);
                    }
                    double loadImbalance = Math.sqrt(varSum / NUM_NODES);

                    // Kondisi selesai
                    boolean done = false;
                    boolean truncated = currentStep >= maxSteps;

                    // Statistik baterai fleet 100 perangkat
                    double fleetBattSum = 0.0;
                    int fleetDepleted = 0;
                    for (int d = 0; d < NUM_IOT_DEVICES; d++) {
                        fleetBattSum += iotDeviceBattery[d];
                        if (iotDeviceBattery[d] < 0.10) fleetDepleted++;
                    }
                    double meanFleetBatt = fleetBattSum / NUM_IOT_DEVICES;

                    // -----------------------------------------------------------------
                    // FORMATTING DAN PENGIRIMAN RESPON JSON KE PYTHON:
                    // -----------------------------------------------------------------
                    StringBuilder sb = new StringBuilder();
                    sb.append("{");
                    sb.append("\"status\":\"ok\",");

                    // Array observasi state 46 dimensi
                    sb.append("\"obs\":[");
                    for (int i = 0; i < STATE_DIM; i++) {
                        sb.append(String.format(Locale.US, "%.5f", currentState[i]));
                        if (i < STATE_DIM - 1)
                            sb.append(",");
                    }
                    sb.append("],");

                    // Array 4 sub-reward [r_latency, r_energy, r_deadline, r_qos]
                    sb.append("\"sub_rewards\":[")
                            .append(String.format(Locale.US, "%.5f", rLatency)).append(",")
                            .append(String.format(Locale.US, "%.5f", rEnergy)).append(",")
                            .append(String.format(Locale.US, "%.5f", rDeadline)).append(",")
                            .append(String.format(Locale.US, "%.5f", rQoS)).append("],");

                    // Metrik diagnostik performa tambahan
                    sb.append("\"total_latency\":").append(String.format(Locale.US, "%.5f", totalLatency)).append(",");
                    sb.append("\"energy_spent\":").append(String.format(Locale.US, "%.5f", energySpent)).append(",");
                    sb.append("\"load_imbalance\":").append(String.format(Locale.US, "%.5f", loadImbalance)).append(",");
                    sb.append("\"is_violated\":").append(isViolated).append(",");
                    sb.append("\"target_node\":").append(targetNode).append(",");
                    sb.append("\"step\":").append(currentStep).append(",");
                    sb.append("\"done\":").append(done).append(",");
                    sb.append("\"truncated\":").append(truncated).append(",");
                    sb.append("\"source_device_id\":").append(srcDev).append(",");
                    sb.append("\"mean_fleet_battery\":").append(String.format(Locale.US, "%.4f", meanFleetBatt)).append(",");
                    sb.append("\"depleted_devices_count\":").append(fleetDepleted).append(",");
                    sb.append("\"devices_battery\":[");
                    for (int d = 0; d < NUM_IOT_DEVICES; d++) {
                        sb.append(String.format(Locale.US, "%.3f", iotDeviceBattery[d]));
                        if (d < NUM_IOT_DEVICES - 1) sb.append(",");
                    }
                    sb.append("]}");

                    // Mengirimkan baris JSON ke socket Python
                    out.println(sb.toString());

                    // =====================================================================
                    // PERINTAH 3: "CLOSE"
                    // Menutup koneksi sesi client secara bersih.
                    // =====================================================================
                } else if (line.startsWith("CLOSE")) {
                    out.println("CLOSE_ACK");
                    break;

                    // =====================================================================
                    // PERINTAH 4: "PING"
                    // Uji liveness koneksi TCP socket.
                    // =====================================================================
                } else if (line.startsWith("PING")) {
                    out.println("PONG");
                }
            }
        } catch (IOException ignored) {
            // Menangani potensi pemutusan koneksi client secara normal
        } finally {
            try {
                // Pastikan client socket ditutup setelah selesai melayani loop perintah
                if (!socket.isClosed()) {
                    socket.close();
                }
            } catch (IOException ignored) {
            }
        }
    }

    /**
     * Menghentikan server socket secara aman dan mematikan thread pool.
     */
    public void stop() {
        isRunning = false;
        try {
            if (serverSocket != null && !serverSocket.isClosed()) {
                serverSocket.close();
            }
        } catch (IOException ignored) {
        }

        // Mematikan seluruh worker threads yang sedang berjalan di thread pool
        threadPool.shutdownNow();
        System.out.println("[iFogSim2-Server] Server dihentikan dengan aman.");
    }
}
