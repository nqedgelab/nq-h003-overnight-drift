"""H-003: overnight drift, buy the close and sell the open. Rules are in
hypothesis.md and must not change here.

Usage: python backtest/h003.py in_sample
"""

import sys
from datetime import time
from pathlib import Path

import numpy as np
import pandas as pd

from nqlab import data

OPEN_BAR = time(9, 30)       # exit at its open
CLOSE_BAR = time(15, 59)     # entry at its close
MAX_GAP_DAYS = 4             # next session at most this many calendar days later

TICK = 0.25
COMMISSION = 0.25       # points per round trip ($2.50 per side at $20/point)
SLIP_ENTRY = 1 * TICK
SLIP_EXIT = 1 * TICK
COST = COMMISSION + SLIP_ENTRY + SLIP_EXIT

# Only the split's own years are loaded, so the last night of a split, whose
# exit would fall in the next split, has no next session and is skipped.
SPLIT_YEARS = {
    "in_sample": range(2015, 2022),
    "validation": range(2022, 2024),
    "holdout": range(2024, 2026),
}


def bar_value(day: pd.DataFrame, at: time, column: str):
    hit = day[day.index.time == at]
    return hit[column].iloc[0] if len(hit) else np.nan


def summarize_session(day: pd.DataFrame, suspect: bool = False) -> dict:
    """The prices one regular-hours session contributes."""
    return {
        "session": day["session"].iloc[0],
        "open": bar_value(day, OPEN_BAR, "open"),
        "close": bar_value(day, CLOSE_BAR, "close"),
        "range_pct": (day["high"].max() - day["low"].min()) / day["close"].iloc[-1],
        "roll_window": bool(day["roll_window"].iloc[0]),
        "suspect": bool(suspect),
    }


def make_trades(sessions: pd.DataFrame) -> pd.DataFrame:
    """Pair each session with the next one, in date order, and apply the rules."""
    s = sessions.sort_values("session").reset_index(drop=True)
    nxt = s.shift(-1)
    t = pd.DataFrame({
        "session": s["session"],
        "exit_session": nxt["session"],
        "entry": s["close"],
        "exit": nxt["open"],
        "bench_exit": nxt["close"],           # regular-hours leg of the exit session
        "entry_day_up": s["close"] > s["open"],
        "vol_prior": s["range_pct"].rolling(20, min_periods=20).mean().shift(1),
    })
    gap = (pd.to_datetime(t["exit_session"]) - pd.to_datetime(t["session"])).dt.days
    ok = (
        t["exit_session"].notna() & (gap <= MAX_GAP_DAYS)
        & t["entry"].notna() & t["exit"].notna()
        & ~s["suspect"] & ~s["suspect"].shift(-1, fill_value=True)
        & ~s["roll_window"] & ~s["roll_window"].shift(-1, fill_value=True)
    )
    t = t[ok].copy()
    t["weekend"] = pd.to_datetime(t["session"]).dt.dayofweek == 4
    t["gross_points"] = t["exit"] - t["entry"]
    t["cost_points"] = COST
    t["bp"] = (t["gross_points"] - COST) / t["entry"] * 1e4
    t["gross_bp"] = t["gross_points"] / t["entry"] * 1e4
    t["bench_bp"] = (t["bench_exit"] - t["exit"] - COST) / t["exit"] * 1e4
    return t.reset_index(drop=True)


def run(bars: pd.DataFrame) -> pd.DataFrame:
    suspect = data.session_report(bars)["suspect"]
    rth = bars[bars["rth"]]
    sessions = pd.DataFrame([summarize_session(day, suspect.get(session, False))
                             for session, day in rth.groupby("session", sort=True)])
    return make_trades(sessions)


def summarize(x: np.ndarray, seed: int = 1) -> dict:
    rng = np.random.default_rng(seed)
    boots = rng.choice(x, size=(10_000, len(x)), replace=True).mean(axis=1)
    equity = np.cumsum(x)
    drawdown = np.max(np.maximum.accumulate(np.concatenate([[0], equity]))[1:] - equity)
    wins, losses = x[x > 0], x[x <= 0]
    ordered = np.sort(x)
    return {
        "trades": len(x),
        "win_rate": len(wins) / len(x),
        "avg_win_bp": wins.mean() if len(wins) else 0.0,
        "avg_loss_bp": -losses.mean() if len(losses) else 0.0,
        "expectancy_bp": x.mean(),
        "ci_low": np.percentile(boots, 2.5),
        "ci_high": np.percentile(boots, 97.5),
        "max_drawdown_bp": drawdown,
        "expectancy_without_top10": ordered[:-10].mean() if len(x) > 10 else np.nan,
        "expectancy_without_worst10": ordered[10:].mean() if len(x) > 10 else np.nan,
        "total_bp": x.sum(),
    }


def report(trades: pd.DataFrame) -> str:
    def row(name, sub):
        s = summarize(sub["bp"].to_numpy())
        return (f"| {name} | {s['trades']} | {s['win_rate']:.1%} | {s['avg_win_bp']:.1f} | "
                f"{s['avg_loss_bp']:.1f} | {s['expectancy_bp']:+.2f} | "
                f"[{s['ci_low']:+.2f}, {s['ci_high']:+.2f}] | {sub['bench_bp'].mean():+.2f} |")

    lines = ["| Group | Trades | Win rate | Avg win bp | Avg loss bp | Expectancy bp | 95% CI | Regular hours bp |",
             "|:---|---:|---:|---:|---:|---:|:---:|---:|", row("All", trades),
             row("Weekend holds", trades[trades.weekend]), row("Weeknights", trades[~trades.weekend])]
    years = pd.to_datetime(trades["session"]).dt.year
    for y in sorted(years.unique()):
        lines.append(row(str(y), trades[years == y]))
    lines.append(row("Before 2020", trades[years < 2020]))
    lines.append(row("2020 on", trades[years >= 2020]))
    w = trades.dropna(subset=["vol_prior"])
    cuts = w["vol_prior"].quantile([1 / 3, 2 / 3]).to_numpy()
    lines.append(row("Low volatility", w[w.vol_prior <= cuts[0]]))
    lines.append(row("Middle volatility", w[(w.vol_prior > cuts[0]) & (w.vol_prior <= cuts[1])]))
    lines.append(row("High volatility", w[w.vol_prior > cuts[1]]))
    lines.append(row("Entry day up", trades[trades.entry_day_up]))
    lines.append(row("Entry day down", trades[~trades.entry_day_up]))
    return "\n".join(lines)


def main(split_name: str) -> None:
    bars = data.split(data.load(years=SPLIT_YEARS[split_name], drop_suspect=False), split_name)
    trades = run(bars)
    out = Path(__file__).resolve().parent / f"trades_{split_name}.csv"
    trades.to_csv(out, index=False)

    s = summarize(trades["bp"].to_numpy())
    bench = trades["bench_bp"].dropna()
    print(f"split: {split_name}  sessions: {bars['session'].nunique()}")
    for k, v in s.items():
        print(f"{k:>28}: {v:.4f}" if isinstance(v, float) else f"{k:>28}: {v}")
    print(f"{'expectancy_before_costs':>28}: {trades['gross_bp'].mean():.4f}")
    print(f"{'regular_hours_bp':>28}: {bench.mean():.4f}  (n={len(bench)})")
    print(f"{'beats_regular_hours':>28}: {trades['bp'].mean() > bench.mean()}")
    print(f"{'expectancy_points':>28}: {(trades['gross_points'] - COST).mean():.4f}")
    print(f"{'median_cost_bp':>28}: {(COST / trades['entry'] * 1e4).median():.4f}")
    print()
    print(report(trades))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "in_sample")
