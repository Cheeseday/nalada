"""Shared chart theme: palette, the layout helper, and the decoupler-verdict vocabulary.

Layering: route = orchestration, charts = figures, data_service = data. Each builder
takes a DataFrame and returns a Plotly go.Figure; the route serializes it with
fig.to_json() and the browser renders it via Plotly.newPlot (see static/js/charts.js).

The palette is mirrored in app/static/css/style.css so the figures and the page read
as one piece. Warm, calm three-colour system: INK / ACCENT / WARM / GRID mirror
--ink / --accent / --clay / --border.
"""
import plotly.graph_objects as go

INK = "#26231d"
MUTED = "#857c6c"        # charts.js lightens this on the dark panel
ACCENT = "#14532d"       # pine green
ACCENT_DARK = "#1c6b3e"
WARM = "#c2603f"         # warm clay
GRID = "#e7e0d0"         # warm grid
GRID_A = "#cfe8d6"
BLACK = "#1c1a17"
FONT = "system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
BORDER_RADIUS = "14px"

# Light green for the Europe series on the dark finale panel — pine (#14532d) would
# vanish against the #123a24 panel, so the always-dark PM2.5 chart uses this instead.
EU_ON_DARK = "#7fbf8f"


def _apply_theme(fig: go.Figure, **layout) -> go.Figure:
    """Apply the shared Nalada look: transparent background, house font and grid."""
    margin = layout.pop("margin", dict(l=8, r=28, t=8, b=8))
    fig.update_layout(
        font=dict(family=FONT, color=INK, size=13),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=margin,
        colorway=[ACCENT, WARM, MUTED],
        hoverlabel=dict(font_family=FONT, bgcolor="rgba(255,255,255,0.75)", bordercolor=INK),
        barcornerradius=5,
        **layout,
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID)
    return fig


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    """Convert #rrggbb to an rgba() string with the given alpha - for translucent fills."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


# decoupler_class verdicts (NB04) - shared by the Chapter 2 verdict board and the
# Chapter 3 city charts, which colour cities by their country's decoupling verdict.
_VERDICT_ORDER = ["genuine", "net_exporter", "no_decoupling", "fake", "degrowth"]
_VERDICT_LABEL = {
    "genuine": "Genuine", "net_exporter": "Net exporter",
    "no_decoupling": "No decoupling", "fake": "Fake", "degrowth": "Degrowth",
}
_VERDICT_COLORS = {
    "genuine": ACCENT, "net_exporter": "#d59a4a",
    "no_decoupling": "#a89e8a", "fake": WARM, "degrowth": "#8a6d9c",
}
