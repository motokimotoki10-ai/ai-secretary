(() => {
  document.addEventListener("click", (event) => {
    const button = event.target.closest(".google-calendar-ready-button");
    if (!button) {
      return;
    }

    event.preventDefault();
    const card = button.closest(".schedule-card");
    let message = card ? card.querySelector(".google-calendar-ready-message") : null;
    if (!message && card) {
      message = document.createElement("p");
      message.className = "google-calendar-ready-message";
      message.setAttribute("aria-live", "polite");
      card.insertBefore(message, card.querySelector("form"));
    }
    if (message) {
      message.textContent = "外部予定表連携は準備中です";
    } else {
      alert("外部予定表連携は準備中です");
    }
  });
})();
