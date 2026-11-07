"""P06 calibration report: figures (static SVG, light surface) and a Markdown report generated from the stored rows.

Colors follow the reference palette of the dataviz method: categorical slots 1-4 (validated for adjacent pairs, light mode),
the reserved status colors for outcome states, and one blue ramp for magnitude. Every figure is accompanied by the full
numbers in the report's tables, which is the table view the low-contrast slots require.
"""

import argparse
import json
from pathlib import Path
import subprocess

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

from .calibration import (MODES, OUTPUT_DIR, POLICY_ORDER, cell_means, calibration_trace, distribution_gate, evaluate_gates,
                          load_rows, solo_feasibility)
from .config import ROOT, load_config, sha256
from .schema_definitions import WORKLOADS
from .traces import TraceGenerator

SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
CATEGORICAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]            # slots 1-4 (validated, adjacent pairs, light mode)
STATUS = {"on_time": "#0ca30c", "late_success": "#fab219", "failed": "#d03b3b"}
STATUS_LABEL = {"on_time": "Tepat waktu", "late_success": "Terlambat (berhasil)", "failed": "Gagal"}
BLUE_RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
POLICY_LABEL = {"always_local": "Always-local", "nearest_fog": "Nearest-fog", "least_fog": "Least Fog", "greedy_eft": "Greedy-EFT"}
WORKLOAD_LABEL = {"light": "Light", "moderate": "Moderate", "heavy": "Heavy", "dynamic": "Dynamic"}
MODE_LABEL = {"heterogeneous": "fog heterogen (utama)", "homogeneous": "fog homogen (kontrol)"}


def style():
    plt.rcParams.update({
        "svg.fonttype": "none", "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"], "font.size": 9,
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "text.color": INK, "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED,
        "axes.edgecolor": AXIS, "axes.spines.top": False, "axes.spines.right": False, "grid.color": GRID, "grid.linewidth": 0.8,
    })


def save(fig, path):
    fig.savefig(path, format=Path(path).suffix.lstrip(".") or "svg", bbox_inches="tight", dpi=110)
    plt.close(fig)


def figure_arrival(config, generator, path):
    """Trend over time, four series: mean arrival rate per 15 s interval across the 20 calibration traces."""
    style()
    low, high = config["seeds"]["calibration_trace_ids"]
    count = high - low + 1
    edges = [config["timing"]["arrival_window_s"] * i / 4 for i in range(5)]
    centers = [(edges[i] + edges[i + 1]) / 2 for i in range(4)]
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    for color, workload in zip(CATEGORICAL, WORKLOADS):
        totals = [0] * 4
        for trace_id in range(low, high + 1):
            for task in calibration_trace(generator, config, workload, trace_id)["tasks"]:
                totals[min(3, int(task["arrival_s"] // 15))] += 1
        rates = [t / count / 15.0 for t in totals]
        ax.plot(centers, rates, color=color, linewidth=1.5, marker="o", markersize=6, markeredgecolor=SURFACE, markeredgewidth=1.0, label=WORKLOAD_LABEL[workload])
        if workload == "dynamic":      # ends at the same height as Light; label the burst instead
            peak = max(range(4), key=lambda i: rates[i])
            ax.annotate(WORKLOAD_LABEL[workload], (centers[peak], rates[peak]), xytext=(0, 9), textcoords="offset points", ha="center", color=INK2, fontsize=9)
        else:
            ax.annotate(WORKLOAD_LABEL[workload], (centers[-1], rates[-1]), xytext=(8, 0), textcoords="offset points", va="center", color=INK2, fontsize=9)
    ax.set_xlabel("Waktu (s), pusat interval 15 s")
    ax.set_ylabel("Laju kedatangan (tugas/s)")
    ax.set_xticks(centers)
    ax.set_xlim(0, 72)
    ax.set_ylim(0, 40)
    ax.grid(axis="y")
    ax.set_title("Laju kedatangan per interval: rata-rata 20 trace kalibrasi", loc="left", color=INK, fontsize=10)
    ax.legend(frameon=False, loc="upper left", ncol=2, labelcolor=INK2)
    save(fig, path)


def figure_solo(feasibility, threshold, path):
    """One value against a limit, two configurations: a dot plot, because the point is the margin over the threshold."""
    style()
    rows = [("Kelas light", lambda f: f["by_class"]["light"]["fraction"]), ("Kelas medium", lambda f: f["by_class"]["medium"]["fraction"]),
            ("Kelas heavy", lambda f: f["by_class"]["heavy"]["fraction"]), ("Semua tugas", lambda f: f["fraction"])]
    fig, ax = plt.subplots(figsize=(6.4, 3.3))
    for row, (label, getter) in enumerate(rows):
        for offset, mode, color in ((-0.14, "heterogeneous", CATEGORICAL[0]), (0.14, "homogeneous", CATEGORICAL[1])):
            value = getter(feasibility[mode]) * 100
            ax.plot(value, row + offset, marker="o", markersize=8, color=color, markeredgecolor=SURFACE, markeredgewidth=1.5, linestyle="none",
                    label=MODE_LABEL[mode] if row == 0 else None, zorder=3)
            ax.annotate(f"{value:.1f}", (value, row + offset), xytext=(9, 0), textcoords="offset points", va="center", fontsize=8, color=INK2)
    ax.axvline(threshold * 100, color=INK2, linewidth=1.0, linestyle=(0, (4, 3)), zorder=1)
    ax.annotate(f"ambang {threshold * 100:.0f}%", (threshold * 100, 3.62), xytext=(-5, 0), textcoords="offset points", ha="right", va="center", color=INK2, fontsize=8)
    ax.set_yticks(range(4))
    ax.set_yticklabels([r[0] for r in rows])
    ax.set_ylim(3.85, -0.6)
    ax.set_xlim(93, 101.2)
    ax.set_xlabel("Tugas dengan rute layak (%); sumbu mulai dari 93%")
    ax.grid(axis="x")
    ax.set_axisbelow(True)
    ax.set_title("Kelayakan solo-task: ada tujuan yang memenuhi deadline tanpa antrean", loc="left", color=INK, fontsize=10)
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.26), ncol=2, labelcolor=INK2)
    save(fig, path)


def figure_status(cells, mode, path):
    """Part-to-whole per policy, one panel per workload: share of tasks on time, late-but-served, and failed (status colors)."""
    style()
    fig, axes = plt.subplots(1, 4, figsize=(11.5, 2.9), sharey=True)
    for ax, workload in zip(axes, WORKLOADS):
        for row, policy in enumerate(reversed(POLICY_ORDER)):
            cell = cells[(mode, policy, workload)]
            left = 0.0
            for key in ("on_time", "late_success", "failed"):
                width = cell[key] * 100
                ax.barh(row, width, left=left, height=0.62, color=STATUS[key], edgecolor=SURFACE, linewidth=1.5)
                if width >= 9:
                    ax.text(left + width / 2, row, f"{width:.0f}", ha="center", va="center", fontsize=8, color=INK if key == "late_success" else "#ffffff")
                left += width
        ax.set_xlim(0, 100)
        ax.set_yticks(range(4))
        ax.set_yticklabels([POLICY_LABEL[p] for p in reversed(POLICY_ORDER)])
        ax.set_title(WORKLOAD_LABEL[workload], loc="left", color=INK, fontsize=10)
        ax.set_xlabel("% tugas")
        ax.grid(axis="x")
        ax.set_axisbelow(True)
    handles = [plt.Rectangle((0, 0), 1, 1, color=STATUS[k]) for k in STATUS]
    fig.legend(handles, [STATUS_LABEL[k] for k in STATUS], loc="upper center", ncol=3, frameon=False, labelcolor=INK2, bbox_to_anchor=(0.5, 1.08))
    fig.suptitle(f"Status akhir tugas per baseline, {MODE_LABEL[mode]}", x=0.01, ha="left", y=1.17, color=INK, fontsize=10)
    save(fig, path)


def _ink_for(rgba):
    """White text on dark cells, near-black on light ones, chosen from relative luminance (WCAG)."""
    channel = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    luminance = 0.2126 * channel(rgba[0]) + 0.7152 * channel(rgba[1]) + 0.0722 * channel(rgba[2])
    return "#ffffff" if luminance < 0.30 else INK


def figure_pressure(cells, mode, path):
    """Magnitude on a baseline x workload grid, one blue ramp per panel: queue, utilization and energy pressure."""
    style()
    panels = [("Utilisasi kanal akses, maks per trace (0-1)", lambda c: c["pressure"]["access_utilization_max"], "{:.2f}"),
              ("Antrean kanal akses, maks (pesan)", lambda c: c["pressure"]["access_queue_max"], "{:.0f}"),
              ("Utilisasi CPU fog, rata-rata (0-1)", lambda c: c["pressure"]["fog_cpu_utilization_mean"], "{:.2f}"),
              ("Energi dinamis (J)", lambda c: c["energy_dynamic_j"], "{:,.0f}")]
    cmap = LinearSegmentedColormap.from_list("blue", BLUE_RAMP)
    fig, axes = plt.subplots(1, 4, figsize=(13, 2.8))
    for ax, (title, getter, fmt) in zip(axes, panels):
        grid = [[getter(cells[(mode, p, w)]) for w in WORKLOADS] for p in POLICY_ORDER]
        top = max(max(r) for r in grid) or 1.0
        ax.imshow(grid, cmap=cmap, vmin=0, vmax=top, aspect="auto")
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                ax.text(c, r, fmt.format(value), ha="center", va="center", fontsize=8, color=_ink_for(cmap(value / top)))
        ax.set_xticks(range(4))
        ax.set_xticklabels([WORKLOAD_LABEL[w] for w in WORKLOADS], fontsize=8)
        ax.set_yticks(range(4))
        ax.set_yticklabels([POLICY_LABEL[p] for p in POLICY_ORDER] if ax is axes[0] else [])
        ax.set_title(title, loc="left", color=INK, fontsize=9)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.tick_params(length=0)
    fig.suptitle(f"Tekanan sumber daya, {MODE_LABEL[mode]} (rata-rata 20 trace; sel lebih gelap = lebih besar)", x=0.01, ha="left", y=1.12, color=INK, fontsize=10)
    save(fig, path)


# ---- Markdown ------------------------------------------------------------------------------------------------

def pct(x):
    return f"{100 * x:.1f}"


def table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" if i == 0 else "---:" for i in range(len(header))) + "|"]
    out += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(out)


def build_markdown(gates, feasibility, cells, config):
    lines = ["# Laporan kalibrasi P06", "",
             "Dibangkitkan oleh `python -m research_v2.calibration_report` dari `rows-*.jsonl`. Hanya empat baseline deterministik pada split "
             "`calibration` (20 trace per workload); ERWO/PPO tidak digunakan untuk memilih skenario. Setiap sel adalah rata-rata 20 trace.", ""]
    status = lambda ok: "LULUS" if ok else "**GAGAL**"
    lines += ["## Gerbang (§24.2)", "",
              table(["Gerbang", "Hasil", "Rincian"], [
                  ["Kelengkapan (640 episode)", status(gates["complete"]["pass"]), f"{gates['complete']['episodes']} dari {gates['complete']['expected']}"],
                  ["Distribusi trace (80 trace, pemeriksaan P01)", status(gates["distribution"]["pass"]), f"{gates['distribution']['traces']} trace"],
                  ["Kelayakan solo-task ≥ 95%", status(gates["solo_feasibility"]["pass"]),
                   "; ".join(f"{m}: {pct(v['fraction'])}%" for m, v in gates["solo_feasibility"]["by_mode"].items())],
                  ["Tekanan heavy: gagal > 1% dan reliability > 50%", status(gates["heavy_pressure"]["pass"]),
                   ", ".join(gates["heavy_pressure"]["passing_conditions"]) or "tidak ada kondisi yang memenuhi"],
              ]), "", f"**Keputusan: {'semua gerbang lulus' if gates['all_pass'] else 'ADA GERBANG YANG GAGAL; berhenti dan diagnosis, jangan menyetel parameter.'}**", ""]
    lines += ["## Kelayakan solo-task", "",
              "Satu tugas sendirian pada sistem kosong; tugas layak bila ada tujuan (dari tujuh) yang menerima hasil sebelum deadline lunak D. "
              "Dihitung analitis dan diverifikasi terhadap engine pada tes.", ""]
    rows = []
    for mode in MODES:
        f = feasibility[mode]
        rows.append([MODE_LABEL[mode], f["tasks"], pct(f["fraction"])] + [pct(f["by_class"][c]["fraction"]) for c in ("light", "medium", "heavy")]
                    + [pct(f["by_workload"][w]["fraction"]) for w in WORKLOADS])
    lines += [table(["Konfigurasi", "Tugas", "Semua %", "Kelas light %", "Kelas medium %", "Kelas heavy %"] + [f"Workload {WORKLOAD_LABEL[w]} %" for w in WORKLOADS], rows), "",
              "![Kelayakan solo-task](solo_feasibility.svg)", ""]
    lines += ["## Laju kedatangan", "", "![Laju kedatangan](arrival_rate.svg)", ""]
    for mode in MODES:
        lines += [f"## Hasil baseline, {MODE_LABEL[mode]}", ""]
        rows = []
        for workload in WORKLOADS:
            for policy in POLICY_ORDER:
                c = cells[(mode, policy, workload)]
                rows.append([WORKLOAD_LABEL[workload], POLICY_LABEL[policy], f"{c['tasks_mean']:.0f}", pct(c["on_time"]), pct(c["late_success"]), pct(c["failed"]),
                             f"{c['reliability']:.3f}", f"{c['D']:.3f}", " ".join(f"{c['costs'][k]:.3f}" for k in ("zL", "zE", "zD", "zB", "zQ"))])
        lines += [table(["Workload", "Baseline", "N", "Tepat waktu %", "Terlambat %", "Gagal %", "Reliability", "D", "zL zE zD zB zQ"], rows), "",
                  f"![Status tugas, {mode}](status_{mode}.svg)", ""]
        rows = []
        for workload in WORKLOADS:
            for policy in POLICY_ORDER:
                c = cells[(mode, policy, workload)]
                p, r = c["pressure"], c["failure_reasons"]
                rows.append([WORKLOAD_LABEL[workload], POLICY_LABEL[policy], f"{p['access_utilization_max']:.2f}", f"{p['access_queue_max']:.1f}",
                             f"{p['fog_cpu_utilization_mean']:.2f}", f"{p['iot_queue_max']:.1f}", f"{p['cpu_queue_rejections']:.1f}",
                             f"{p['network_queue_rejections']:.1f}", pct(r["SERVICE_TIMEOUT"]), f"{c['energy_dynamic_j']:,.0f}"])
        lines += ["### Tekanan sumber daya", "",
                  table(["Workload", "Baseline", "Util. akses maks", "Antrean akses maks", "Util. CPU fog", "Antrean IoT maks", "Tolak antrean CPU",
                         "Tolak antrean jaringan", "Timeout %", "E dinamis (J)"], rows), "",
                  f"![Tekanan sumber daya, {mode}](pressure_{mode}.svg)", ""]
        rows = [[WORKLOAD_LABEL[w], POLICY_LABEL[p]] + [pct(s) for s in cells[(mode, p, w)]["action_share"]] for w in WORKLOADS for p in POLICY_ORDER]
        lines += ["### Pembagian aksi (% keputusan)", "", table(["Workload", "Baseline", "IoT asal", "F1", "F2", "F3", "F4", "F5", "Cloud"], rows), ""]
        rows = [[WORKLOAD_LABEL[w], f"{cells[(mode, 'greedy_eft', w)]['eft_estimator']['mean_error_s']:+.3f}",
                 f"{cells[(mode, 'greedy_eft', w)]['eft_estimator']['median_abs_error_s']:.3f}",
                 f"{cells[(mode, 'greedy_eft', w)]['eft_estimator']['p95_abs_error_s']:.3f}",
                 pct(cells[(mode, 'greedy_eft', w)]['eft_estimator']['share_realized_not_below_estimate'])] for w in WORKLOADS]
        lines += ["### Estimator EFT sebagai estimator (bukan outcome)", "",
                  "Skor EFT tujuan terpilih dibandingkan dengan latensi nyata tugas yang berhasil (nyata − estimasi). Ini diagnostik, bukan gerbang.", "",
                  table(["Workload", "Rata-rata galat (s)", "Median |galat| (s)", "p95 |galat| (s)", "% nyata ≥ estimasi"], rows), ""]
    diagnostics = gates["diagnostics"]
    lines += ["## Diagnostik: trivial, infeasible, atau kurang teridentifikasi?", "",
              f"- Rentang reliability seluruh sel: {diagnostics['reliability_min']:.3f} sampai {diagnostics['reliability_max']:.3f}. "
              f"Semua sel > 0,99 (trivial): {diagnostics['every_cell_reliability_above_0_99']}. Semua sel < 0,01 (runtuh): {diagnostics['every_cell_reliability_below_0_01']}.",
              "- Rentang D antar baseline per kondisi (D terkecil, terbesar, selisih):", ""]
    lines += [table(["Kondisi", "D min", "D maks", "Selisih"], [[k, f"{v['D_min']:.3f}", f"{v['D_max']:.3f}", f"{v['range']:.3f}"] for k, v in diagnostics["D_spread_across_policies"].items()]), ""]
    lines += ["Urutan kemenangan antar baseline **bukan** kriteria kalibrasi (§24.2); tabel di atas hanya menunjukkan apakah pilihan aksi berpengaruh pada hasil.", ""]
    return "\n".join(lines) + "\n"


def compute_summary(output_dir=OUTPUT_DIR):
    """Everything the report states, recomputed from the stored rows and the traces; writes nothing."""
    output_dir = Path(output_dir)
    config = load_config()
    generator = TraceGenerator(config)
    rows = load_rows(output_dir)
    cells = cell_means(rows)
    feasibility = {}
    low, high = config["seeds"]["calibration_trace_ids"]
    traces = [calibration_trace(generator, config, w, i) for w in WORKLOADS for i in range(low, high + 1)]
    for mode, homogeneous in MODES.items():
        feasibility[mode] = solo_feasibility(traces, config, homogeneous)
    gates = evaluate_gates(rows, feasibility, config, distribution_gate(config, generator))
    return {"config_sha256": sha256(config), "gates": gates, "solo_feasibility": feasibility,
            "cells": {f"{m}/{p}/{w}": c for (m, p, w), c in sorted(cells.items())}}, rows, cells, config, generator


def parameter_snapshot(rows, config):
    """What was calibrated: full config, thresholds, gate definitions and the builds that produced the rows."""
    from .calibration import evaluate_gates as gate_function
    jars = sorted({(r.get("provenance") or {}).get("jar_sha256") for r in rows} - {None})
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        head = None
    return {"purpose": "P06 calibration of the physical model with four deterministic reference policies; no ERWO/PPO result is used",
            "config_sha256": sha256(config), "config": config, "jar_sha256_of_rows": jars, "git_head_at_report_time": head,
            "calibration_trace_ids": config["seeds"]["calibration_trace_ids"], "workloads": list(WORKLOADS),
            "configurations": {m: {"homogeneous_fog": h} for m, h in MODES.items()}, "policies": list(POLICY_ORDER),
            "episodes": len(rows), "thresholds": config["pilot"], "gate_definitions": " ".join(gate_function.__doc__.split())}


def generate(output_dir=OUTPUT_DIR):
    output_dir = Path(output_dir)
    summary, rows, cells, config, generator = compute_summary(output_dir)
    (output_dir / "parameter_snapshot.json").write_text(json.dumps(parameter_snapshot(rows, config), indent=2) + "\n", encoding="utf-8")
    gates, feasibility = summary["gates"], summary["solo_feasibility"]
    figure_arrival(config, generator, output_dir / "arrival_rate.svg")
    figure_solo(feasibility, config["pilot"]["solo_feasible_fraction"], output_dir / "solo_feasibility.svg")
    for mode in MODES:
        figure_status(cells, mode, output_dir / f"status_{mode}.svg")
        figure_pressure(cells, mode, output_dir / f"pressure_{mode}.svg")
    (output_dir / "calibration_report.md").write_text(build_markdown(gates, feasibility, cells, config), encoding="utf-8")
    (output_dir / "calibration_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return gates


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()
    gates = generate(args.output_dir)
    print(json.dumps({k: (v["pass"] if isinstance(v, dict) and "pass" in v else v) for k, v in gates.items() if k != "diagnostics"}, indent=2))


if __name__ == "__main__":
    main()
