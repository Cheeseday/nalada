// Render every Plotly figure embedded on the page. Each chart div carries
// data-plot="<id>" pointing at a <script type="application/json"> holding the
// serialized figure (fig.to_json() from app/charts.py).
(function () {
  document.querySelectorAll(".js-plot[data-plot]").forEach(function (el) {
    var src = document.getElementById(el.getAttribute("data-plot"));
    if (!src) return;
    var fig = JSON.parse(src.textContent);
    Plotly.newPlot(el, fig.data, fig.layout, {
      responsive: true,
      displayModeBar: false,
    });
  });
})();
