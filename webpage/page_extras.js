// Extras for the browser version, added to the page that pygbag builds
// (see .github/workflows/web.yml). They are plain JavaScript because the browser
// only allows full screen straight from a real click or key press.
(function () {
  // Smooth scaling: pygbag stretches the canvas with "pixelated" scaling, which makes text jagged.
  // Shape: when the page opens, pygbag can size the canvas before the game has set its window,
  // squeezing the 16:9 picture (narrow letters). Keep it 16:9, as big as fits, centred.
  // (Clicks still land in the right place: the browser maps them through the canvas's real size.)
  const style = document.createElement("style");
  style.textContent = "canvas { image-rendering: auto !important; }\n"
    + "#canvas, canvas.emscripten {"
    + " position: fixed !important; left: 50% !important; top: 50% !important; margin: 0 !important;"
    + " transform: translate(-50%, -50%) !important;"
    + " width: min(100vw, calc(100vh * 16 / 9)) !important;"
    + " height: min(100vh, calc(100vw * 9 / 16)) !important; }";
  document.head.appendChild(style);

  // Full screen button (bottom right) and the F key.
  const button = document.createElement("button");
  button.id = "fullscreen-button";
  button.title = "Full screen (F)";
  button.textContent = "⛶ Full screen";
  button.style.cssText = "position:fixed;right:12px;bottom:12px;z-index:100000;padding:8px 14px;"
    + "font:600 14px Arial,sans-serif;color:#fff;background:rgba(30,41,59,0.85);"
    + "border:1px solid #475569;border-radius:8px;cursor:pointer;";

  function toggle() {
    if (document.fullscreenElement) {
      document.exitFullscreen();
    } else {
      document.documentElement.requestFullscreen().catch(function () {});
    }
  }

  button.addEventListener("click", function (e) { e.stopPropagation(); toggle(); });
  window.addEventListener("keydown", function (e) {
    if ((e.key === "f" || e.key === "F") && !e.ctrlKey && !e.altKey && !e.metaKey) { toggle(); }
  }, true);
  document.addEventListener("fullscreenchange", function () {
    button.style.display = document.fullscreenElement ? "none" : "block";
  });

  function add() { document.body.appendChild(button); }
  if (document.body) { add(); } else { document.addEventListener("DOMContentLoaded", add); }
})();
