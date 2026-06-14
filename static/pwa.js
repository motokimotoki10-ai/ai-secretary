if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/static/service-worker.js").catch(() => {
      // PWA登録に失敗しても通常利用は継続する。
    });
  });
}

window.addEventListener("load", () => {
  const hint = document.getElementById("pwaInstallHint");
  if (!hint) {
    return;
  }

  const isStandalone =
    window.matchMedia("(display-mode: standalone)").matches ||
    window.navigator.standalone === true;

  if (isStandalone) {
    hint.hidden = true;
  }
});
