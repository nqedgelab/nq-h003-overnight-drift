# H-003 results: overnight drift

**Verdict: rejected at step 3 (validation).** It passed in sample, then lost money in 2022–2023. The holdout period was not used, so it stays unseen.

Run on 2026-11-01 with `python backtest/h003.py in_sample`. The rules are exactly those committed in [`hypothesis.md`](hypothesis.md) before this run, and the rule logic is unit-tested in [`backtest/test_h003.py`](backtest/test_h003.py).

## In sample, 2015–2021, after costs

| Measure | Value |
|:---|---:|
| Sessions | 1,807 |
| Trades (nights) | 1,523 |
| Win rate | 57.3% |
| Average win | 47.6 bp |
| Average loss | 51.8 bp |
| **Expectancy** | **+5.20 bp** |
| 95% bootstrap CI | +1.37 bp to +8.97 bp |
| Expectancy in points | +4.82 points (about $96 per contract) |
| Expectancy without the 10 best nights | +3.04 bp |
| Expectancy without the 10 worst nights | +7.83 bp |
| Expectancy before costs | +6.34 bp |
| Regular-hours benchmark, after costs | +2.75 bp (1,478 nights with a full exit session) |
| Median cost per trade | 1.09 bp |
| Max drawdown | 1,792 bp |
| Total | +7,924 bp |

- **Step 1 passes.** Expectancy is above zero and so is the lower bound of its confidence interval.
- **Step 2 passes.** +5.20 bp beats the regular-hours leg's +2.75 bp on the same nights.
- It also survives losing its 10 best nights, at +3.04 bp.

The largest nights were checked and are real market events, not contract-roll jumps: 2020-03-23 to 24 (+542 bp), 2020-03-06 to 09 (−643 bp), 2015-08-21 to 24 (−618 bp) and the Brexit vote night, 2016-06-23 to 24 (−370 bp).

## The case against this result

**Step 2's margin is not significant.** The rule compared point estimates, and +5.20 bp beat +2.75 bp. But the paired difference is +2.27 bp with a 95% CI of −3.8 to +8.5 bp. On these numbers alone, overnight and regular hours could earn the same.

**The overnight leg is longer.** On NQ, "overnight" is 17.5 hours of trading and regular hours is 6.5. If drift were spread evenly by clock time, the overnight leg would win step 2 just by being longer. That's a weakness in how step 2 was written, and it can't be changed now.

A fairer comparison is return per unit of risk. That check wasn't a rule, so it's reported here as context only:

| Leg | Gross return | Std. dev. | Share of return | Share of variance |
|:---|---:|---:|---:|---:|
| Overnight, 16:00 to 09:30 | +6.16 bp | 76.7 bp | 61% | 38% |
| Regular hours, 09:30 to 16:00 | +3.89 bp | 97.1 bp | 39% | 62% |

The overnight leg carried 61% of the return with 38% of the variance, about 2.5 times the return per unit of variance. That's what the published effect predicts, and it's more than time-proportional drift would explain. Still, 2015–2021 rose strongly, so the real test is validation.

**Most of it is recent.** Before 2020 the result was +3.09 bp with a CI including zero; 2020 on was +10.48 bp. 2020 alone (+13.20 bp) had the biggest nights of the sample.

## Breakdown (reported, not used to change the rules)

| Group | Trades | Win rate | Avg win bp | Avg loss bp | Expectancy bp | 95% CI | Regular hours bp |
|:---|---:|---:|---:|---:|---:|:---:|---:|
| All | 1523 | 57.3% | 47.6 | 51.8 | +5.20 | [+1.37, +8.97] | +2.75 |
| Weekend holds | 288 | 58.7% | 48.9 | 58.2 | +4.62 | [−6.10, +14.46] | +5.31 |
| Weeknights | 1235 | 57.0% | 47.3 | 50.3 | +5.34 | [+1.32, +9.37] | +2.21 |
| 2015 | 218 | 53.7% | 47.5 | 49.5 | +2.58 | [−8.35, +13.09] | −4.82 |
| 2016 | 219 | 54.8% | 37.3 | 45.1 | +0.01 | [−8.54, +8.12] | +0.50 |
| 2017 | 217 | 59.4% | 25.6 | 25.2 | +4.99 | [+0.57, +9.51] | +4.59 |
| 2018 | 216 | 54.2% | 54.4 | 57.3 | +3.18 | [−7.03, +13.20] | −2.39 |
| 2019 | 217 | 58.5% | 45.5 | 52.9 | +4.70 | [−3.90, +13.14] | +6.04 |
| 2020 | 218 | 61.9% | 75.3 | 87.8 | +13.20 | [−3.22, +29.40] | +10.44 |
| 2021 | 218 | 58.7% | 46.4 | 47.1 | +7.76 | [−0.65, +15.71] | +4.88 |
| Before 2020 | 1087 | 56.1% | 41.8 | 46.4 | +3.09 | [−0.90, +6.97] | +0.78 |
| 2020 on | 436 | 60.3% | 61.2 | 66.7 | +10.48 | [+1.55, +19.31] | +7.65 |
| Low volatility | 502 | 57.0% | 31.0 | 34.3 | +2.89 | [−1.34, +6.96] | +0.12 |
| Middle volatility | 501 | 54.9% | 36.2 | 46.3 | −1.05 | [−6.63, +4.26] | +3.08 |
| High volatility | 501 | 60.3% | 73.6 | 77.3 | +13.64 | [+4.19, +22.71] | +6.09 |
| Entry day up | 841 | 59.1% | 45.4 | 46.6 | +7.79 | [+2.83, +12.63] | −3.95 |
| Entry day down | 682 | 55.1% | 50.6 | 57.6 | +2.01 | [−4.06, +7.91] | +10.94 |

Every year's expectancy is zero or above, but only 2017's CI excludes zero. High-volatility and entry-day-up nights look stronger. Those groups come from this data, and the rules are frozen. Validation tests the rule as written, not its best-looking slice.

## Validation, 2022–2023, after costs

Run once on 2026-11-01 with `python backtest/h003.py validation`, with the rules unchanged. It was the first use of the validation period by any hypothesis.

| Measure | In sample | **Validation** |
|:---|---:|---:|
| Trades (nights) | 1,523 | 433 |
| Win rate | 57.3% | 48.7% |
| Average win | 47.6 bp | 63.4 bp |
| Average loss | 51.8 bp | 64.4 bp |
| **Expectancy** | +5.20 bp | **−2.14 bp** |
| 95% bootstrap CI | +1.37 to +8.97 | −10.42 to +6.04 |
| Expectancy in points | +4.82 | −3.09 |
| Without the 10 best nights | +3.04 bp | −8.38 bp |
| Without the 10 worst nights | +7.83 bp | +3.20 bp |
| Before costs | +6.34 bp | −1.58 bp |
| Regular-hours benchmark | +2.75 bp | +2.95 bp |
| Max drawdown | 1,792 bp | 2,096 bp |

Step 3 needed validation expectancy above zero. It was −2.14 bp, so H-003 is **rejected**. It also lost to the regular-hours leg, which earned +2.95 bp.

| Group | Trades | Win rate | Avg win bp | Avg loss bp | Expectancy bp | 95% CI | Regular hours bp |
|:---|---:|---:|---:|---:|---:|:---:|---:|
| All | 433 | 48.7% | 63.4 | 64.4 | −2.14 | [−10.42, +6.04] | +2.95 |
| Weekend holds | 83 | 48.2% | 42.0 | 57.1 | −9.34 | [−23.85, +5.54] | +14.99 |
| Weeknights | 350 | 48.9% | 68.4 | 66.2 | −0.44 | [−9.85, +9.24] | +0.42 |
| 2022 | 218 | 45.9% | 78.5 | 78.3 | −6.40 | [−20.53, +7.89] | −5.56 |
| 2023 | 215 | 51.6% | 49.8 | 48.7 | +2.17 | [−6.38, +11.04] | +11.58 |
| Low volatility | 138 | 52.9% | 44.5 | 42.3 | +3.62 | [−5.74, +13.21] | +3.51 |
| Middle volatility | 138 | 46.4% | 60.2 | 58.7 | −3.59 | [−16.07, +9.45] | +2.21 |
| High volatility | 138 | 46.4% | 87.1 | 87.4 | −6.47 | [−25.99, +13.54] | +8.75 |
| Entry day up | 232 | 47.8% | 54.3 | 63.7 | −7.27 | [−17.19, +2.80] | +0.20 |
| Entry day down | 201 | 49.8% | 73.5 | 65.3 | +3.78 | [−9.32, +17.19] | +6.08 |

## What validation says

- **It wasn't only the bear market.** 2022 fell, and the overnight leg lost 6.40 bp a night. But 2023 rose strongly, and overnight still made only +2.17 bp while regular hours made +11.58 bp. In a rising year, the gains came in the day session, which is the opposite of the claim.
- **The risk-adjusted case reversed too.** In sample, overnight carried 61% of the return with 38% of the variance. In validation, overnight gross return was −1.70 bp against +3.51 bp for regular hours, with overnight carrying 29% of the variance.
- **The in-sample slices that looked strongest failed.** High-volatility nights went from +13.64 bp to −6.47 bp, and entry-day-up nights from +7.79 bp to −7.27 bp. Using them as filters after seeing the in-sample table would have made things worse. That's the reason the rules were frozen.
- **The in-sample pass was most likely drift plus 2020.** Before 2020 the in-sample result already had a CI including zero.
