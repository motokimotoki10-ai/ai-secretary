(() => {
  const input = document.getElementById("secretaryConsultInput");
  const button = document.getElementById("secretaryConsultButton");
  const status = document.getElementById("secretaryConsultStatus");
  const historyList = document.getElementById("secretaryConsultHistoryList");
  const routeInput = document.getElementById("secretaryRouteInput");
  const routeButton = document.getElementById("secretaryRouteButton");
  const routeStatus = document.getElementById("secretaryRouteStatus");
  const routeResult = document.getElementById("secretaryRouteResult");

  if (!input || !button || !status || !historyList) {
    return;
  }

  let history = [];

  const escapeHtml = (value) =>
    String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");

  const renderHistory = () => {
    if (!history.length) {
      historyList.innerHTML = '<p class="empty">まだ相談履歴はありません。</p>';
      return;
    }

    historyList.innerHTML = history
      .map(
        (item) => `
          <article class="secretary-consult-card">
            <strong>Q. ${escapeHtml(item.question)}</strong>
            <p>${escapeHtml(item.answer).replace(/\n/g, "<br>")}</p>
          </article>
        `
      )
      .join("");
  };

  const renderRouteCandidates = (candidates) => {
    if (!routeResult) {
      return;
    }

    if (!candidates || !candidates.length) {
      routeResult.innerHTML = '<p class="empty">候補を見つけられませんでした。</p>';
      return;
    }

    routeResult.innerHTML = candidates
      .map(
        (candidate) => `
          <article class="secretary-route-card">
            <span>${escapeHtml(candidate.kind)}</span>
            <strong>${escapeHtml(candidate.title)}</strong>
            <p>${escapeHtml(candidate.detail)}</p>
            <a href="${escapeHtml(candidate.url)}">${escapeHtml(candidate.action_label)}</a>
          </article>
        `
      )
      .join("");
  };

  if (routeInput && routeButton && routeStatus && routeResult) {
    routeButton.addEventListener("click", async () => {
      const text = routeInput.value.trim();
      if (!text) {
        routeStatus.textContent = "振り分ける内容を入力してください。";
        return;
      }

      routeButton.disabled = true;
      routeStatus.textContent = "秘書が内容を確認しています。";

      try {
        const response = await fetch("/secretary/route", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ text })
        });
        const result = await response.json();

        if (response.ok && result.ok) {
          renderRouteCandidates(result.candidates || []);
          routeStatus.textContent = result.message || "候補を整理しました。";
        } else {
          routeStatus.textContent = result.message || "振り分けに失敗しました。";
        }
      } catch (error) {
        routeStatus.textContent = "振り分けに失敗しました。";
      } finally {
        routeButton.disabled = false;
      }
    });
  }

  button.addEventListener("click", async () => {
    const question = input.value.trim();
    if (!question) {
      status.textContent = "相談内容を入力してください。";
      return;
    }

    button.disabled = true;
    status.textContent = "秘書が確認中です。";

    try {
      const response = await fetch("/secretary/consult", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ question })
      });
      const result = await response.json();

      if (response.ok && result.ok) {
        history.unshift({
          question,
          answer: result.answer || "回答を作れませんでした。"
        });
        history = history.slice(0, 5);
        renderHistory();
        input.value = "";
        status.textContent = "回答しました。";
      } else {
        status.textContent = result.message || "相談に失敗しました。";
      }
    } catch (error) {
      status.textContent = "相談に失敗しました。";
    } finally {
      button.disabled = false;
    }
  });
})();
