# H-003: overnight drift, buy the close and sell the open

- **Status:** rejected <!-- untested | testing | supported | rejected | inconclusive -->
- **Written:** 2026-11-01 (before any testing)

No close-to-open return has been looked at. The in-sample years were already used by H-001 (full-day trades) and H-002 (the 10:00 return and the 15:30–16:00 window). So it's known that 2015–2021 mostly rose, and that the last half hour drifted down. Validation and holdout are still untouched.

## Claim
On NQ, holding long from the 16:00 ET close to the 09:30 ET open of the next session has positive expectancy after costs. It also earns more than the regular-hours leg of the next session, 09:30 to 16:00, on the same days.

## Why it might work
The idea comes from outside this project. Cliff, Cooper and Gulen ("Return differences between trading and non-trading hours: like night and day", 2008) and Lou, Polk and Skouras ("A tug of war: overnight versus intraday expected returns", *Journal of Financial Economics*, 2019) found that most US equity index gains came between the close and the open. Regular-hours returns were near zero or negative over long periods.

Their proposed mechanisms:
- **Overnight risk premium.** Holding through the close means holding through news with no chance to exit until the open. Some investors pay to avoid that by being flat at the close.
- **Clientele.** Institutions tend to trade near the open and the close in ways that push prices in opposite directions, and retail flow at the open has been linked to buying pressure there.
- **Margin.** Intraday leverage that has to be cut by the close creates selling late in the day.

The other side is traders who go flat at the close: day traders, risk-limited desks, and anyone unwilling to hold through overnight news.

**The case against.**
- **Just drift.** 2015–2021 rose. Almost any long-only trade looks good there. That's why it must also beat the regular-hours leg, and why validation (2022–2023, which includes a bear market) is the real test.
- **Gap risk.** There's no stop. A few large overnight gaps could carry or wreck the result, so the "without the top 10 trades" check matters more than usual. It's also reported with the 10 worst trades removed.
- **Crowding.** The effect has been published since 2008, so it may have been traded away. H-002 showed that a published result needn't transfer to NQ at all.
- **Futures aren't the cash index.** NQ trades almost around the clock. The "overnight" premium in stock studies partly reflects markets being closed; on NQ, price discovery continues all night.

**The most likely outcome is a positive in-sample result that comes from drift, which then fails the regular-hours comparison or fails in validation.**

## Rules
All times New York (ET). Bars come from `nqlab.data`.

1. **Sessions.** Sessions are taken from the data with nothing dropped (`load(drop_suspect=False)`), so a dropped session can't be skipped over silently. The "next session" is the next one that appears there.
2. **Entry.** Long at the close of the 15:59 bar of a session. Skip the night if that bar is missing, which also skips early-close days.
3. **Exit.** At the open of the 09:30 bar of the next session. Skip the night if that bar is missing.
4. **Skipped nights.**
   - Either session is flagged suspect by `data.session_report()`.
   - The next session is more than 4 calendar days later. A weekend plus a holiday is 4 days; anything longer means a whole session is missing.
   - Either session is in `roll_window`. Prices aren't back-adjusted, so a hold across a contract switch would include the price jump between contracts.
5. **Weekends.** Friday-to-Monday holds count like any other night. They are reported separately.
6. **Size.** 1 contract, fixed. Always long. At most one trade per night.
7. **No filters.** There's no stop, target, day-of-week rule, trend filter or volatility filter. Any variant, such as skipping weekends or going flat before news, is a new hypothesis.

## Measurement
- **Unit.** There's no stop, so R isn't defined. Each trade is measured in **basis points of the entry price**, after costs, as in H-002.
- **Benchmark.** The regular-hours leg of the exit session: long at the 09:30 open, out at the 15:59 close, with the same costs. It's measured on the same nights, wherever the 15:59 bar of the exit session exists. The overnight trade has to beat it.

## Falsification
H-003 is **rejected** if any of these holds, checked in order:

1. In sample (2015–2021), expectancy after costs is ≤ 0 bp, or the lower bound of its 95% bootstrap confidence interval is ≤ 0 bp.
2. In sample, expectancy after costs is ≤ the regular-hours benchmark's expectancy after costs on the same nights.
3. Validation (2022–2023, looked at once), expectancy after costs is ≤ 0 bp.
4. Holdout (2024 onward, looked at once, only if 1–3 pass), expectancy after costs is ≤ 0 bp.

It's **supported** only if all four pass. It's **inconclusive** if any period has fewer than the minimum number of trades below.

Even if it passes, the result is fragile if a handful of nights drive it. The test reports expectancy with the 10 best trades removed and with the 10 worst removed. If removing the 10 best turns it negative, the verdict says so.

## Test plan
- **Data period.** The fixed splits in `nqlab/data.py`: in sample 2015–2021, validation 2022–2023, holdout 2024 to Jul 2025. A night belongs to the split of its entry session. Rules are frozen at this commit and can't be changed after seeing any result.
- **Minimum sample size.** 300 trades in sample and 100 each in validation and holdout. Skipping roll windows leaves roughly 85% of nights.
- **Costs assumed.**
  - Commission and fees: $2.50 per side, or 0.25 points per round trip ($20 per point).
  - Slippage: 1 tick (0.25 points) on entry and 1 tick on exit.
  - That's 0.75 points per round trip, charged in points and converted to basis points of the entry price. The benchmark pays the same.
- **Regimes to check separately** (reported, not used to rescue a failed result):
  - weekend holds vs weeknights;
  - each calendar year;
  - before and after 2020;
  - volatility tercile, using the previous 20 sessions' average daily range;
  - whether the entry session's own regular-hours leg was up or down.
- **Reported:** trade count, win rate, average win and loss in bp, expectancy in bp and in points, its bootstrap 95% CI, max drawdown in bp, expectancy without the 10 best and without the 10 worst trades, and the regular-hours benchmark.

## Result
**Rejected at step 3** (tested 2026-11-01).

- **In sample**, after costs: 1,523 nights, expectancy **+5.20 bp** (95% CI +1.37 to +8.97 bp), against +2.75 bp for the regular-hours leg. Steps 1 and 2 passed.
- **Validation**, after costs: 433 nights, expectancy **−2.14 bp** (95% CI −10.42 to +6.04 bp), against +2.95 bp for the regular-hours leg. Step 3 failed.

The holdout period was not used.

Full results: [`results.md`](results.md).
