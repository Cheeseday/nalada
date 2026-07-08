// reveal.js - scroll-reveal for editorial elements.
// Any element with class "reveal" fades + rises in when it enters the viewport.
// Chart draw-in (bars growing from zero) is handled separately in charts.js.
(function () {
  "use strict";

  var reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function run() {
    var els = Array.prototype.slice.call(document.querySelectorAll(".reveal"));
    if (!els.length) return;

    // No IntersectionObserver (or reduced motion)
    if (reduced || !("IntersectionObserver" in window)) {
      els.forEach(function (el) { el.classList.add("is-visible"); });
      return;
    }

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          // Optional stagger via data-reveal-delay="120" (ms)
          var d = e.target.getAttribute("data-reveal-delay");
          if (d) e.target.style.transitionDelay = d + "ms";
          e.target.classList.add("is-visible");
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -8% 0px" });

    els.forEach(function (el) { io.observe(el); });

    // Safety: guarantee visibility even if the observer never fires.
    setTimeout(function () { els.forEach(function (el) { el.classList.add("is-visible"); }); }, 2600);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", run);
  } else {
    run();
  }
})();
