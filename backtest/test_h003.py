import pandas as pd
import pytest

import h003


def day(session, open_=100.0, close=100.0, roll=False, drop=(), end="15:59"):
    """Build an RTH session of flat bars at 100, with the rule bars set."""
    index = pd.date_range(f"{session} 09:30", f"{session} {end}", freq="min",
                          tz="America/New_York")
    df = pd.DataFrame({"open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0}, index=index)
    df.loc[index.time == h003.OPEN_BAR, "open"] = open_
    df.loc[index.time == h003.CLOSE_BAR, "close"] = close
    df["volume"] = 10
    df["session"] = pd.Timestamp(session).date()
    df["rth"] = True
    df["roll_window"] = roll
    for t in drop:
        df = df[df.index.time != t]
    return df


def trades(*days, suspect=()):
    rows = [h003.summarize_session(d, d["session"].iloc[0] in suspect) for d in days]
    return h003.make_trades(pd.DataFrame(rows))


MON, TUE, FRI = "2024-07-01", "2024-07-02", "2024-07-05"
NEXT_MON = "2024-07-08"


def test_long_from_close_to_next_open():
    t = trades(day(MON, close=100), day(TUE, open_=102, close=103))
    assert len(t) == 1
    row = t.iloc[0]
    assert (row.entry, row.exit, row.gross_points) == (100, 102, 2)
    assert row.bp == pytest.approx((2 - h003.COST) / 100 * 1e4)


def test_benchmark_is_next_sessions_regular_hours():
    row = trades(day(MON, close=100), day(TUE, open_=102, close=101)).iloc[0]
    assert row.bench_bp == pytest.approx((101 - 102 - h003.COST) / 102 * 1e4)


def test_last_session_has_no_trade():
    assert trades(day(MON)).empty


def test_missing_entry_or_exit_bar_skips_the_night():
    assert trades(day(MON, drop=[h003.CLOSE_BAR]), day(TUE)).empty
    assert trades(day(MON), day(TUE, drop=[h003.OPEN_BAR])).empty


def test_early_close_entry_is_skipped():
    assert trades(day(MON, end="12:59"), day(TUE)).empty


def test_suspect_session_on_either_side_skips_the_night():
    mon = pd.Timestamp(MON).date()
    tue = pd.Timestamp(TUE).date()
    assert trades(day(MON), day(TUE), suspect={mon}).empty
    assert trades(day(MON), day(TUE), suspect={tue}).empty


def test_roll_window_on_either_side_skips_the_night():
    assert trades(day(MON, roll=True), day(TUE)).empty
    assert trades(day(MON), day(TUE, roll=True)).empty


def test_gap_longer_than_four_days_skips_the_night():
    assert len(trades(day(MON), day("2024-07-05"))) == 1     # 4 days: weekend plus a holiday
    assert trades(day(MON), day("2024-07-06")).empty           # 5 days: a session is missing


def test_weekend_hold_counts_and_is_flagged():
    t = trades(day(FRI, close=100), day(NEXT_MON, open_=101))
    assert len(t) == 1 and bool(t.iloc[0].weekend)


def test_always_long_one_trade_per_night():
    t = trades(day(MON, close=100), day(TUE, open_=98, close=99), day("2024-07-03", open_=99))
    assert list(t.gross_points) == [-2, 0]
