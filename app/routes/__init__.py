from flask import Blueprint, render_template, abort, request

from app import charts
from db import data_service

main = Blueprint('main', __name__)

# Single source of truth for the projects data: the nav bar, the landing
# cards, the chapter routes. Scope badge tells, which geography the chapter covers.
CHAPTERS = [
    {
        "num": 1, 
        "slug": "context", 
        "title": "Context",
        "scope": "🌍",
        "scope_label": "Global",
        "tagline": "Air pollution and emissions are rising. Is it the fault of "
        "urbanization, or is there another driver at work?",
        "stat": "r ≈ 0.75",
        "stat_label": "how strongly wealth predicts CO₂ - far more than density or urbanisation",
        "conclusion": ("It's not about urbanization or population density. The thing that actually tracks "
        "emissions is <span class=\"hot\">wealth</span> and what a country <em>burns</em> to sustain the level."),
    },
    {
        "num": 2, 
        "slug": "decoupling", 
        "title": "Decoupling",
        "scope": "🇪🇺➕", 
        "scope_label": "Europe+",
        "tagline": "29 of 34 European countries cut CO₂ while their GDP grows. The consumption "
                    "lens reveals who genuinely decoupled and who just offshored their emissions.",
        "stat": "29/34",
        "stat_label": "European countries grew GDP while territorial CO₂ fell",
        "conclusion": ("Most of the analyzed countries 'passed the test' - they are indeed <em>striving to decouple</em> "
                       "economic growth from emissions. However, some have <span class=\"hot\">shifted</span> "
                       "the direction of their emissions rather than their volume."),
    },
    {
        "num": 3, 
        "slug": "structure", 
        "title": "Structure",
        "scope": "🇪🇺",
        "scope_label": "Eurostat cities",
        "tagline": "Do genuine decouplers build cities differently?",
        "stat": "size",
        "stat_label": "not honesty, is what actually predicts a European city's car dependency",
        "conclusion": ("Genuine decouplers don't build greener cities. What predicts a European city's "
                       "car dependency is its <span class=\"hot\">size</span> - not its country's "
                       "<em>honesty</em>."),
    },
    {
        "num": 4, 
        "slug": "synthesis", 
        "title": "Synthesis",
        "scope": "🇪🇺➕", 
        "scope_label": "Europe+",
        "tagline": "The Transition Performance Index: blend of reducing trends and current state, "
        "relative indexes and absolute numbers. And the punchline.",
        "stat": "40%",
        "stat_label": "of the score is weighted on honesty, so offshoring emissions is not encouraged",
        "conclusion": ("Even European leaders are reducing emissions <span class=\"hot\">twice as slowly</span> "
                       "as needed by 2050. Being at the top <em>doesn't</em> always mean doing enough."),
    },
    {
        "num": 5,
        "slug": "methodology",
        "title": "Methodology",
        "scope": "🔬",
        "scope_label": "Under the hood",
        "tagline": "How decoupling is measured, how the honesty verdict is decided, how the Transition "
        "Performance Index is built, weighted and stress-tested - everything is here.",
        "stat": "6",
        "stat_label": "independent fairness tests the ranking survived before it was trusted",
        "conclusion": "",
    },
]
CHAPTERS_BY_SLUG = {c["slug"]: c for c in CHAPTERS}


@main.app_context_processor
def inject_chapters():
    """Make the chapter list available to every template (nav bar, footer, etc.)."""
    return {"chapters": CHAPTERS}


@main.route('/')
def index():
    # Landing hook: how many of the countries that *claim* territorial decoupling
    # actually hold up once you count imported (consumption) emissions.
    verdicts = data_service.get_decoupler_class()
    genuine = int((verdicts["verdict"] == "genuine").sum())
    return render_template('index.html', genuine_count=genuine, total_count=len(verdicts))


def _chart_block(block_id, title, scope, takeaway, fig, section=None, legend=None):
    return {
        "id": block_id, 
        "title": title, 
        "scope": scope, 
        "section": section,
        "takeaway": takeaway, 
        "fig_json": fig.to_json(), 
        "legend": legend
    }


def _toggle_block(block_id, title, scope, takeaway, fig_2000, fig_1990,
                  section=None, labels=("Since 2000", "Since 1990"), legend=None):
    """Package twofigures (base 2000 + 1990) into one block. The template renders the
    custom .base-toggle buttons and charts.js swaps between them (replaces Plotly's
    native updatemenus - see build_tpi_score / build_decoupling_index).

    legend: same custom-legend list as _chart_block (the key is base-year-independent,
    so one static legend serves both toggled figures)."""
    return {
        "id": block_id, "title": 
        title, "scope": 
        scope, "section": section,
        "takeaway": takeaway,
        "fig_json": fig_2000.to_json(),
        "fig_json_alt": fig_1990.to_json(),
        "toggle": [{"base": "2000", "label": labels[0]},
                   {"base": "1990", "label": labels[1]}],
        "legend": legend,
    }


# Chapter 1 narrative
_SEC_ACCUSED = "The delusion"
_SEC_DRIVER = "The real driver"
_SEC_TWIST = "The twist"

# Chapter 2 narrative
_SEC_FLAT = "The flattering lens"
_SEC_HONEST = "The honesty check"
VERDICT = "The verdict"

# Chapter 3 narrative
_SEC_HYPOTHESIS = "The tempting hypothesis"
_SEC_TEST = "Reality check"
_SEC_SIZE = "The real driver"

# Chapter 4 narrative
_SEC_RANK = "The ranking"
_SEC_ANATOMY = "Anatomy of a score"
_SEC_CAVEATS = "Are they good enough?"


_CHAPTER_INTRO = {
    "context": (
        "Most of humanity live in cities nowadays. Sometimes it seems like urbanization is the root of the planet's "
        "pollution problem. Data don't suggest it and points to the real source."
    ),
    "decoupling": (
        "On paper, Europe's climate policy looks impressive and quite optimistic: 29 out of 34 countries "
        "have reduced their territorial carbon dioxide while their economies continued to grow. In this "
        "chapter, I'll examine this claim - first by giving it credit, and then by testing whether it holds "
        "up to an honest look at what these countries actually consume."
    ),
    "structure": (
        "In the previous chapter, I sorted countries into groups based on their decoupling performance. "
        "Now I'd like to test the hypothesis that 'genuine decoupling' countries are qualitatively changing "
        "the behavior of urban residents: fewer cars, 'greener' infrastructure, etc."
    ),
    "synthesis": (
        "Everything so far converges here. The Transition Performance Index combines decoupling honesty, "
        "absolute footprint, grid cleanliness, prosperity and pace into a single criterion-referenced "
        "score - weighted 40% on honesty, so that offshoring emissions can't get a good grade. An index deserves "
        "trust only when it has a connection to reality. Does it have one? Let's find out together."
    ),
}
_SECTION_INTRO = {
    "context": {
        _SEC_ACCUSED: (
            "Urbanization and CO₂ emissions are indeed growing in tandem around the world. "
            "This is why cities are often seen as the main reason."
        ),
        _SEC_DRIVER: (
            "But if you split the same countries by income - the relationship breaks down: population density "
            "tells almost nothing about emissions, while wealth predicts almost everything."
        ),
        _SEC_TWIST: (
            "Europe is organized differently from the rest of the world."
        ),
    },
    "decoupling": {
        _SEC_FLAT: (
            "Every figure here only takes into account CO₂ emissions within a country's own borders - "
            "the figures reported by governments."
        ),
        _SEC_HONEST: (
            "Territorial numbers can't see emissions embodied in imports - so a country can look "
            "quite clean by buying its goods from someone else. "
            "Let's take a look at what the combination of consumption and territorial CO₂ gives us."
        ),
    },
    "structure": {
        _SEC_HYPOTHESIS: (
            "If genuinely decoupling countries build differently, their cities should be less dependent on "
            "cars. Here is the median value for each country, colored according to the decoupling verdict."
        ),
        _SEC_TEST: (
            "As a verdict, compare the city's car dependency in each country. If the hypothesis were correct - "
            "the genuine block would be located clearly below all the others, without overlapping them."
        ),
        _SEC_SIZE: (
            "Car dependency is tracked by city size, not by decoupling level. The bigger the city, the fewer cars per person."
        ),
    },
    "synthesis": {
        _SEC_RANK: (
            "The headline ranking excludes three countries because its numbers are distorted (Ireland's "
            "profit-shifted GDP, Luxembourg's cross-border workforce and tiny Malta) and boundary case "
            "(Norway) is marked with an asterisk. Try to switch the base year and see how much the "
            "advantage of the post-Soviet countries disappears if the counting starts in 2000 instead of 1990."
        ),
        _SEC_ANATOMY: (
            "No two scores are built the same way. Honesty is the tall green base, so it looks decisive - "
            "yet the final totals sit close together. Treat a similar rank as a tie, not a clear win."
        ),
        _SEC_CAVEATS: (
            "A high rank means 'ahead of the rest of Europe', not 'finished'. Two last checks keep the ranking honest: "
            "where each country really stands today, and whether even the leaders are cutting fast enough."
        ),
    },
}


def _context_blocks():
    """Chapter 1 - urbanization is often blamed for pollutions and cities look guilty, but in fact wealth drives emissions."""
    ds, ch = data_service, charts
    GL = "🌍 Global"
    ACCUSED, DRIVER, TWIST = _SEC_ACCUSED, _SEC_DRIVER, _SEC_TWIST
    income_legend = [
        {"color": "#14532d", "label": "High income", "round": True},
        {"color": "#7fae5a", "label": "Upper middle income", "round": True},
        {"color": "#d59a4a", "label": "Lower middle income", "round": True},
        {"color": "#c2603f", "label": "Low income", "round": True},
    ]
    return [
        _chart_block(
            "urban-by-income",
            "Urbanization and CO₂ rise together across the world. Case closed?",
            GL,
            "Richer countries are both more urban and higher-emitting - in fact, one factor stimulates the other. "
            "Due to that, urbanization may become an object of special attention.",
            ch.build_urban_by_income(ds.get_co2_urban_by_income()),
            section=ACCUSED,
            legend=[{"color": "#14532d", "label": "Average CO₂/capita (tonnes)"},
                    {"color": "#c2603f", "label": "Average urban population (%)", "line": True}],
        ),
        _chart_block(
            "density-vs-emissions",
            "Do dense countries pollute more?",
            GL,
            "Density isn't a causer here. Dense and sparse countries pollute in the same range.",
            ch.build_density_vs_emissions(ds.get_density_vs_co2()),
            section=DRIVER,
            legend=income_legend,
        ),
        _chart_block(
            "gdp-vs-co2",
            "Does wealth predict emissions?",
            GL,
            "GDP per capita is the single strongest predictor of CO₂ emissions. (r ≈ 0.75) - the correlation with GDP is "
            "far stronger than with density or urbanisation indexes. This is the real factor today.",
            ch.build_gdp_vs_co2(ds.get_gdp_vs_co2()),
            section=DRIVER,
            legend=income_legend,
        ),
        _chart_block(
            "urban-vs-pm25",
            "How does urbanization influence air pollution?",
            GL,
            "Globally, this relationship is weak and noisy - some highly urbanized countries have "
            "the dirtiest air. But if you look at European countries (highlighted), the situation "
            "changes dramatically: the more urban the country, the lower the PM2.5 level. Air quality "
            "depends on what you burn, not population density.",
            ch.build_urban_vs_air_pollution(ds.get_urban_vs_air_pollution()),
            section=TWIST,
            legend=[{"color": "#9db3a5", "label": "Rest of world", "round": True},
                    {"color": "#c2603f", "label": "Europe", "ring": True}],
        ),
    ]


def _decoupling_blocks():
    """Chapter 2 - the decoupling storyline: flattering territorial lens -> honesty check -> verdict."""
    ds, ch = data_service, charts
    EU = "🇪🇺 Europe"
    FLAT, HONEST = _SEC_FLAT, _SEC_HONEST
    return [
        _chart_block(
            "top-reducers", 
            "Who cut the most? Top 15 European reducers over the last decade", 
            EU,
            "Let's take a first look: the biggest territorial CO₂/capita cuts of the "
            "last decade. The rest of this chapter asks how many of them are real.",
            ch.build_top_reducers(ds.get_top_reducers()), 
            section=FLAT
        ),
        _chart_block(
            "emissions-peak", 
            "How far past peak?", 
            EU,
            "Most of Europe is far below its all-time emissions peak, but for the post-Soviet economies "
            "the peak was in 1985-89, which can be explained as an industrial collapse rather than a deliberate policy.",
            ch.build_emissions_peak(ds.get_emissions_peak()), 
            section=FLAT
        ),
        _chart_block(
            "decade-change", 
            "The trajectory, decade by decade", 
            EU,
            "Green colour = CO₂/capita fell that decade. Eastern Europe demonstrate a dramatic drop in the 1990s. "
            "Western Europe's sustainable progress shows up in 2010s - the result of a deep review of environmental policy.",
            ch.build_decade_change(ds.get_decade_change()), 
            section=FLAT
        ),
        _toggle_block(
            "decoupling-index",
            "Economy growth up, emissions down? Decoupling elasticity map",
            EU,
            "The Tapio decoupling model, developed by Petri Tapio, measures the elasticity between economic growth "
            "(GDP) and environmental impact (CO₂ emissions). Bottom-right = GDP grew while territorial CO₂ fell - "
            "that's decoupling. Try to toggle the base year: a 1990 base flatters the post-Soviet economies, 2000 gives "
            "the fairer view. Both views are measured at 2022, the latest year with GDP figures for every country.",
            ch.build_decoupling_index(ds.get_decoupling_index(2000)),
            ch.build_decoupling_index(ds.get_decoupling_index(1990)),
            section=FLAT,
            legend=[
                {"color": "#14532d", "label": "Strong decoupling", "round": True},
                {"color": "#7fae5a", "label": "Weak decoupling", "round": True},
                {"color": "#d59a4a", "label": "Coupling", "round": True},
                {"color": "#a89e8a", "label": "Recession", "round": True},
            ],
        ),
        _chart_block(
            "consumption-gap", 
            "What countries consume vs what they emit", 
            EU,
            "Positive gap (red) = a country's footprint is bigger than its territorial number - "
            "emissions imported from elsewhere.",
            ch.build_consumption_gap(ds.get_consumption_gap()),
            section=HONEST,
            legend=[
                {"color": "#c2603f", "label": "Net importer (consumes more CO₂)"},
                {"color": "#14532d", "label": "Net exporter (emits more CO₂)"},
            ],
        ),
        _chart_block(
            "fake-board", 
            "The offshoring board", 
            EU,
            "Net imported emissions as a share of territorial CO₂. Malta, Switzerland and "
            "Belgium consume far more carbon than they produce themselves.",
            ch.build_fake_decoupler_board(ds.get_fake_decoupler_board()), 
            section=HONEST
        ),
        _chart_block(
            "verdict-board", 
            "Genuine, fake, or not a decoupler at all?",
            EU,
            "The synthesis: each country placed by how deeply territorial CO₂ fell, coloured by how much of that "
            "cut survives once consumption is counted - green genuine, bronze partial, red fake. The red ones "
            "mostly moved the address of their emissions, not their footprint.",
            ch.build_decoupler_board(ds.get_decoupler_class()), 
            section=VERDICT
            ),
    ]


def _structure_blocks():
    """Chapter 3 - the null result: honesty doesn't shape cities; city size does."""
    ds, ch = data_service, charts
    EU = "🇪🇺 Europe"
    HYPOTHESIS, TEST, SIZE = _SEC_HYPOTHESIS, _SEC_TEST, _SEC_SIZE

    city_cars = ds.get_city_cars_by_country()
    n_countries = len(city_cars)
    n_cities = int(city_cars["n_cities"].sum())
    present = set(city_cars["verdict"])
    car_verdict_legend = [{"color": ch._VERDICT_COLORS[v], "label": ch._VERDICT_LABEL[v]}
                          for v in ch._VERDICT_ORDER if v in present]
    return [
        _chart_block(
            "median-city-cars-by-country",
            "Do 'honest' countries have less car-dependent cities?",
            EU,
            "Each bar is a country's median amount of cars per 1,000 people, coloured by its decoupling "
            "verdict. As we can see, the specifics of the country affect much more than decoupling level. "
            f"A scope caveat: Eurostat publishes city car statistics for only {n_countries} of the 34 countries "
            f"({n_cities} cities). Every verdict except degrowth shows up here, including one 'no decoupling' "
            "case (Spain); but Austria, Ireland and Cyprus have no city data, so this chapter tests the "
            "hypothesis on a subset of Europe, not the full set.",
            ch.build_city_cars_by_country(city_cars),
            section=HYPOTHESIS,
            legend=car_verdict_legend,
        ),
        _chart_block(
            "cars-distr-by-verdict",
            "Median amount of cars by decoupling verdict",
            EU,
            "Split each city by its country's verdict and every tier overlaps almost entirely - genuine, "
            "partial and even 'no decoupling' Spain sit right on top of each other, all slightly above fake, "
            "not below it. So the hypothesis has not been confirmed.",
            ch.build_cars_dist_by_verdict(ds.get_city_cars_snapshot()),
            section=TEST,
        ),
        _chart_block(
            "cars-by-size-band",
            "Does car dependency fall when city size changes?",
            EU,
            "Bucketed by population, median amount of cars per 1,000 people falls monotonically as cities grow. "
            "Size, not honesty, is what actually predicts how car-dependent a European city is.",
            ch.build_cars_by_size_band(ds.get_city_cars_snapshot()),
            section=SIZE,
            legend=[{"color": "#7fbf8f", "label": "Median cars per 1,000 people, by city-size band"}],
        ),
    ]


def _synthesis_blocks():
    """Chapter 4 - the capstone: the honest ranking, then two caveats that keep it humble."""
    ds, ch = data_service, charts
    EU = "🇪🇺 Europe"
    RANK, ANATOMY, CAVEATS = _SEC_RANK, _SEC_ANATOMY, _SEC_CAVEATS
    tpi_2000, tpi_1990 = ds.get_tpi_leaderboard(2000), ds.get_tpi_leaderboard(1990)

    _head = tpi_2000[~tpi_2000["flag"].fillna("").str.contains("!")].sort_values("final", ascending=False).head(15)
    _bars_present, _dots_present = set(_head["verdict"].dropna()), set(tpi_2000["verdict"].dropna())
    verdict_bars = [{"color": ch._VERDICT_COLORS[v], "label": ch._VERDICT_LABEL[v]}
                    for v in ch._VERDICT_ORDER if v in _bars_present]
    verdict_dots = [{"color": ch._VERDICT_COLORS[v], "label": ch._VERDICT_LABEL[v], "round": True}
                    for v in ch._VERDICT_ORDER if v in _dots_present]
    return [
        _toggle_block(
            "tpi-leaderboard",
            "The honest ranking: leaders by Transition Performance Index",
            EU,
            "Sweden, Portugal and Finland lead - all genuine decouplers. The bronze bars just behind them "
            "(the UK, Denmark, France) grew rich and cut emissions too, but only partially decoupled - a real "
            "cut with part of it are offshored - so the honesty weighting keeps them out of the leading group.",
            ch.build_tpi_score(tpi_2000),
            ch.build_tpi_score(tpi_1990),
            section=RANK,
            legend=verdict_bars,
        ),
        _chart_block(
            "rank-shift",
            "Post-Soviet recession reshuffles the ranking",
            EU,
            "Lines sloping down to the right lose their rank when the base year is moved from 1990 to 2000 - "
            "their advantage was built on the early-1990s industrial collapse, not intentional policy. "
            "Portugal climbs against the tide. Netherlands goes down.",
            ch.build_rank_shift(tpi_2000, tpi_1990),
            section=RANK,
            legend=verdict_dots,
        ),
        _chart_block(
            "tpi-weighted-contributions",
            "What drives each score? Weighted contributions (2000 base, top 15)",
            EU,
            "What lifts the leaders is honesty - the big green base under every bar. Still, "
            "two countries can finish neck and neck by very different routes: a clean grid here, "
            "more wealth there, a strong recent push somewhere else.",
            ch.build_tpi_weighted_contribution(tpi_2000),
            section=ANATOMY,
            legend=[
                {"color": "#14532d", "label": "Honesty (consumption cut - fake-decoupling penalty)"},
                {"color": "#3f7f88", "label": "Territorial CO₂/capita cut"},
                {"color": "#9c6f84", "label": "Consumption CO₂/capita"},
                {"color": "#d59a4a", "label": "Grid cleanliness"},
                {"color": "#7f8a72", "label": "GDP per capita"},
                {"color": "#cbbfa6", "label": "Momentum (recent trend, ±3)"},
            ],
        ),
        _chart_block(
            "tpi-journey",
            "Journey vs destination: a good score isn't a clean footprint",
            EU,
            "Almost all countries remain far from the 2 t/capita fair-share target. A high TPI marks "
            "the countries that are adapting best compared to Europe - they're moving faster, but "
            "they're still on the way.",
            ch.build_tpi_journey(tpi_2000),
            section=CAVEATS,
            legend=verdict_dots,
        ),
        _chart_block(
            "tpi-sufficiency",
            "Sufficiency: are even the leaders fast enough?",
            EU,
            "This is the punchline of the whole project. With current pace only Portugal, among the top-15, "
            "will reach the climate-neutral aim (2t/capita) by 2050. Honestly, we have a long way to go.",
            ch.build_tpi_sufficiency(ds.get_tpi_sufficiency()),
            section=CAVEATS,
            legend=[
                {"color": "#9db3a5", "label": "Actual pace (2010 → latest)"},
                {"color": "#c2603f", "label": "Required for 2 t/capita by 2050"},
            ],
        ),
    ]


def _charts_for(slug):
    """Ordered chart blocks for a chapter, or [] if it isn't built yet (falls back to the stub)."""
    if slug == "context":
        return _context_blocks()
    if slug == "decoupling":
        return _decoupling_blocks()
    if slug == "structure":
        return _structure_blocks()
    if slug == "synthesis":
        return _synthesis_blocks()
    return []


@main.route('/chapters/<slug>')
def chapter(slug):
    ch = CHAPTERS_BY_SLUG.get(slug)
    if ch is None:
        abort(404)
    if slug == "methodology":
        robustness = charts.build_tpi_robustness(data_service.get_tpi_leaderboard(2000))
        return render_template('methodology.html', chapter=ch,
                               robustness_fig_json=robustness.to_json())
    blocks = _charts_for(slug)
    template = 'chapter.html' if blocks else 'chapter_stub.html'
    return render_template(template, chapter=ch, charts=blocks,
                           chapter_intro=_CHAPTER_INTRO.get(slug),
                           section_intros=_SECTION_INTRO.get(slug, {}))


@main.route('/.well-known/appspecific/com.chrome.devtools.json')
def _chrome_devtools_probe():
    return ('', 204)
