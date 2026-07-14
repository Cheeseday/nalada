"""Figure builders for the dashboard, one builder per data_service getter, split by chapter.

Layering: route = orchestration, charts = figures (this package), data_service = data.
Each builder takes a DataFrame and returns a Plotly go.Figure; the route serializes it
with fig.to_json() and the browser renders it via Plotly.newPlot (see static/js/charts.js).

Shared palette and helpers live in ._theme; the per-chapter modules hold the builders.
Everything is re-exported here so callers can keep using `charts.build_*`.
"""
from ._theme import (
    INK, MUTED, ACCENT, ACCENT_DARK, WARM, GRID, GRID_A, BLACK,
    FONT, BORDER_RADIUS, EU_ON_DARK,
    _VERDICT_ORDER, _VERDICT_LABEL, _VERDICT_COLORS,
)
from .context import (
    build_urban_by_income,
    build_density_vs_emissions,
    build_urban_vs_air_pollution,
    build_gdp_vs_co2,
)
from .decoupling import (
    build_top_reducers,
    build_emissions_peak,
    build_decade_change,
    build_decoupling_index,
    build_consumption_gap,
    build_fake_decoupler_board,
    build_decoupler_board,
)
from .structure import (
    build_city_cars_by_country,
    build_cars_dist_by_verdict,
    build_cars_by_size_band,
)
from .synthesis import (
    build_tpi_score,
    build_rank_shift,
    build_tpi_weighted_contribution,
    build_tpi_journey,
    build_tpi_sufficiency,
    build_tpi_robustness,
)

__all__ = [
    # Chapter 1 - Context
    "build_urban_by_income", 
    "build_density_vs_emissions",
    "build_urban_vs_air_pollution", 
    "build_gdp_vs_co2",
    # Chapter 2 - Decoupling
    "build_top_reducers", 
    "build_emissions_peak", 
    "build_decade_change",
    "build_decoupling_index", 
    "build_consumption_gap",
    "build_fake_decoupler_board", 
    "build_decoupler_board",
    # Chapter 3 - Structure
    "build_city_cars_by_country", 
    "build_cars_dist_by_verdict",
    "build_cars_by_size_band",
    # Chapter 4 - Synthesis
    "build_tpi_score",
    "build_rank_shift",
    "build_tpi_weighted_contribution",
    "build_tpi_journey",
    "build_tpi_sufficiency",
    # Chapter 5 - Methodology
    "build_tpi_robustness",
]
