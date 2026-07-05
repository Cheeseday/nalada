from flask import Blueprint, render_template, abort, request

from app import charts
from db import data_service

main = Blueprint('main', __name__)

# Single source of truth for the four-chapter arc: drives the nav bar, the landing
# cards, and (later) the chapter routes. Scope badge = which geography the chapter covers.
CHAPTERS = [
    {
        "num": 1, 
        "slug": "context", 
        "title": "Context",
        "scope": "🌍", 
        "scope_label": "Global",
        "tagline": "Urbanization looks like the villain. It's a red herring - "
                   "wealth and energy mix drive emissions, not city living.",
    },
    {
        "num": 2, 
        "slug": "decoupling", 
        "title": "Decoupling",
        "scope": "🇪🇺", 
        "scope_label": "Europe",
        "tagline": "27 of 34 European countries cut CO₂ while their GDP grows. The consumption "
                    "lens reveals who genuinely decoupled and who just offshored their emissions.",
    },
    {
        "num": 3, 
        "slug": "structure", 
        "title": "Structure",
        "scope": "🇪🇺", 
        "scope_label": "Europe",
        "tagline": "Do genuine decouplers build cities differently? We tested it "
                   "rigorously - and the real driver is city size, not honesty.",
    },
    {
        "num": 4, 
        "slug": "synthesis", 
        "title": "Synthesis",
        "scope": "🇪🇺", 
        "scope_label": "Europe",
        "tagline": "The Transition Performance Index: an honesty-weighted ranking of "
                   "who is actually transitioning - with the caveats built in.",
    },
]
CHAPTERS_BY_SLUG = {c["slug"]: c for c in CHAPTERS}


@main.app_context_processor
def inject_chapters():
    """Make the chapter list available to every template (nav bar, footer, etc.)."""
    return {"chapters": CHAPTERS}


@main.route('/')
def index():
    return render_template('index.html')


def _chart_block(block_id, title, scope, takeaway, fig, section=None):
    """Package one figure for the template: id + prose + serialized Plotly JSON."""
    return {"id": block_id, "title": title, "scope": scope, "section": section,
            "takeaway": takeaway, "fig_json": fig.to_json()}


# Chapter 2 narrative scaffolding (section keys are shared by the blocks and their intros)
_SEC_FLAT = "The flattering lens - territorial emissions"
_SEC_HONEST = "The honest test - consumption & trade"
VERDICT = "The verdict"

# Connective tissue: a chapter intro that plants the doubt, a blurb under each section that
# marks the turn, and an outro that hands off to Chapter 4. Keyed by chapter slug.
_CHAPTER_INTRO = {
    "decoupling": (
        "On paper, Europe has already won the hardest argument in climate policy: 27 of 34 "
        "countries cut their CO₂ while their economies kept growing. This chapter takes that "
        "claim apart - first admiring it, then testing whether it survives an honest look at "
        "what these countries actually consume."
    ),
}
_SECTION_INTRO = {
    "decoupling": {
        _SEC_FLAT: (
            "Every figure here counts only the CO₂ emitted inside a country's own borders - "
            "number that governments report."
        ),
        _SEC_HONEST: (
            "Territorial numbers can't see emissions embodied in imports - so a country can look "
            "quite clean by buying its goods from someone else."
            "Let's take a look at what the combination of consumption and territorial CO₂ gives us."
        ),
    },
}


def _decoupling_blocks():
    """Chapter 2 - the ladder: flattering territorial lens -> honest consumption test -> verdict."""
    ds, ch = data_service, charts
    EU = "🇪🇺 Europe"
    FLAT, HONEST = _SEC_FLAT, _SEC_HONEST
    return [
        _chart_block(
            "top-reducers", 
            "Who cut the most? Top 10 European reducers over the last decade", 
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
            "Green = CO₂/capita fell that decade. Eastern Europe's deep cuts land in the "
            "1990s. Western Europe's sustainable progress shows up in 2010s.",
            ch.build_decade_change(ds.get_decade_change()), 
            section=FLAT
        ),
        _chart_block(
            "decoupling-index", 
            "Economy growth up, emissions down? Decoupling elasticity map", 
            EU,
            "The Tapio decoupling model, developed by Petri Tapio, measures the elasticity between economic growth "
            "(GDP) and environmental impact (CO₂ emissions). Bottom-right = GDP grew while territorial CO₂ fell - "
            "that's decoupling. Toggle the base year: a 1990 base flatters the post-Soviet economies, 2000 gives the fairer view.",
            ch.build_decoupling_index(ds.get_decoupling_index(2000), ds.get_decoupling_index(1990)),
            section=FLAT
        ),
        _chart_block(
            "consumption-gap", 
            "What countries consume vs what they emit", 
            EU,
            "Positive gap (red) = a country's footprint is bigger than its territorial number - "
            "emissions imported from elsewhere.",
            ch.build_consumption_gap(ds.get_consumption_gap()), 
            section=HONEST
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
    """Chapter 1. The world context"""
    ds, ch = data_service, charts
    GL = "🌍 Global"
    return [
        _chart_block(
            "urban-by-income", 
            "Urbanization and CO₂ rise together across the world's countries. Case closed?", 
            GL,
            "Let's take a first look: the biggest territorial CO₂/capita cuts of the "
            "last decade.",
            ch.build_urban_by_income(ds.get_co2_urban_by_income()), 
            # section=FLAT
        ),
        _chart_block(
            "density-vs-emissions", 
            "Do dense countries pollute more?", 
            GL,
            "Density doesn't help to predict the emissions level. But wealth does.",
            ch.build_density_vs_emissions(ds.get_density_vs_co2()), 
            # section=FLAT
        ),
    ]



def _charts_for(slug):
    """Ordered chart blocks for a chapter, or [] if it isn't built yet (falls back to the stub)."""
    if slug == "decoupling":
        return _decoupling_blocks()
    if slug == "context":
        return _context_blocks()
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
