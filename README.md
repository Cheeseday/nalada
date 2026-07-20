# Nalada

**Have 29 European countries really decoupled growth from CO₂ - or just offshored their emissions?**

A data investigation in four chapters, ending in an honesty-weighted Transition Performance Index.

<p align="center">
  <img src="app/static/img/og-cover.png" alt="Nalada - 29 of 34 European countries report decoupling; only 15 genuinely did." width="840">
</p>

<p align="center">
  <img alt="Python 3.11" src="https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white">
  <img alt="Flask 3.1" src="https://img.shields.io/badge/Flask-3.1-000000?logo=flask&logoColor=white">
  <img alt="PostgreSQL" src="https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white">
  <img alt="Plotly 6.8" src="https://img.shields.io/badge/Plotly-6.8-3F4F75?logo=plotly&logoColor=white">
  <img alt="License MIT" src="https://img.shields.io/badge/License-MIT-14532d">
</p>

> **Live demo:** _not deployed yet - link goes here once Render is live._

---

## The question

**Territorial** emissions - what a country burns inside its borders - tell a flattering story.

**Consumption** emissions - what its people actually consume, wherever it was made - tell an honest one.
The gap between the two indicators is where borrowed green credentials hide.

On paper, **29 of 34** European countries (1990–2023) grew their GDP while territorial CO₂ fell.
Switch to the consumption lens, and only **15** genuinely did.

## What it finds

Every country gets one verdict, from a single classifier built in notebook 04 and stored in one table,
so all four chapters speak the same vocabulary:

| Verdict | Countries | Meaning |
| --- | :---: | --- |
| **Genuine** | 15 | The reported reduction is backed by a real consumption reduction |
| **Partial** | 6 | The reduction is real, but a large share was offshored |
| **Fake** | 7 | This reduction is mostly due to imported emissions |
| **No decoupling** | 4 | Territorial emissions barely moved |
| **Net exporter** | 1 | Exports more embedded CO₂ than it imports (Poland) |
| **Degrowth** | 1 | No growth to decouple from (Ukraine) |

Three findings that survived the analysis:

- **Wealth drives emissions - not urbanisation.** Income tracks CO₂ emissions at *r ≈ 0.75*, far more strongly than
  density or urbanisation share. Wealth - this is the real factor today.
- **Genuine decouplers don't build greener cities.** What predicts a European city's car dependency is its
  **size**, not its country's honesty. A hypothesis that died honestly.
- **Even the leaders aren't doing enough.** Only **2 of 34** countries are on a Paris-compatible path
  (2.0 t/capita by 2050). Even European leaders are reducing emissions twice as slowly as needed by 2050. 
  Being at the top doesn't always mean doing enough.

## The chapters

| # | Chapter | Scope | The question it answers |
| :---: | --- | --- | --- |
| 01 | **Context** | 🌍 Global | Air pollution and emissions are rising. Is it the fault of urbanization, or is there another driver at work? |
| 02 | **Decoupling** | 🇪🇺➕ Europe+ | Who genuinely decoupled, and who just offshored their emissions? |
| 03 | **Structure** | 🇪🇺 Eurostat cities | Do genuine decouplers build cities differently? |
| 04 | **Synthesis** | 🇪🇺➕ Europe+ | The Transition Performance Index and the punchline of the whole project. |
| 05 | **Methodology** | 🔬 Under the hood | How decoupling is measured, how the honesty verdict is decided, how the Transition Performance Index is built, weighted and stress-tested - everything is here. |

## The index

Chapter 4 ranks countries with a **Transition Performance Index (TPI)** that blends reduction trends with
current state, and relative indices with absolute levels. Its defining choice: **40% of the score is weighted
on honesty**, so offshoring emissions can't buy you a good rank.

The honesty verdict turns on a *real-share* ratio - how much of a country's reported cut survives the
consumption lens. The thresholds (>= 0.70 genuine, 0.30-0.70 partial, < 0.30 fake) aren't round numbers for
looks: both fall inside natural gaps in the data, so the split barely moves if you slightly altered thresholds.

The weighting is a judgement call, not a law of nature - so it's stress-tested rather than asserted.
Monte Carlo weight sampling and a set of fairness referees check that the leaders survive very different
weightings. Chapter 5 and [`analysis/08_INDEX_METHODOLOGY.md`](analysis/08_INDEX_METHODOLOGY.md) show the
full workings.

## Tech stack

| Layer | Choice |
| --- | --- |
| **Web** | Flask 3.1, server-rendered Jinja templates |
| **Data** | PostgreSQL + SQLAlchemy, raw SQL per query |
| **Analysis** | pandas 3.0, numpy 2.4, Jupyter notebooks |
| **Charts** | Plotly 6.8 - figures built server-side, rendered client-side |
| **Deploy** | Render (gunicorn) + Neon Postgres |

The app keeps three concerns apart: **`routes/`** orchestrates, **`charts/`** builds figures, and
**`db/data_service.py`** is the only thing that touches data. Notebooks do the investigation; the app only
reads the tables they produce.

## Data sources

| Source | What it provides |
| --- | --- |
| [Our World in Data](https://github.com/owid/co2-data) | Territorial & consumption CO₂, GDP, population, energy mix, trade-embedded CO₂ |
| [World Bank](https://data.worldbank.org/) | Urbanisation, population density, income group, PM2.5 exposure |
| [Eurostat Urban Audit](https://ec.europa.eu/eurostat/web/cities/database) | City population, cars per 1 000, green space, transport |

## Project structure

```
nalada/
├── app/                      # Flask application
│   ├── charts/               # Plotly figure builders (one module per chapter)
│   ├── routes/               # Chapter definitions (single source of truth) + views
│   ├── static/               # CSS, JS, favicons, social card
│   └── templates/            # Jinja templates
├── analysis/                 # Jupyter notebooks - the actual investigation
│   └── 08_INDEX_METHODOLOGY.md
├── db/
│   ├── queries/              # Raw SQL, one file per getter
│   ├── models.py             # SQLAlchemy schema (source tables)
│   ├── init_db.py            # Creates the schema
│   └── data_service.py       # The only data access layer the app uses
├── etl/                      # Loaders: OWID, World Bank, Eurostat
│   └── run_etl.py            # Full pipeline entry point
├── tests/
├── config.py                 # Reads .env
├── run.py                    # Local dev server
├── wsgi.py                   # Production entry point (gunicorn wsgi:app)
└── render.yaml               # Render blueprint
```

## Run it locally

**Prerequisites:** Python 3.11 and a running PostgreSQL server.

```bash
# 1. Clone
git clone https://github.com/Cheeseday/nalada.git
cd nalada

# 2. Environment - the app and the notebook stack
conda env create -f environment.yml
conda activate nalada
```

`environment.yml` is the full development environment, pinned to the versions the analysis actually ran on:
the web app plus jupyter, matplotlib, scipy, statsmodels and pytest. `requirements.txt` is a deliberately
lean subset - only what the Flask app imports at request time - and is what the deploy installs.

```bash
# 3. Database + config
createdb nalada
```

Create a `.env` in the project root:

```ini
DATABASE_URL=postgresql://user:password@localhost:5432/nalada
SECRET_KEY=any-random-string      # optional, defaults to "dev-secret"
FLASK_ENV=development             # "production" turns debug off
```

```bash
# 4. Schema, then data
python db/init_db.py     # creates countries, emissions, urbanization, cities, city_stats
python etl/run_etl.py    # OWID -> country enrichment -> World Bank -> Eurostat
```

The OWID CSV downloads itself on first run and caches to `data/` (gitignored); World Bank and Eurostat are
pulled from their APIs. Expect this step to take a few minutes.

> **⚠️ Step 5 is required - the app won't render without it.**
> Two tables the app reads (`decoupler_class` and `tpi_scores`) are **built by the notebooks**, not by the ETL.
> Run them once, in order:
>
> - `analysis/04_decoupling_analysis.ipynb` -> writes **`decoupler_class`** (every country's verdict)
> - `analysis/08_decoupling_index.ipynb` -> writes **`tpi_scores`** (the index)

```bash
# 6. Serve
python run.py            # → http://127.0.0.1:5000
```

## Tests

```bash
pytest
```

The suite is integration-level: it runs against a live, populated database and checks the data-service
contracts - expected columns, verdicts drawn from the allowed set, scores inside their bounds.

## Limitations

This project accuses others of giving themselves flattering reviews, so it owes you its own caveats:

- **Consumption CO₂ is modelled, not measured.** It's reconstructed with multi-regional input-output models
  that estimate the CO₂ embodied in trade, inheriting uncertainty from global trade tables and sector
  aggregation. It captures the trend, not a precise level.
- **The honesty weighting is a choice.** Scoring the index 40% on honesty is a deliberate decision, not a law
  of nature - though the fairness tests show the leaders survive very different weightings.

Chapter 5 lays out all six limitations alongside the full workings.

## License

[MIT](LICENSE) © 2026 Aleś Kiryluškin

---

**Aleś Kiryluškin** - Data Analyst
[GitHub](https://github.com/Cheeseday)
[LinkedIn](https://www.linkedin.com/in/ales-kirylushkin/)
