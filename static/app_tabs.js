(function () {
  const panels = Array.from(document.querySelectorAll("[data-tab-panel]"));
  const tabs = Array.from(document.querySelectorAll("[data-tab-target]"));
  const shell = document.querySelector("[data-initial-tab]");

  if (!panels.length || !tabs.length) {
    return;
  }

  const targetMap = {
    "#todoSection": "schedule",
    "#scheduleListSection": "schedule",
    "#googleCalendarSection": "schedule",
    "#recordingSection": "talk",
    "#businessCardSection": "talk",
    "#moneySection": "money",
    "#settingsSection": "settings",
    "#aiExtensionSection": "settings",
    "#writerSection": "settings",
  };

  function openPanel(tabName) {
    panels.forEach((panel) => {
      const isActive = panel.dataset.tabPanel === tabName;
      panel.classList.toggle("is-active", isActive);
      panel.hidden = !isActive;
    });

    tabs.forEach((tab) => {
      const isActive = tab.dataset.tabTarget === tabName;
      tab.classList.toggle("is-active", isActive);
      if (isActive) {
        tab.setAttribute("aria-current", "page");
      } else {
        tab.removeAttribute("aria-current");
      }
    });
  }

  function openContainingDetails(selector) {
    const target = document.querySelector(selector);
    const details = target ? target.closest("details") : null;
    if (details) {
      details.open = true;
    }
  }

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      openPanel(tab.dataset.tabTarget);
    });
  });

  document.addEventListener("click", (event) => {
    const link = event.target.closest('a[href^="#"]');
    if (!link) {
      return;
    }

    const selector = link.getAttribute("href");
    const tabName = link.dataset.openTab || targetMap[selector];
    if (!tabName) {
      return;
    }

    event.preventDefault();
    openPanel(tabName);
    openContainingDetails(selector);
  });

  const initialTab = shell ? shell.dataset.initialTab : "home";
  openPanel(initialTab || "home");
})();
