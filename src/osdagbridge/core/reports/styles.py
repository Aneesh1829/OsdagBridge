# =============================================================================
# OsdagBridge Report Generator — Centralized Style & Layout Configuration
# Single source of truth for page geometry, margins, colors, table spacing,
# and multi-page LongTable header helpers.
# =============================================================================

from dataclasses import dataclass


@dataclass(frozen=True)
class ReportStyleConfig:
    # Page geometry & margins (prevents footer/row bleed such as page 30)
    paper_size: str = "a4paper"
    margin_top: str = "0.95in"
    margin_bottom: str = "1.05in"
    margin_left: str = "0.85in"
    margin_right: str = "0.85in"
    headheight: str = "16pt"
    footskip: str = "28pt"

    # Brand & status colors
    primary_color_hex: str = "91B014"   # osdagGreen
    accent_color_hex: str = "1F4E78"    # subtle structural navy for headers/accents
    header_bg_hex: str = "F2F6E4"       # soft tint for table headers
    stripe_bg_hex: str = "FAFBF7"       # subtle alternating row tint
    pass_color: str = "1E7E34"
    fail_color: str = "C00000"
    warn_color: str = "B45309"

    # Typography & line spacing
    base_font_size: str = "11pt"
    line_spread: float = 1.15
    table_font_cmd: str = r"\small"
    compact_table_font_cmd: str = r"\footnotesize"

    # Table & longtable spacing rules
    tabcolsep: str = "5pt"
    compact_tabcolsep: str = "3.5pt"
    arraystretch: float = 1.18
    row_pad: str = "6pt"
    lt_pre: str = "6pt"
    lt_post: str = "8pt"
    array_rule_width: str = "0.5pt"
    extra_row_height: str = "1.0pt"
    needspace_lines: str = "6"
    header_repeat_threshold: str = "10\\baselineskip"


STYLE = ReportStyleConfig()


def build_geometry_preamble(cfg: ReportStyleConfig = STYLE) -> str:
    """Return geometry, color, and table-spacing LaTeX definitions."""
    return rf"""
\usepackage[{cfg.paper_size}, top={cfg.margin_top}, bottom={cfg.margin_bottom}, left={cfg.margin_left}, right={cfg.margin_right}, headheight={cfg.headheight}, footskip={cfg.footskip}]{{geometry}}
\definecolor{{osdagGreen}}{{HTML}}{{{cfg.primary_color_hex}}}
\definecolor{{osdagNavy}}{{HTML}}{{{cfg.accent_color_hex}}}
\definecolor{{osdagHeaderBg}}{{HTML}}{{{cfg.header_bg_hex}}}
\definecolor{{osdagStripeBg}}{{HTML}}{{{cfg.stripe_bg_hex}}}
\definecolor{{statusPass}}{{HTML}}{{{cfg.pass_color}}}
\definecolor{{statusFail}}{{HTML}}{{{cfg.fail_color}}}
\definecolor{{statusWarn}}{{HTML}}{{{cfg.warn_color}}}

\setlength{{\LTleft}}{{\fill}}
\setlength{{\LTright}}{{\fill}}
\setlength{{\tabcolsep}}{{{cfg.tabcolsep}}}
\renewcommand{{\arraystretch}}{{{cfg.arraystretch}}}
\setlength{{\LTpre}}{{{cfg.lt_pre}}}
\setlength{{\LTpost}}{{{cfg.lt_post}}}
\setlength{{\arrayrulewidth}}{{{cfg.array_rule_width}}}
\setlength{{\extrarowheight}}{{{cfg.extra_row_height}}}
\setstretch{{{cfg.line_spread}}}

\BeforeBeginEnvironment{{table}}{{\needspace{{{cfg.needspace_lines}\baselineskip}}}}
\BeforeBeginEnvironment{{longtable}}{{\needspace{{{cfg.needspace_lines}\baselineskip}}}}
"""


def longtable_headers(header_row_tex: str, continued_label: str = "(Continued)") -> str:
    """
    Generate LaTeX \\endfirsthead and \\endhead blocks so multi-page
    longtables repeat their column headers cleanly across page breaks.
    """
    num_cols = header_row_tex.count("&") + 1
    return (
        r"\\" + "\n"
        + r"\nopagebreak" + "\n"
        + r"\hline" + "\n"
        + header_row_tex + "\n"
        + r"\hline" + "\n"
        + r"\endfirsthead" + "\n"
        + r"\hline" + "\n"
        + rf"\multicolumn{{{num_cols}}}{{l}}{{\textit{{\footnotesize {continued_label}}}}} \\" + "\n"
        + r"\hline" + "\n"
        + header_row_tex + "\n"
        + r"\hline" + "\n"
        + r"\endhead" + "\n"
    )