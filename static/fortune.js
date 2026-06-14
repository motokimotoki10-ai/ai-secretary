(() => {
  const button = document.getElementById("fortuneMonthButton");
  const list = document.getElementById("fortuneMonthList");

  if (!button || !list) {
    return;
  }

  button.addEventListener("click", () => {
    list.hidden = !list.hidden;
    button.textContent = list.hidden ? "今月の運気一覧" : "今月の運気一覧を閉じる";
  });
})();
