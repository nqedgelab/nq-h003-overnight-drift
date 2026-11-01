"""Draw this repo's README artwork. Run from the repo root after both backtests:
python assets/make_assets.py
"""

import csv
import re
from pathlib import Path

from nqlab import art

OUT = Path(__file__).resolve().parent
RUNS = [OUT.parent / "backtest" / f"trades_{name}.csv" for name in ("in_sample", "validation")]
SCALE = 100   # art.equity draws in R with a tick every 20; plot hundreds of bp, relabel as bp

SECTIONS = [
    ("claim", "The idea", "What was claimed, and the exact rules"),
    ("result", "The result", "Passed in sample, failed in validation"),
    ("lessons", "What it taught", "Why a rejection is still useful"),
    ("data", "Reproduce it", "Same data, same code, same answer"),
]


def in_bp(svg: str) -> str:
    """Turn the chart's R labels back into basis points."""
    def relabel(m):
        value = float(m.group(1)) * SCALE
        return f">{value:+,.0f} bp<"
    return re.sub(r">([+-]?\d+(?:\.\d+)?)R<", relabel, svg)


def main():
    rows = []
    for path in RUNS:
        with path.open(newline="") as f:
            rows += [(r["session"], float(r["bp"]) / SCALE) for r in csv.DictReader(f)]
    for name, t in art.THEMES.items():
        status = (f'Verdict: <tspan fill="{t["bad"]}" font-weight="700">rejected</tspan>'
                  f'<tspan dx="14" fill="{t["sub"]}">·</tspan><tspan dx="14">−2.14 bp per night in validation</tspan>')
        art.write(OUT, "banner", name, art.banner(
            t, "H-003", "Overnight drift: buy the close, sell the open", status,
            "nq-h003-overnight-drift"))
        for num, (slug, title, sub) in enumerate(SECTIONS, 1):
            art.write(OUT, f"section-{slug}", name, art.section(t, num, slug, title, sub))
        art.write(OUT, "equity", name, in_bp(art.equity(
            t, rows, "Cumulative result, in sample then validation",
            f"{len(rows):,} nights, 2015–2023, after costs, measured in basis points of entry price",
            "rejected in validation")))
    print("ok")


if __name__ == "__main__":
    main()
