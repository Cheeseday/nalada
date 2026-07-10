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
        "tagline": "27 of 34 European countries cut CO₂ while their GDP grows. The consumption "
                    "lens reveals who genuinely decoupled and who just offshored their emissions.",
        "stat": "27/34",
        "stat_label": "European countries grew GDP while territorial CO₂ fell",
    },
    {
        "num": 3, 
        "slug": "structure", 
        "title": "Structure",
        "scope": "🇪🇺➕", 
        "scope_label": "Europe+",
        "tagline": "Do genuine decouplers build cities differently? I tested it "
                   "rigorously - and the real driver is city size, not honesty.",
        "stat": "size",
        "stat_label": "not honesty, is what actually predicts a European city's car dependency",
    },
    {
        "num": 4, 
        "slug": "synthesis", 
        "title": "Synthesis",
        "scope": "🇪🇺➕", 
        "scope_label": "Europe+",
        "tagline": "The Transition Performance Index: an honesty-weighted ranking of "
                   "who is actually transitioning - with the caveats built in.",
        "stat": "40%",
        "stat_label": "of the score is weighted on honesty — so offshoring emissions can't buy a good grade",
        "conclusion": ("Even Europe's leaders are cutting at roughly <span class=\"hot\">half</span> "
                       "the pace a fair share by 2050 demands. Relative virtue is <em>not</em> sufficiency."),
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
_SEC_CAVEATS = "Two honest caveats - good enough?"


_CHAPTER_INTRO = {
    "context": (
        "Most of humanity live in cities nowadays. Sometimes it seems like urbanization is the root of the planet's "
        "pollution problem. Data don't suggest it and points to the real source."
    ),
    "decoupling": (
        "On paper, Europe's climate policy looks impressive and quite optimistic: 27 out of 34 countries "
        "have reduced their carbon dioxide consumption while their economies continued to grow. In this "
        "chapter, I'll examine this claim - first by giving it credit, and then by testing whether it holds "
        "up to an honest look at what these countries actually consume."
    ),
    "structure": (
        "Chapter 2 sorted Europe into genuine cutters and address-changers. The tempting next step "
        "is to check whether that honesty shows up in how their cities are built - fewer cars, less "
        "sprawl. This chapter runs that test, and reports what it found even though the answer is no."
    ),
    "synthesis": (
        "Everything so far converges here. The Transition Performance Index rolls decoupling honesty, "
        "absolute footprint, grid cleanliness, prosperity and pace into a single criterion-referenced "
        "score - weighted 40% on honesty, so that offshoring emissions can't buy a good grade. But an "
        "index is only as trustworthy as its caveats, so the chapter ends by turning the ranking on itself."
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
            "quite clean by buying its goods from someone else."
            "Let's take a look at what the combination of consumption and territorial CO₂ gives us."
        ),
    },
    "structure": {
        _SEC_HYPOTHESIS: (
            "If genuinely decoupling countries build differently, their cities should lean less on "
            "cars. Here is the median for each country, colored according to the decoupling verdict."
        ),
        _SEC_TEST: (
            "As a verdict, compare every city's car dependency side by side. If the hypothesis were correct - "
            "the genuine block would be located clearly below all the others, without overlapping them."
        ),
        _SEC_SIZE: (
            "Car dependency is tracked by size, not by decoupling level. The bigger the city, the fewer cars per person."
        ),
    },
    "synthesis": {
        _SEC_RANK: (
            "The headline ranking drops three countries whose numbers are distorted (Ireland's "
            "profit-shifted GDP, Luxembourg's cross-border workforce, tiny Malta) and marks boundary "
            "cases with an asterisk. Toggle the base year and watch how much of the post-Soviet lead "
            "evaporates once the clock starts in 2000 instead of 1990."
        ),
        _SEC_ANATOMY: (
            "No two leaders climb the same way. Each top-15 score is broken into the weighted points "
            "every component contributes - honesty is the tall green base, the rest stacks on top."
        ),
        _SEC_CAVEATS: (
            "A high rank means 'transitioning well relative to Europe', not 'done'. Two final checks "
            "keep the index honest: where each country actually sits today, and whether even the "
            "leaders are cutting fast enough to matter."
        ),
    },
}


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
            "Most of Europe is far below its all-time emissions peak, but for the post-Soviet economies"
            "the peak was in 1985-89, which can be explained as a industrial collapse rather than a deliberate policy.",
            ch.build_emissions_peak(ds.get_emissions_peak()), 
            section=FLAT
        ),
        _chart_block(
            "decade-change", 
            "The trajectory, decade by decade", 
            EU,
            "Green colour = CO₂/capita fell that decade. Eastern Europe demonstrate a dramatic drop in the 1990s. "
            "Western Europe's sustainable progress shows up in 2010s - the result of a deep review of environmental policy",
            ch.build_decade_change(ds.get_decade_change()), 
            section=FLAT
        ),
        _toggle_block(
            "decoupling-index",
            "Economy growth up, emissions down? Decoupling elasticity map",
            EU,
            "The Tapio decoupling model, developed by Petri Tapio, measures the elasticity between economic growth "
            "(GDP) and environmental impact (CO₂ emissions). Bottom-right = GDP grew while territorial CO₂ fell - "
            "that's decoupling. Try to toggle the base year: a 1990 base flatters the post-Soviet economies, 2000 gives the fairer view.",
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
            "The synthesis: each country placed by how deeply territorial CO₂ emissions fell, coloured by whether the "
            "consumption side have the same intention. Countries in red zone only moved the address of emissions, not their footprint.",
            ch.build_decoupler_board(ds.get_decoupler_class()), 
            section=VERDICT
            ),
    ]


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


def _structure_blocks():
    """Chapter 3 - the null result: honesty doesn't shape cities; city size does."""
    ds, ch = data_service, charts
    EU = "🇪🇺 Europe"
    HYPOTHESIS, TEST, SIZE = _SEC_HYPOTHESIS, _SEC_TEST, _SEC_SIZE

    # Decoupling-verdict key for the by-country bars — only the verdicts that appear,
    # in canonical order (mirrors charts._VERDICT_ORDER/_LABEL/_COLORS).
    city_cars = ds.get_city_cars_by_country()
    _verdict_key = [("genuine", "Genuine", "#14532d"), ("net_exporter", "Net exporter", "#d59a4a"),
                    ("no_decoupling", "No decoupling", "#a89e8a"), ("fake", "Fake", "#c2603f"),
                    ("degrowth", "Degrowth", "#8a6d9c")]
    present = set(city_cars["verdict"])
    car_verdict_legend = [{"color": c, "label": lbl}
                          for key, lbl, c in _verdict_key if key in present]
    return [
        _chart_block(
            "median-city-cars-by-country",
            "Do honest countries have less car-dependent cities?",
            EU,
            "Each bar is a country's median cars per 1000 people, coloured by its decoupling "
            "verdict. As we can see, the specifics of the country affect much more than decoupling level.",
            ch.build_city_cars_by_country(city_cars),
            section=HYPOTHESIS,
            legend=car_verdict_legend,
        ),
        _chart_block(
            "cars-distr-by-verdict",
            "The rigorous test: cars by verdict",
            EU,
            "Divide each city by its country's verdict and the distributions overlap almost "
            "entirely - genuine's median is even slightly higher, not lower than the fake one.",
            ch.build_cars_dist_by_verdict(ds.get_city_cars_snapshot()),
            section=TEST,
        ),
        _chart_block(
            "cars-by-size-band",
            "Does car dependency fall when city size is changing?",
            EU,
            "Bucketed by population, median number of cars per 1000 people falls monotonically as cities grow."
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

    # Decoupling-verdict key (mirrors charts._TPI_VERDICT_COLORS). Square swatches for the
    # bar chart, round for the two scatter charts, so each key matches its marks.
    _verdicts = [("Genuine", "#14532d"), ("Fake", "#c2603f"),
                 ("Special", "#d59a4a"), ("Other", "#a89e8a")]
    verdict_bars = [{"color": c, "label": l} for l, c in _verdicts]
    verdict_dots = [{"color": c, "label": l, "round": True} for l, c in _verdicts]
    return [
        _toggle_block(
            "tpi-leaderboard",
            "The honest ranking: leaders by Transition Performance Index",
            EU,
            "Sweden and Finland (genuine) top the list; Portugal is the quiet surprise. The clay bars "
            "matter most - the UK, Denmark and France score well on grid, prosperity and pace, but are "
            "flagged fake decouplers, so honesty pulls them down the board.",
            ch.build_tpi_score(tpi_2000),
            ch.build_tpi_score(tpi_1990),
            section=RANK,
            legend=verdict_bars,
        ),
        _chart_block(
            "rank-shift",
            "How much of the lead is a post-Soviet windfall?",
            EU,
            "Lines sloping down to the right lost rank when the base year moves from 1990 to 2000 - "
            "their advantage was built on the early-1990s industrial collapse, not recent policy. "
            "Portugal climbs against the tide; several Eastern economies fall.",
            ch.build_rank_shift(tpi_2000, tpi_1990),
            section=RANK,
            legend=verdict_dots,
        ),
        _chart_block(
            "tpi-weighted-contributions",
            "What drives each score? Weighted contributions (2000 base, top 15)",
            EU,
            "Honesty - the 0.40-weighted green base - is what separates the leaders. Countries with "
            "similar totals often get there through different mixes: a clean grid here, high prosperity "
            "there, a strong recent trend somewhere else.",
            ch.build_tpi_weighted_contribution(tpi_2000),
            section=ANATOMY,
            # Stacked-segment key - mirrors charts._TPI_COMPONENT_COLORS + the segment labels.
            legend=[
                {"color": "#14532d", "label": "Honesty (consumption cut − fake-decoupling penalty)"},
                {"color": "#3f7f88", "label": "Territorial CO₂/capita cut"},
                {"color": "#9c6f84", "label": "Consumption CO₂/capita"},
                {"color": "#d59a4a", "label": "Grid cleanliness"},
                {"color": "#7f8a72", "label": "GDP per capita"},
                {"color": "#cbbfa6", "label": "Momentum (recent trend, ±3)"},
            ],
        ),
        _chart_block(
            "tpi-journey",
            "Journey vs destination: a good score is not a clean footprint",
            EU,
            "Every country still sits far from the 2 t/capita fair-share line (top). A high TPI marks "
            "the countries transitioning best relative to Europe - the fastest movers, not the ones "
            "that have already arrived.",
            ch.build_tpi_journey(tpi_2000),
            section=CAVEATS,
            legend=verdict_dots,
        ),
        _chart_block(
            "tpi-sufficiency",
            "Sufficiency: are even the leaders fast enough?",
            EU,
            "The punchline of the whole project. For the top-15, the pace actually achieved since 2010 "
            "(slate) falls short of the pace required to reach 2 t/capita by 2050 (red) almost "
            "everywhere. Relative virtue is not sufficiency.",
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
    if slug == "decoupling":
        return _decoupling_blocks()
    if slug == "context":
        return _context_blocks()
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
    blocks = _charts_for(slug)
    template = 'chapter.html' if blocks else 'chapter_stub.html'
    return render_template(template, chapter=ch, charts=blocks,
                           chapter_intro=_CHAPTER_INTRO.get(slug),
                           section_intros=_SECTION_INTRO.get(slug, {}))

@main.route('/.well-known/appspecific/com.chrome.devtools.json')
def _chrome_devtools_probe():
    return ('', 204)
