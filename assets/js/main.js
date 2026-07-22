/* SEIZURE site behavior: theme toggle, mobile nav, publication filter. Vanilla, no dependencies. */
(function () {
  "use strict";

  function initTheme() {
    var btn = document.querySelector(".theme-toggle");
    if (!btn) return;
    var root = document.documentElement;
    function current() {
      return root.getAttribute("data-theme") ||
        (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    }
    function sync() { btn.setAttribute("aria-pressed", current() === "dark" ? "true" : "false"); }
    sync();
    btn.addEventListener("click", function () {
      var next = current() === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("theme", next); } catch (e) {}
      sync();
    });
  }

  function initNav() {
    var toggle = document.querySelector(".nav-toggle");
    var nav = document.getElementById("site-nav");
    if (!toggle || !nav) return;
    function close() {
      nav.setAttribute("data-open", "false");
      toggle.setAttribute("aria-expanded", "false");
    }
    toggle.addEventListener("click", function () {
      var open = nav.getAttribute("data-open") === "true";
      nav.setAttribute("data-open", open ? "false" : "true");
      toggle.setAttribute("aria-expanded", open ? "false" : "true");
    });
    nav.addEventListener("click", function (e) { if (e.target.closest("a")) close(); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") close(); });
  }

  function initPubFilter() {
    var bar = document.querySelector(".pub-filter");
    if (!bar) return;
    var buttons = bar.querySelectorAll("button[data-filter]");
    var items = Array.prototype.slice.call(document.querySelectorAll(".pub[data-type]"));
    var groups = Array.prototype.slice.call(document.querySelectorAll(".year-group"));
    function apply(type) {
      items.forEach(function (el) {
        el.hidden = !(type === "all" || el.getAttribute("data-type") === type);
      });
      // hide a year group when all of its items are hidden
      groups.forEach(function (g) {
        var any = g.querySelector(".pub:not([hidden])");
        g.hidden = !any;
      });
      buttons.forEach(function (b) {
        b.setAttribute("aria-pressed", b.getAttribute("data-filter") === type ? "true" : "false");
      });
    }
    bar.addEventListener("click", function (e) {
      var b = e.target.closest("button[data-filter]");
      if (b) apply(b.getAttribute("data-filter"));
    });
  }

  function ready(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }
  ready(function () { initTheme(); initNav(); initPubFilter(); });
})();
