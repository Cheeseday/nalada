# Transition Performance Index (TPI) - Methodology

Companion to [`08_decoupling_index.ipynb`](08_decoupling_index.ipynb). What the index measures, every knob, and the battery of fairness checks ("referees") it must survive.

## What is this analysis about? 

The TPI scores European countries 0–100 on how well they combine an **honest, consumption-based emissions reduction** with a **clean grid**, a **low absolute footprint** and **real prosperity**. It isn't actually a "decoupling index" because it deliberately blends decoupling *rates* (how fast emissions fell) with current *states* (where the country stands today). Decoupling is one input, not the whole claim.

Two design principles:

1. **Consumption-based accounting is the spine.** Territorial numbers let a country look green by offshoring its factories. The heaviest component measures whether the *honest* number - what residents actually consume, not only produce.
2. **Criterion-referenced scoring.** Every metric is scored against fixed real-world anchors (e.g. 2 t/cap = Paris-compatible fair share). Scores mean something on their own, and adding/removing a country never reshuffles the rest.

## Components and weights

| Component | Weight | What it measures | Anchor (0 pts - 100 pts) |

| **Honesty** | 0.40 | Consumption-CO2/capita reduction (blend: 60% long-run from base year and 40% since 2010) **minus** a fake-decoupling penalty when territorial fell much more than consumption. **Can go negative.** | reduction 0% -> 45% (long), 0% -> 30% (recent); penalty 0 -> 60 pts over 0–60% divergence |
| **Energy cleanliness** | 0.15 | Absolute current grid intensity (kg CO2/kWh) - rewards *being* clean, not just getting cleaner | 0.30 (coal grid) - 0.03 (near-zero-carbon, looks like a good aim for modern society) |
| **Absolute consumption** | 0.15 | Consumption CO2/capita today - it's about destination and 2 tonnes is a good aim as well | 16 t - 2 t |
| **Prosperity** | 0.15 | 60% absolute GDP/capita + 40% growth *guard* (full marks for any positive growth; only shrinking economies lose points - it kills the post-communist deindustrialization pit) | GDP $15k -> $60k; growth −30% -> 0% |
| **Territorial reduction** | 0.15 | Classic headline cut in CO2/capita from base year | 0% -> 55% (~ EU Fit-for-55 ambition) |

Plus a **momentum modifier** (±3 pts on top): smoothed consumption-CO2 slope 2010->latest. Small by design - a tiebreaker, not a driver.

**Two base years (1990 and 2000), always shown side by side.** It's anattempt to dismiss the collapse of the economy in countries with Soviet influence. 2000 is more fair for all Europe in that sense. The *shift between the two rankings* is itself a real finding.

**Per-capita everywhere** - controls for Eastern Europe's large population decline (falling totals from emigration are not decoupling).

**Missing components:** weights renormalize over what's available; a country must have at least territorial reduction + absolute consumption to be ranked. If consumption data starts late (Norway: 2003), honesty is measured from that year - for both curves, so the fake-penalty comparison stays fair.

## Flags

- **`!` data-quality** (IRL, LUX, MLT) - the input numbers themselves are distorted (Irish GDP inflated by multinational profit-shifting; Luxembourg's per-capita denominators broken by cross-border workers; Malta is tiny/sparse). **Excluded from the headline ranking**, shown in the full one.
- **`*` accounting-boundary** (NOR) - the data is accurate but the accounting *frame* is kind: emissions from Norway's exported oil and gas burn abroad, outside both territorial and consumption accounting. **Kept in the ranking, visibly flagged** - I flag rather than punish until it can be quantified fairly for *all* countries. Future quantification path: extraction-based accounting from the OWID energy dataset (`oil_production`/`gas_production`/`coal_production`, TWh) × IPCC combustion factors; underlying source Energy Institute Statistical Review; framing UNEP Production Gap Report.

## Context layers (it doesn't affect the rating, just for additional context)

- **Sufficiency overlay** - the index is *relative* virtue; this checks countries against *physics*. At each country's actual consumption-CO2 pace (2010->latest), when does it reach ~2 t/cap? Compared with the rate required by 2050. Expected headline: almost nobody in Europe is Paris-sufficient. This is the one of key points of yhis index - a high TPI rank means "best in Europe," not "fast enough."
- **Historical responsibility** - cumulative CO2 since 1750 (total, share of global, per capita) from the raw OWID file. The atmosphere integrates over 150 years. My index show only recent decades.

## The six fairness referees

The ranking is only trusted to the extent it survives attacks on every subjective choice:

| # | Referee | What it varies | Pass criterion |

| 1 | **Named scenarios** | 6 deliberate weightings (equal, honesty-heavy, destination-heavy, prosperity-heavy, reduction-heavy) | small `rank_range` per country |
| 2 | **Weight Monte Carlo** | 2,000 random weight vectors (Dirichlet over the full simplex) | high `pct_top5` / `pct_top10`; tight box plots |
| 3 | **Rank correlation + leave-one-component-out** | drops each component entirely, renormalizes the rest | Spearman vs normative ≈ 1; no single component reorders the top |
| 4 | **Threshold robustness** | jitters every scoring anchor ±15%, 200 full rebuilds | same leaders as Referee 2 -> robust to *both* subjective layers (weights **and** anchors) - the check most published indices skip |
| 5 | **Component redundancy** | correlation matrix of the five component scores | no pair \|r\| > 0.6 (no double-counting, construct validity) |
| 6 | **Input-noise propagation** | consumption series ±12% systematic + ±5% yearly, territorial ±3% (MRIO uncertainty per Owen 2017, Wiedmann & Lenzen 2018), 300 rebuilds | scores reported as mean ± 95% CI with **rank intervals**. CI-overlapping countries are *statistically tied* |

Sampling note: 2,000 draws give proportion estimates accurate to ~±2 pp - more draws sharpen nothing material.

## Honest limitations (kept on purpose)

- **Europe-only.** The continent is the easy case - deindustrialized and import-heavy. Without non-European comparators the index cannot see whether the whole leaderboard is successful offshoring at scale.
- **No bunker fuels** (international aviation/shipping) and **no land-use (LULUCF)** emissions, because OWID's standard consumption columns exclude them.
- **Per-capita lens.** To a lesser extent, it takes into account the real impact of the country on the pollution of the planet, but it is more fair to people.
## How to read the result

The defensible summary is not "Country X is #1." It is:

> *"A leading group - stable across 2,000 random weightings, ±15% threshold jitter, and propagated input noise - outperforms the rest of Europe on honest transition metrics; and even that group is not yet cutting consumption emissions at a Paris-compatible pace."*
