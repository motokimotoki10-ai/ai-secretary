(() => {
  const legacyButton = document.getElementById("fortuneMonthButton");
  const legacyList = document.getElementById("fortuneMonthList");
  const toggles = Array.from(document.querySelectorAll("[data-fortune-toggle]"));

  if (legacyButton && legacyList && !toggles.includes(legacyButton)) {
    legacyButton.dataset.fortuneToggle = "true";
    legacyButton.dataset.openLabel = "今月の運気一覧";
    legacyButton.dataset.closeLabel = "今月の運気一覧を閉じる";
    legacyList.dataset.fortuneList = "true";
    toggles.push(legacyButton);
  }

  toggles.forEach((button) => {
    const list =
      button.nextElementSibling && button.nextElementSibling.matches("[data-fortune-list]")
        ? button.nextElementSibling
        : document.querySelector("[data-fortune-list]");

    if (!list) {
      return;
    }

    const openLabel = button.dataset.openLabel || button.textContent || "一覧を見る";
    const closeLabel = button.dataset.closeLabel || "一覧を閉じる";

    button.addEventListener("click", () => {
      list.hidden = !list.hidden;
      button.textContent = list.hidden ? openLabel : closeLabel;
    });
  });
})();
