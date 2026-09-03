/* LifeTrace front-end helpers: Plotly chart rendering + small UI utilities. */

window.LifeTrace = (function () {
  var PLOTLY_CONFIG = { displayModeBar: false, responsive: true };

  function renderCharts() {
    var charts = window.__CHARTS__ || {};
    Object.keys(charts).forEach(function (key) {
      var el = document.getElementById("chart-" + key);
      if (!el) return;
      var data = charts[key];
      if (typeof data === "string") {
        try { data = JSON.parse(data); } catch (e) { return; }
      }
      if (window.Plotly) {
        Plotly.react(el, data.data || [], data.layout || {}, PLOTLY_CONFIG);
      }
    });
  }

  function renderChart(id, spec) {
    var el = document.getElementById(id);
    if (!el || !window.Plotly) return;
    Plotly.react(el, spec.data || [], spec.layout || {}, PLOTLY_CONFIG);
  }

  function toast(message) {
    var t = document.getElementById("toast");
    if (!t) {
      t = document.createElement("div");
      t.id = "toast";
      t.className = "toast";
      document.body.appendChild(t);
    }
    t.textContent = message;
    t.classList.add("show");
    clearTimeout(t._timer);
    t._timer = setTimeout(function () { t.classList.remove("show"); }, 2600);
  }

  function ready(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }

  ready(renderCharts);

  return { renderCharts: renderCharts, renderChart: renderChart, toast: toast };
})();
