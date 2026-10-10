"""
plot_topology.py
----------------
Menghasilkan visualisasi diagram arsitektur topologi jaringan Fog-Cloud 3-Tier (Figure 1)
dan pemetaan konfigurasi perangkat iFogSim2 untuk naskah publikasi ilmiah (PNG 300 DPI & PDF).
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

OUTPUT_DIR = "figures"
os.makedirs(OUTPUT_DIR, exist_ok=True)

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "figure.autolayout": True,
})


def draw_network_topology():
    fig, ax = plt.subplots(figsize=(11, 7.2), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    # ==============================================================================
    # 1. LATAR BELAKANG 3 TIER LAYER
    # ==============================================================================
    # Tier 3: Cloud Layer
    rect_cloud = patches.FancyBboxPatch((3, 72), 94, 25, boxstyle="round,pad=1.0",
                                        facecolor="#f3e8fd", edgecolor="#9467bd", linewidth=1.8, linestyle="--", alpha=0.85)
    ax.add_patch(rect_cloud)
    ax.text(6, 93, "TIER 3: CLOUD DATA CENTER LAYER (High-Compute / High-Latency WAN)", fontsize=11, fontweight="bold", color="#6a1b9a")

    # Tier 2: Fog / Edge Layer
    rect_fog = patches.FancyBboxPatch((3, 33), 94, 35, boxstyle="round,pad=1.0",
                                      facecolor="#e8f5e9", edgecolor="#2ca02c", linewidth=1.8, linestyle="--", alpha=0.85)
    ax.add_patch(rect_fog)
    ax.text(6, 64, "TIER 2: DISTRIBUTED FOG / EDGE COMPUTING LAYER (Low-Latency Wireless)", fontsize=11, fontweight="bold", color="#1b5e20")

    # Tier 1: IoT End-Device Layer
    rect_iot = patches.FancyBboxPatch((3, 3), 94, 26, boxstyle="round,pad=1.0",
                                      facecolor="#fff3e0", edgecolor="#ff7f0e", linewidth=1.8, linestyle="--", alpha=0.85)
    ax.add_patch(rect_iot)
    ax.text(6, 25, "TIER 1: LOCAL IoT DEVICE / GATEWAY LAYER (Energy-Constrained)", fontsize=11, fontweight="bold", color="#e65100")

    # ==============================================================================
    # 2. NODE-NODE KOMPUTASI (7 TARGET NODES)
    # ==============================================================================
    
    # 2.1 Node 6: Cloud Data Center
    cloud_box = patches.FancyBboxPatch((36, 75), 28, 15, boxstyle="round,pad=0.8",
                                       facecolor="#7e57c2", edgecolor="#4a148c", linewidth=2.0)
    ax.add_patch(cloud_box)
    ax.text(50, 85.5, "Node 6: Cloud Data Center", fontsize=11, fontweight="bold", color="white", ha="center")
    ax.text(50, 81.5, "• CPU: 40,000 MIPS (Exec: 0.10x)\n• RAM: 64 GB | BW: 10 Gbps\n• WAN Latency: 65 - 85 ms",
            fontsize=8.5, color="#f3e5f5", ha="center")

    # 2.2 Node 1 s/d 5: Fog Nodes (Distributed)
    fog_x_positions = [10, 28, 46, 64, 82]
    for idx, x_pos in enumerate(fog_x_positions):
        node_id = idx + 1
        fog_box = patches.FancyBboxPatch((x_pos - 6.5, 37), 13, 21, boxstyle="round,pad=0.6",
                                         facecolor="#43a047", edgecolor="#1b5e20", linewidth=1.8)
        ax.add_patch(fog_box)
        ax.text(x_pos, 54, f"Node {node_id}\n(Fog Node {chr(65+idx)})", fontsize=9.5, fontweight="bold", color="white", ha="center")
        ax.text(x_pos, 44.5, f"• 4,000 MIPS\n• 8 GB RAM\n• 1 Gbps BW\n• Lat: 15-35ms\n• Exec: 0.45x",
                fontsize=7.8, color="#e8f8f5", ha="center")

    # 2.3 Node 0: Local IoT Gateway
    iot_box = patches.FancyBboxPatch((35, 6), 30, 16, boxstyle="round,pad=0.8",
                                     facecolor="#fb8c00", edgecolor="#b26a00", linewidth=2.0)
    ax.add_patch(iot_box)
    ax.text(50, 17.5, "Node 0: Local IoT Gateway / Device", fontsize=10.5, fontweight="bold", color="white", ha="center")
    ax.text(50, 12.0, "• CPU: 1,200 MIPS (Weak / Exec: 1.60x)\n• RAM: 2 GB | Battery: Limited (E: 1.25x)\n• Zero Wireless Transmission Latency (0.0 ms)",
            fontsize=8.2, color="#fff3e0", ha="center")

    # ==============================================================================
    # 3. KONEKSI LINK KOMUNIKASI & JALUR OFFLOADING (ARROWS)
    # ==============================================================================
    
    # IoT ke Fog Nodes (Wireless Links)
    for x_pos in fog_x_positions:
        ax.annotate(
            "", xy=(x_pos, 37), xytext=(50, 22),
            arrowprops=dict(arrowstyle="<->", color="#2e7d32", lw=1.5, linestyle="-", shrinkA=4, shrinkB=4)
        )

    # IoT ke Cloud (WAN Long-Distance Link)
    ax.annotate(
        "", xy=(50, 75), xytext=(50, 22),
        arrowprops=dict(arrowstyle="<->", color="#6a1b9a", lw=2.2, linestyle=":", shrinkA=4, shrinkB=4)
    )

    # Label Link WAN & Wireless
    ax.text(52, 28, "5G / Wi-Fi Links (Low Latency / Energy Efficient)", fontsize=8.5, color="#1b5e20", fontweight="bold")
    ax.text(51, 68.5, "WAN Backbone (High Propagation Delay)", fontsize=8.5, color="#6a1b9a", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#9467bd", alpha=0.9))

    # Clustering / Inter-Fog Links (Mesh)
    for i in range(len(fog_x_positions) - 1):
        ax.annotate(
            "", xy=(fog_x_positions[i+1] - 6.5, 48), xytext=(fog_x_positions[i] + 6.5, 48),
            arrowprops=dict(arrowstyle="<->", color="#388e3c", lw=1.2, linestyle="--")
        )
    ax.text(50, 34.5, "Inter-Fog Clustering & Load Sharing (Mesh Topology)", fontsize=8.0, color="#2e7d32", ha="center", style="italic")

    # ==============================================================================
    # 4. OVERLAY OBS (46D) & ACTION SPACE (0..6)
    # ==============================================================================
    obs_box = patches.FancyBboxPatch((71, 75), 25, 15, boxstyle="round,pad=0.5",
                                     facecolor="#ffffff", edgecolor="#333333", linewidth=1.2)
    ax.add_patch(obs_box)
    ax.text(83.5, 87, "46D State Vector Mapping", fontsize=8.5, fontweight="bold", color="#111111", ha="center")
    ax.text(83.5, 79.5, "[0:7] CPU Load  | [7:14] RAM Avail\n[14:21] Net BW  | [21:28] Link Lat\n[28:35] Queue   | [35:42] Energy\n[42:46] Task Profile (Data, MI, SLA)",
            fontsize=7.2, color="#333333", ha="center")

    action_box = patches.FancyBboxPatch((4, 75), 26, 15, boxstyle="round,pad=0.5",
                                       facecolor="#ffffff", edgecolor="#d62728", linewidth=1.2)
    ax.add_patch(action_box)
    ax.text(17, 87, "Action Space: Discrete(7)", fontsize=8.5, fontweight="bold", color="#d62728", ha="center")
    ax.text(17, 79.5, "• a = 0 : Local IoT Device\n• a = 1..5 : Fog Nodes 1..5\n• a = 6 : Cloud Server\nSelected by ERWO-PPO in ~0.53 ms",
            fontsize=7.2, color="#333333", ha="center")

    fig.suptitle("Figure 1: Hierarchical 3-Tier Fog-Cloud Network Topology & 7-Node Offloading Architecture", fontsize=13, y=0.99, fontweight="bold")
    plt.tight_layout()

    png_path = os.path.join(OUTPUT_DIR, "fig1_network_topology.png")
    pdf_path = os.path.join(OUTPUT_DIR, "fig1_network_topology.pdf")
    plt.savefig(png_path, dpi=300, bbox_inches="tight")
    plt.savefig(pdf_path, bbox_inches="tight")
    plt.close()
    print(f"[TOPOLOGY] Figure 1 tersimpan di: {png_path} dan {pdf_path}")


if __name__ == "__main__":
    draw_network_topology()
