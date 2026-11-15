# =============================================================================
# OsdagBridge Report Generator — Programmatic Matplotlib Visualizations
# Generates charts for Section 5.5 (Utilization Ratios) and Chapter 7
# (Material Quantities) into a temporary directory during report compilation.
# =============================================================================

import os
import re
import logging
from typing import Dict, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .styles import STYLE

logger = logging.getLogger(__name__)


def _to_float(val, default=None) -> Optional[float]:
    if val is None or val == "":
        return default
    if isinstance(val, (int, float)):
        return float(val)
    match = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", str(val).replace(",", ""))
    if match:
        try:
            return float(match.group(0))
        except ValueError:
            return default
    return default


def _extract_utilization_ratios(bridge) -> Dict[str, float]:
    """
    Compute max Utilization Ratio (UR = Demand / Capacity) for:
      - Steel Plate Girders
      - Concrete Deck Slab
      - Cross Bracing
      - End Diaphragms
    """
    out = getattr(bridge, "output_dict", {}) or {}
    dr = out.get("design_results", {}) or {}
    per_girder = dr.get("per_girder", {}) or {}
    deck_rpt = out.get("deck_report_values", {}) or {}

    # 1. Steel Plate Girders
    girder_urs = []
    for g_key, g_val in per_girder.items():
        if str(g_key).startswith("EB") or not isinstance(g_val, dict):
            continue
        for chk in g_val.get("checks") or []:
            dcr = _to_float(chk.get("dcr"))
            if dcr is not None:
                girder_urs.append(dcr)
    if not girder_urs:
        for k in ("util_flexure", "util_shear", "util_interaction", "util_ltb"):
            pct = _to_float(out.get(k))
            if pct is not None:
                girder_urs.append(pct / 100.0 if pct > 5.0 else pct)
    girder_ur = max(girder_urs) if girder_urs else 0.0

    # 2. Concrete Deck Slab
    deck_urs = []
    pairs = [
        ("dd_m_uls_sag", "dd_mu_bot"),
        ("dd_m_uls_hog", "dd_mu_top"),
        ("dd_m_uls_oh", "dd_mu_oh"),
        ("dd_punch_ved", "dd_vrd_c_mpa"),
        ("dd_shear_ved", "dd_shear_vrdc"),
    ]
    for dem_k, cap_k in pairs:
        dem = _to_float(deck_rpt.get(dem_k))
        cap = _to_float(deck_rpt.get(cap_k))
        if dem is not None and cap is not None and cap > 0:
            deck_urs.append(dem / cap)
    wk = _to_float(deck_rpt.get("dd_wk_bot"))
    wk_lim = _to_float(deck_rpt.get("dd_wk_limit"))
    if wk is not None and wk_lim is not None and wk_lim > 0:
        deck_urs.append(wk / wk_lim)
    deck_ur = max(deck_urs) if deck_urs else 0.0

    # 3. Cross Bracing
    cb_urs = []
    for cb_pair in bridge.get_cb_pairs():
        for member in ("diagonal", "chord"):
            for ftype in ("compression", "tension"):
                eff = _to_float(bridge.get_cb_efficiency(cb_pair, member, ftype))
                if eff is not None:
                    cb_urs.append(eff)
            slnd = _to_float(bridge.get_cb_slenderness(cb_pair, member))
            if slnd is not None:
                lim = 400.0 if member == "chord" else 250.0
                cb_urs.append(slnd / lim)
    cb_ur = max(cb_urs) if cb_urs else 0.0

    # 4. End Diaphragms
    ed_ur = cb_ur if cb_urs else 0.0

    return {
        "Steel Plate Girders": round(girder_ur, 3),
        "Concrete Deck Slab": round(deck_ur, 3),
        "Cross Bracing": round(cb_ur, 3),
        "End Diaphragms": round(ed_ur, 3),
    }


def generate_ur_summary_chart(bridge, out_path: str) -> Optional[str]:
    """
    Generate bar chart of Utilization Ratio (UR = Demand / Capacity) for primary
    elements with a red dashed reference line at UR = 1.0.
    """
    try:
        ur_map = _extract_utilization_ratios(bridge)
        labels = list(ur_map.keys())
        values = list(ur_map.values())

        colors = [
            f"#{STYLE.fail_color}" if v > 1.0 else f"#{STYLE.accent_color_hex}"
            for v in values
        ]

        fig, ax = plt.subplots(figsize=(7.2, 3.8), dpi=220)
        bars = ax.bar(labels, values, width=0.5, color=colors, edgecolor="#222222", linewidth=0.7)

        ax.axhline(
            1.0,
            color="red",
            linestyle="--",
            linewidth=1.5,
            label="Limit Threshold (UR = 1.0)",
            zorder=4,
        )

        ymax = max([1.25] + [v * 1.18 for v in values])
        ax.set_ylim(0, ymax)
        ax.set_ylabel("Utilization Ratio (Demand / Capacity)", fontsize=10, fontweight="bold")
        ax.set_title("Overall Element Utilization Ratio Summary", fontsize=11, fontweight="bold", pad=10)
        ax.grid(axis="y", linestyle=":", alpha=0.6, zorder=0)
        ax.tick_params(axis="x", labelsize=9)
        ax.tick_params(axis="y", labelsize=9)

        for bar, val in zip(bars, values):
            status_txt = "FAIL" if val > 1.0 else "PASS"
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                val + ymax * 0.025,
                f"{val:.2f} ({status_txt})",
                ha="center",
                va="bottom",
                fontsize=8.5,
                fontweight="bold",
                color=f"#{STYLE.fail_color}" if val > 1.0 else "#111111",
            )

        ax.legend(loc="upper right", fontsize=8.5, frameon=True)
        fig.tight_layout()
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        fig.savefig(out_path, dpi=220)
        plt.close(fig)
        return out_path
    except Exception as exc:
        logger.warning("Failed to generate UR summary chart: %s", exc)
        return None


def generate_material_quantity_charts(inputs: dict, out_dir: str) -> Dict[str, str]:
    """
    Generate Chapter 7 material quantity charts:
      1) steel_tonnage_chart.png: Structural steel weight (MT) by component
         (Girders, Cross Bracing, End Diaphragms).
      2) concrete_vs_rebar_chart.png: Concrete volume (m^3) vs Reinforcement
         steel weight (MT).
    """
    generated = {}
    inp = inputs or {}

    # 1. Structural Steel Tonnage (MT)
    try:
        girders_wt = _to_float(inp.get("steel_girders_wt_total"), 0.0) or 0.0
        bracing_wt = (
            (_to_float(inp.get("bracing_top_wt_total"), 0.0) or 0.0)
            + (_to_float(inp.get("bracing_bot_wt_total"), 0.0) or 0.0)
            + (_to_float(inp.get("bracing_diag_wt_total"), 0.0) or 0.0)
        )
        # End diaphragm total weight if exposed, else 0.0
        diaphragm_wt = _to_float(inp.get("diaphragm_wt_total"), 0.0) or 0.0

        steel_labels = ["Girders", "Cross Bracing", "End Diaphragms"]
        steel_vals = [girders_wt, bracing_wt, diaphragm_wt]

        fig, ax = plt.subplots(figsize=(6.8, 3.5), dpi=220)
        bars = ax.bar(
            steel_labels,
            steel_vals,
            width=0.45,
            color=[f"#{STYLE.accent_color_hex}", f"#{STYLE.primary_color_hex}", "#6C757D"],
            edgecolor="#222222",
            linewidth=0.7,
        )
        ymax = max([1.0] + [v * 1.2 for v in steel_vals])
        ax.set_ylim(0, ymax)
        ax.set_ylabel("Weight (MT)", fontsize=10, fontweight="bold")
        ax.set_title("Structural Steel Quantity by Component (MT)", fontsize=11, fontweight="bold", pad=10)
        ax.grid(axis="y", linestyle=":", alpha=0.6, zorder=0)
        ax.tick_params(axis="both", labelsize=9)

        for bar, val in zip(bars, steel_vals):
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                val + ymax * 0.025,
                f"{val:.2f} MT",
                ha="center",
                va="bottom",
                fontsize=8.5,
                fontweight="bold",
            )

        fig.tight_layout()
        os.makedirs(out_dir, exist_ok=True)
        steel_path = os.path.join(out_dir, "steel_tonnage_chart.png")
        fig.savefig(steel_path, dpi=220)
        plt.close(fig)
        generated["steel_tonnage_chart"] = steel_path
    except Exception as exc:
        logger.warning("Failed to generate steel tonnage chart: %s", exc)

    # 2. Concrete Volume (m^3) vs Reinforcement Steel Weight (MT)
    try:
        conc_vol = _to_float(inp.get("concrete_deck_vol_total"), 0.0) or 0.0
        rebar_wt = _to_float(inp.get("rebar_deck_wt_total"), 0.0) or 0.0

        comp_labels = ["Concrete Volume (m³)", "Reinforcement Steel (MT)"]
        comp_vals = [conc_vol, rebar_wt]

        fig, ax = plt.subplots(figsize=(6.8, 3.5), dpi=220)
        bars = ax.bar(
            comp_labels,
            comp_vals,
            width=0.42,
            color=["#4A777A", f"#{STYLE.primary_color_hex}"],
            edgecolor="#222222",
            linewidth=0.7,
        )
        ymax = max([1.0] + [v * 1.2 for v in comp_vals])
        ax.set_ylim(0, ymax)
        ax.set_ylabel("Quantity (m³ / MT)", fontsize=10, fontweight="bold")
        ax.set_title("Concrete Volume (m³) vs. Reinforcement Steel Weight (MT)", fontsize=10.5, fontweight="bold", pad=10)
        ax.grid(axis="y", linestyle=":", alpha=0.6, zorder=0)
        ax.tick_params(axis="both", labelsize=9)

        units = ["m³", "MT"]
        for bar, val, unit in zip(bars, comp_vals, units):
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                val + ymax * 0.025,
                f"{val:.2f} {unit}",
                ha="center",
                va="bottom",
                fontsize=8.5,
                fontweight="bold",
            )

        fig.tight_layout()
        os.makedirs(out_dir, exist_ok=True)
        conc_path = os.path.join(out_dir, "concrete_vs_rebar_chart.png")
        fig.savefig(conc_path, dpi=220)
        plt.close(fig)
        generated["concrete_vs_rebar_chart"] = conc_path
    except Exception as exc:
        logger.warning("Failed to generate concrete vs rebar chart: %s", exc)

    return generated