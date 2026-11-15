# =============================================================================
# Chapter 3: Loads and Load Combinations
# Refactored for separated Vehicle Live Loads & Footpath Live Loads tables,
# dynamic UI vehicle selection, and centralized style/longtable helpers.
# =============================================================================

from osdagbridge.core.utils.common import (
    KEY_CB_LOAD,
    KEY_LL_CUSTOM_VEHICLES,
    KEY_LL_FOOTPATH_PRESSURE_MODE,
    KEY_LL_FOOTPATH_PRESSURE_VALUE,
    KEY_LL_IRC_70R_BOGIE,
    KEY_LL_IRC_70R_TRACKED,
    KEY_LL_IRC_70R_WHEELED,
    KEY_LL_IRC_AA_TRACKED,
    KEY_LL_IRC_AA_WHEELED,
    KEY_LL_IRC_CLASS_A,
    KEY_LL_IRC_CLASS_FATIGUE,
    KEY_LL_IRC_CLASS_SV,
    KEY_MATERIAL_DECK_DENSITY,
    KEY_MATERIAL_GIRDER_DENSITY,
    KEY_PL_SELF_WEIGHT_FACTOR,
    KEY_RL_LOAD_VALUE,
    KEY_SL_DAMPING,
    KEY_SL_DEAD_LOAD_MODE,
    KEY_SL_DEAD_LOAD_VALUE,
    KEY_SL_HORIZONTAL_COEFF,
    KEY_SL_IMPORTANCE_FACTOR,
    KEY_SL_LIVE_LOAD_MODE,
    KEY_SL_LIVE_LOAD_VALUE,
    KEY_SL_SEISMIC_ZONE,
    KEY_SL_SOIL_TYPE,
    KEY_SL_SPECTRAL_COEFF,
    KEY_SL_TIME_PERIOD,
    KEY_SL_VERTICAL_COEFF,
    KEY_SL_ZONE_FACTOR,
    KEY_SPAN,
    KEY_TL_BRIDGE_TEMP_MAX,
    KEY_TL_BRIDGE_TEMP_MIN,
    KEY_TL_HIGHEST_MAX_TEMP,
    KEY_TL_LOWEST_MIN_TEMP,
    KEY_TL_TEMP_FALL,
    KEY_TL_TEMP_RISE,
    KEY_WC_LD_LANE_TABLE_COUNT,
    KEY_WC_MATERIAL,
    KEY_WC_THICKNESS,
    KEY_WL_AVG_EXPOSED_HEIGHT,
    KEY_WL_BASIC_WIND_SPEED,
    KEY_WL_HOURLY_MEAN_WIND,
    KEY_WL_HOURLY_WIND_PRESSURE,
    KEY_WL_LONGITUDINAL_WIND_FORCE,
    KEY_WL_TERRAIN_TYPE,
    KEY_WL_TRANSVERSE_WIND_FORCE,
    KEY_WL_VERTICAL_WIND_FORCE
)

from osdagbridge.core.reports.report_utils import _tex, _render_value
from .styles import STYLE, longtable_headers


def _get_selected_vehicles(input_dict):
    """Return list of vehicle display names selected in the Loading tab."""
    vehicle_keys = [
        (KEY_LL_IRC_CLASS_A, "Class A"),
        (KEY_LL_IRC_70R_WHEELED, "Class 70R (Wheeled)"),
        (KEY_LL_IRC_70R_TRACKED, "Class 70R (Tracked)"),
        (KEY_LL_IRC_AA_WHEELED, "Class AA (Wheeled)"),
        (KEY_LL_IRC_AA_TRACKED, "Class AA (Tracked)"),
        (KEY_LL_IRC_CLASS_SV, "Class SV"),
        (KEY_LL_IRC_70R_BOGIE, "Class 70R (Bogie)"),
        (KEY_LL_IRC_CLASS_FATIGUE, "Class Fatigue"),
    ]
    selected = [label for key, label in vehicle_keys if input_dict.get(key)]

    custom = input_dict.get(KEY_LL_CUSTOM_VEHICLES)
    if custom and isinstance(custom, list):
        for item in custom:
            if isinstance(item, dict) and item.get("name"):
                selected.append(str(item["name"]))
            elif isinstance(item, str) and item.strip():
                selected.append(item.strip())

    return selected


def ch3_loads(input_dict):
    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

    selected_vehicles = _get_selected_vehicles(input_dict)

    span = input_dict.get(KEY_SPAN)
    span_m = None
    im_class_a_str = "---"
    im_heavy_str = "---"
    if span not in (None, ""):
        try:
            span_m = float(span)
            im_a = IRC6_2017.cl_208_2_impact_factor(span_m)
            im_class_a_str = f"{1.0 + im_a:.3f}"
            im_aa = IRC6_2017.cl_208_3_impact_factor(span_m)
            im_heavy_str = f"{1.0 + im_aa:.3f}"
        except Exception:
            span_m = None

    lanes = input_dict.get(KEY_WC_LD_LANE_TABLE_COUNT)
    braking_considered = "No"
    braking_value_str = "---"
    if lanes not in (None, ""):
        try:
            lanes_int = int(lanes)
            if lanes_int > 0:
                braking_force_t = IRC6_2017.cl_211_2_braking_force(lanes_int)
                braking_force_kN = braking_force_t * 9.81
                braking_considered = "Yes"
                braking_value_str = f"{braking_force_kN:.2f}"
        except Exception:
            braking_considered = "No"
            braking_value_str = "---"

    vehicle_rows = []
    if selected_vehicles:
        for veh in selected_vehicles:
            lower_veh = veh.lower()
            if "class a" in lower_veh:
                if_val = im_class_a_str
            elif any(tok in lower_veh for tok in ("70r", "aa", "bogie")):
                if_val = im_heavy_str
            else:
                if_val = "---"

            row_tex = (
                _tex(veh)
                + r" & ---"
                + r" & " + _tex(if_val)
                + r" & " + _tex(braking_considered)
                + r" & " + _tex(braking_value_str)
                + r" & ---"
                + r" & ---"
                + r" \\[" + STYLE.row_pad + r"]"
                + "\n\\hline"
            )
            vehicle_rows.append(row_tex)
    else:
        vehicle_rows.append(
            r"None & --- & --- & No & --- & --- & --- \\[" + STYLE.row_pad + r"]\n\hline"
        )

    vehicle_rows_str = "\n".join(vehicle_rows)

    fp_mode = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE, "")
    fp_value = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE, "")
    fp_intensity_str = "---"
    fp_ref_str = _tex(fp_mode) if fp_mode not in (None, "") else "---"

    if str(fp_mode).strip().lower() in ("as per irc 6", "as per irc6", "automatic"):
        try:
            fp_intensity_str = f"{IRC6_2017.cl_206_1_footway_load():.3f}"
            fp_ref_str = "IRC 6 Cl. 206.1"
        except Exception:
            fp_intensity_str = "---"
    elif fp_value not in (None, ""):
        try:
            fp_intensity_str = f"{float(fp_value):.3f}"
        except Exception:
            fp_intensity_str = _tex(fp_value)

    # Vz / Pz — prefer stored computed values; fall back to IRC6 Table 12
    vz_val = input_dict.get(KEY_WL_HOURLY_MEAN_WIND)
    pz_val = input_dict.get(KEY_WL_HOURLY_WIND_PRESSURE)
    if not vz_val or not pz_val:
        try:
            _vb = input_dict.get(KEY_WL_BASIC_WIND_SPEED) or input_dict.get("wind_speed")
            _h = input_dict.get(KEY_WL_AVG_EXPOSED_HEIGHT)
            _ter = {
                "Plain Terrain": "plain",
                "Terrain with Obstructions": "obstructed",
            }.get(str(input_dict.get(KEY_WL_TERRAIN_TYPE, "")).strip(), "plain")
            _res = IRC6_2017.table_12(float(_h), _ter, float(_vb))
            if not vz_val:
                vz_val = _res.get("Vz")
            if not pz_val:
                pz_val = _res.get("Pz")
        except Exception:
            pass

    # Table 3.5 — Seismic: prefer stored computed values; fall back to IRC6 cl_218_5_1
    sl_zone_factor = input_dict.get(KEY_SL_ZONE_FACTOR)
    sl_spectral = input_dict.get(KEY_SL_SPECTRAL_COEFF)
    sl_ah = input_dict.get(KEY_SL_HORIZONTAL_COEFF)
    sl_av = input_dict.get(KEY_SL_VERTICAL_COEFF)
    if not sl_ah or not sl_zone_factor:
        try:
            _zone = input_dict.get(KEY_SL_SEISMIC_ZONE) or input_dict.get("seismic_zone")
            _zmap = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V"}
            _z = str(_zone).strip().upper()
            if _z.isdigit():
                _z = _zmap.get(_z)
            _smap = {"Type I – Rocky or Hard": 1, "Type II – Medium Soil": 2, "Type III – Soft Soil": 3}
            _st = _smap.get(str(input_dict.get(KEY_SL_SOIL_TYPE, "")), 1)
            _tp = input_dict.get(KEY_SL_TIME_PERIOD)
            _damp = input_dict.get(KEY_SL_DAMPING) or "5"
            _dl_v = input_dict.get(KEY_SL_DEAD_LOAD_VALUE)
            _ll_v = input_dict.get(KEY_SL_LIVE_LOAD_VALUE)
            _dead = float(_dl_v) if str(input_dict.get(KEY_SL_DEAD_LOAD_MODE, "")) == "Custom" and _dl_v else 0.0
            _live = float(_ll_v) if str(input_dict.get(KEY_SL_LIVE_LOAD_MODE, "")) == "Custom" and _ll_v else 0.0
            _res = IRC6_2017.cl_218_5_1(
                zone=f"Zone {_z}",
                soil_type=_st,
                dead_load_kN=_dead,
                live_load_kN=_live,
                period_T=float(_tp) if _tp else None,
                damping_percent=float(_damp),
            )
            if not sl_zone_factor:
                sl_zone_factor = _res.get("Z")
            if not sl_spectral:
                sl_spectral = _res.get("Sa_g_adjusted")
            if not sl_ah:
                sl_ah = _res.get("Ah")
            if not sl_av:
                sl_av = round(_res.get("Ah", 0) * 2 / 3, 4)
        except Exception:
            pass

    # Table 3.6 — Temperature: compute effective bridge temp range from shade temps
    try:
        _tmax = input_dict.get(KEY_TL_HIGHEST_MAX_TEMP) or input_dict.get("shade_temp_max")
        _tmin = input_dict.get(KEY_TL_LOWEST_MIN_TEMP) or input_dict.get("shade_temp_min")
        if _tmax and _tmin:
            _res = IRC6_2017.cl_215_2_effective_bridge_temperature(
                float(_tmax), float(_tmin), "metallic", False
            )
            _bt_min = _res.get("T_min", 0)
            _bt_max = _res.get("T_max", 0)
            _mean = (_bt_max + _bt_min) / 2.0
            if not input_dict.get(KEY_TL_BRIDGE_TEMP_MIN):
                input_dict[KEY_TL_BRIDGE_TEMP_MIN] = f"{_bt_min:.2f}"
            if not input_dict.get(KEY_TL_BRIDGE_TEMP_MAX):
                input_dict[KEY_TL_BRIDGE_TEMP_MAX] = f"{_bt_max:.2f}"
            if not input_dict.get(KEY_TL_TEMP_RISE):
                input_dict[KEY_TL_TEMP_RISE] = f"{_bt_max - _mean:.2f}"
            if not input_dict.get(KEY_TL_TEMP_FALL):
                input_dict[KEY_TL_TEMP_FALL] = f"{_mean - _bt_min:.2f}"
    except Exception:
        pass

    # --- Load Combinations (dynamically generated from IRC 6) ---
    _LOAD_LABEL_MAP = {
        "dead_load": "DL",
        "surfacing": "SIDL",
        "live_load": "LL",
        "wind_load": "WL",
        "thermal_load": "TL",
        "vehicle_collision": "VC",
        "barge_impact": "BI",
        "floating_bodies": "FB",
        "seismic": "EQ",
    }

    def _fmt_factors(factors):
        parts = []
        for load, val in factors.items():
            label = _LOAD_LABEL_MAP.get(load, load.upper())
            if isinstance(val, dict):
                add = val.get("adding")
                rel = val.get("relieving")
                add_s = f"{add:.2f}" if add is not None else "--"
                rel_s = f"{rel:.2f}" if rel is not None else "--"
                parts.append(f"{label}({add_s}/{rel_s})")
            else:
                if val is None:
                    continue
                parts.append(f"{label}({val:.2f})")
        return " + ".join(parts)

    uls_combos = IRC6_2017.uls_load_combinations()
    sls_combos = IRC6_2017.sls_load_combinations()
    lc_rows = []
    for i, combo in enumerate(uls_combos, start=1):
        cases = _fmt_factors(combo["factors"])
        lc_rows.append(
            f"ULS-{i:02d}" + r" & " + cases + r" \\[" + STYLE.row_pad + r"]" + "\n"
            + r"\hline"
        )
    for i, combo in enumerate(sls_combos, start=1):
        cases = _fmt_factors(combo["factors"])
        lc_rows.append(
            f"SLS-{i:02d}" + r" & " + cases + r" \\[" + STYLE.row_pad + r"]" + "\n"
            + r"\hline"
        )
    lc_rows_str = "\n".join(lc_rows)

    kv_header = longtable_headers(r"\textbf{Parameter} & \textbf{Value}")
    lc_header = longtable_headers(r"\textbf{Combination ID} & \textbf{Load Cases}")

    veh_header_tex = (
        r"\multirow{2}{*}{\textbf{Vehicle}} & "
        r"\multirow{2}{*}{\makecell{\textbf{Total Load}\\\textbf{(kN)}}} & "
        r"\multirow{2}{*}{\makecell{\textbf{Impact}\\\textbf{Factor}}} & "
        r"\multicolumn{3}{c|}{\textbf{Braking Load}} & "
        r"\multirow{2}{*}{\makecell{\textbf{Centrifugal}\\\textbf{Forces}}} \\" + "\n"
        r"\cline{4-6}" + "\n"
        r"& & & \textbf{Considered?} & \textbf{Value (kN)} & \textbf{Eccentricity} \\"
    )

    veh_endhead_tex = (
        r"\multicolumn{7}{l}{\textit{\footnotesize (Continued)}} \\" + "\n"
        + r"\hline" + "\n"
        + r"\textbf{Vehicle} & \textbf{Total Load (kN)} & \textbf{Impact Factor} & "
        r"\textbf{Considered?} & \textbf{Value (kN)} & \textbf{Eccentricity} & \textbf{Centrifugal Forces} \\"
    )

    fp_header = longtable_headers(
        r"\textbf{Parameter} & \textbf{Value} & \textbf{Unit} & \textbf{Basis / Reference}"
    )

    return r"""
\chapter{Loads and Load Combinations}

This section summarizes all loads applied to the bridge and the load combinations considered for analysis and design.

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Dead Load -- Self Weight}}
""" + kv_header + r"""
\textnormal{Steel Self-Weight Applied} & """ + (_render_value(input_dict, KEY_MATERIAL_GIRDER_DENSITY, r' kN/m\textsuperscript{3}')) + r""" \\""" + STYLE.row_pad + r"""
\hline
\textnormal{Concrete Deck Weight} & """ + (_render_value(input_dict, KEY_MATERIAL_DECK_DENSITY, r' kN/m\textsuperscript{3}')) + r""" \\""" + STYLE.row_pad + r"""
\hline
\textnormal{Self-Weight Factor} & """ + (_render_value(input_dict, KEY_PL_SELF_WEIGHT_FACTOR)) + r""" \\""" + STYLE.row_pad + r"""
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Dead Load for Surfacing (DW)}}
""" + kv_header + r"""
\textnormal{Wearing Course Load} & """ + (_render_value(input_dict, KEY_WC_MATERIAL)) + r""" x """ + (_render_value(input_dict, KEY_WC_THICKNESS)) + r""" \\""" + STYLE.row_pad + r"""
\hline
\textnormal{Additional SIDL (Crash Barrier)} & """ + (_render_value(input_dict, KEY_CB_LOAD)) + r""" kN/m per barrier \\""" + STYLE.row_pad + r"""
\hline
\textnormal{Railing Load} & """ + (_render_value(input_dict, KEY_RL_LOAD_VALUE)) + r""" kN/m\sdstar{} \\""" + STYLE.row_pad + r"""
\hline
\end{longtable}

\vspace{1em}
\begingroup
\footnotesize
\setlength{\tabcolsep}{""" + STYLE.compact_tabcolsep + r"""}
\begin{longtable}{|L{2.8cm}|C{1.9cm}|C{1.7cm}|C{2.1cm}|C{1.9cm}|C{2.1cm}|C{2.2cm}|}
\caption{\textbf{Vehicle Live Loads (LL)}}
\hline
""" + veh_header_tex + r"""
\hline
\endfirsthead
\hline
""" + veh_endhead_tex + r"""
\hline
\endhead
""" + vehicle_rows_str + r"""
\end{longtable}
\endgroup

\vspace{1em}
\begin{longtable}{|L{5.2cm}|C{3.2cm}|C{2.6cm}|L{4.5cm}|}
\caption{\textbf{Footpath Live Loads}}
""" + fp_header + r"""
\textnormal{Footpath Live Load Intensity} & """ + _tex(fp_intensity_str) + r""" & kN/m\textsuperscript{2} & """ + _tex(fp_ref_str) + r""" \\""" + STYLE.row_pad + r"""
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Wind Load (WL) --- per IRC 6}}
""" + kv_header + r"""
\textnormal{Basic Wind Speed, Vb} & """ + (_render_value(input_dict, "wind_speed", " m/s")) + r""" [from Project Location] \\""" + STYLE.row_pad + r"""
\hline
\textnormal{Terrain Type} & """ + (_render_value(input_dict, KEY_WL_TERRAIN_TYPE)) + r""" \\""" + STYLE.row_pad + r"""
\hline
\textnormal{Average Exposed Height, H (m)} & """ + (_render_value(input_dict, KEY_WL_AVG_EXPOSED_HEIGHT, " m")) + r""" \\""" + STYLE.row_pad + r"""
\hline
\textnormal{Hourly Mean Wind Speed, Vz} & """ + (_render_value(input_dict, KEY_WL_HOURLY_MEAN_WIND, " m/s")) + r""" \\""" + STYLE.row_pad + r"""
\hline
\textnormal{Hourly Wind Pressure, Pz} & """ + (_render_value(input_dict, KEY_WL_HOURLY_WIND_PRESSURE, r" N/m\textsuperscript{2}")) + r""" \\""" + STYLE.row_pad + r"""
\hline
\textnormal{Transverse Wind Force} & """ + (_render_value(input_dict, KEY_WL_TRANSVERSE_WIND_FORCE, " kN")) + r""" \\""" + STYLE.row_pad + r"""
\hline
\textnormal{Longitudinal Wind Force} & """ + (_render_value(input_dict, KEY_WL_LONGITUDINAL_WIND_FORCE, " kN")) + r""" \\""" + STYLE.row_pad + r"""
\hline
\textnormal{Vertical Wind Force} & """ + (_render_value(input_dict, KEY_WL_VERTICAL_WIND_FORCE, " kN")) + r""" \\""" + STYLE.row_pad + r"""
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Earthquake Load (EL) --- per IRC 6}}
""" + kv_header + r"""
\textnormal{Seismic Zone} & """ + (_render_value(input_dict, "seismic_zone")) + r""" [from Project Location] \\""" + STYLE.row_pad + r"""
\hline
\textnormal{Zone Factor, Z} & """ + (_render_value(input_dict, KEY_SL_ZONE_FACTOR)) + r""" \\""" + STYLE.row_pad + r"""
\hline
\textnormal{Importance Factor, I} & """ + (_render_value(input_dict, KEY_SL_IMPORTANCE_FACTOR)) + r""" \\""" + STYLE.row_pad + r"""
\hline
\textnormal{Type of Soil} & """ + (_render_value(input_dict, KEY_SL_SOIL_TYPE)) + r""" \\""" + STYLE.row_pad + r"""
\hline
\textnormal{Sa/g} & """ + (_render_value(input_dict, KEY_SL_SPECTRAL_COEFF)) + r""" \\""" + STYLE.row_pad + r"""
\hline
\textnormal{Horizontal Seismic Coefficient, Ah} & """ + (_render_value(input_dict, KEY_SL_HORIZONTAL_COEFF)) + r""" \\""" + STYLE.row_pad + r"""
\hline
\textnormal{Vertical Seismic Coefficient, Av} & """ + (_render_value(input_dict, KEY_SL_VERTICAL_COEFF)) + r""" \\""" + STYLE.row_pad + r"""
\hline
\textnormal{Horizontal Seismic Force (longitudinal)} & --- kN \\""" + STYLE.row_pad + r"""
\hline
\textnormal{Horizontal Seismic Force (transverse)} & --- kN \\""" + STYLE.row_pad + r"""
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Temperature Load (TL) --- per IRC 6}}
""" + kv_header + r"""
\textnormal{Maximum Shade Temperature} & """ + (_render_value(input_dict, "shade_temp_max")) + r""" $^\circ$C \\""" + STYLE.row_pad + r"""
\hline
\textnormal{Minimum Shade Temperature} & """ + (_render_value(input_dict, "shade_temp_min")) + r""" $^\circ$C \\""" + STYLE.row_pad + r"""
\hline
\textnormal{Effective Bridge Temp. Range} & """ + (_render_value(input_dict, KEY_TL_BRIDGE_TEMP_MIN)) + r""" to """ + (_render_value(input_dict, KEY_TL_BRIDGE_TEMP_MAX)) + r""" $^\circ$C \\""" + STYLE.row_pad + r"""
\hline
\textnormal{Temperature Rise / Fall for Design} & +""" + (_render_value(input_dict, KEY_TL_TEMP_RISE)) + r""" $^\circ$C / \textminus{}""" + (_render_value(input_dict, KEY_TL_TEMP_FALL)) + r""" $^\circ$C \\""" + STYLE.row_pad + r"""
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|C{4.0cm}|p{11.5cm}|}
\caption{\textbf{Load Combinations}}
""" + lc_header + r"""
""" + lc_rows_str + r"""
\end{longtable}

\noindent\textit{Note: All IRC 6 load combinations are auto-generated by OsdagBridge. User-defined custom combinations, if any, are appended.}
"""