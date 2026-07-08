// render the page's Plotly figures + editorial behaviours.
//
// Each figure is emitted server-side by app/charts.py as fig.to_json() into a
// <script type="application/json" id="fig-ID"> and rendered into
// <div class="chart js-plot" data-plot="fig-ID">.

(function () {
  "use strict";

  var PLOT_CFG = { responsive: true, displayModeBar: false };

  // Dark-panel palette (mirrors --panel-dark* in style.css)
  var DARK_INK = "#e8e2d2";
  var DARK_MUTED = "#b8c7bd";
  var DARK_GRID = "rgba(255,255,255,.12)";
  var DARK_LINE = "rgba(255,255,255,.22)";
  var MUTED_HEX = "#857c6c";    
  var MUTED_ON_DARK = "#9db3a5";
  var INK_HEX = "#26231d";

  function readFig(id) {
    var src = document.getElementById(id);
    if (!src) return null;
    try { return JSON.parse(src.textContent); } catch (e) { return null; }
  }

  function applyDark(fig) {
    var lay = fig.layout = fig.layout || {};
    lay.paper_bgcolor = "rgba(0,0,0,0)";
    lay.plot_bgcolor = "rgba(0,0,0,0)";
    lay.font = Object.assign({}, lay.font, { color: DARK_INK });
    if (lay.legend) lay.legend.font = Object.assign({}, lay.legend.font, { color: DARK_INK });
    ["xaxis", "yaxis", "xaxis2", "yaxis2"].forEach(function (k) {
      if (!lay[k]) return;
      lay[k].color = DARK_INK;
      lay[k].gridcolor = DARK_GRID;
      lay[k].linecolor = DARK_LINE;
      lay[k].zerolinecolor = DARK_LINE;
      if (lay[k].title) lay[k].title.font = Object.assign({}, lay[k].title.font, { color: DARK_MUTED });
    });
    (fig.data || []).forEach(function (t) {
      if (t.marker && t.marker.color === MUTED_HEX) t.marker.color = MUTED_ON_DARK;
      if (t.line && t.line.color === MUTED_HEX) t.line.color = MUTED_ON_DARK;
    });
    // Lift dark-ink annotations (e.g. the verdict board's country labels) so they
    // stay legible on the panel; leave intentionally-coloured ones (green/clay) alone.
    (lay.annotations || []).forEach(function (a) {
      if (a.font && a.font.color === INK_HEX) a.font = Object.assign({}, a.font, { color: DARK_INK });
    });
    return fig;
  }

  function wireToggle(gd) {
    var block = gd.closest(".chart-block") || document;
    var toggle = block.querySelector(".base-toggle");
    if (!toggle) return;
    var figs = {}; // data-base value -> figure
    var btns = Array.prototype.slice.call(toggle.querySelectorAll(".base-toggle-btn"));
    // First button = the already-rendered base figure; others map to alt ids.
    btns.forEach(function (b) {
      var id = b.getAttribute("data-fig");
      if (id) figs[b.getAttribute("data-base")] = readFig(id);
    });
    var dark = !!gd.closest(".chart-block--dark");
    btns.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var fig = figs[btn.getAttribute("data-base")];
        if (!fig) return;
        btns.forEach(function (b) { b.classList.toggle("is-active", b === btn); });
        if (dark) applyDark(fig);
        // react (not animate) so the base64 numeric arrays are decoded and the bars render.
        window.Plotly.react(gd, fig.data, fig.layout, PLOT_CFG);
      });
    });
  }

  // ---- Render one plot ----
  function render(gd) {
    var fig = readFig(gd.getAttribute("data-plot"));
    if (!fig) return;
    // Pin the container to the figure's height. .chart carries only a CSS min-height, so
    // when the window is resized Plotly's responsive handler sizes the plot to the
    // container and the container collapses to that min-height - leaving the fixed-height
    // SVG overflowing the card (points spill over the takeaway text). An explicit height
    // gives the responsive resize a stable target so the card always contains the chart.
    if (fig.layout && fig.layout.height) gd.style.height = fig.layout.height + "px";
    if (gd.closest(".chart-block--dark")) applyDark(fig);
    window.Plotly.newPlot(gd, fig.data, fig.layout, PLOT_CFG);

    // Toggle, if this chart declares an alternate figure.
    if (gd.getAttribute("data-plot-alt")) wireToggle(gd);
  }

  function run() {
    if (!window.Plotly) { setTimeout(run, 50); return; }
    document.querySelectorAll(".js-plot[data-plot]").forEach(render);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", run);
  else run();
})();
