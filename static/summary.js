(() => {
  const summaryButton = document.getElementById("summaryButton");
  const summaryResult = document.getElementById("summaryResultText");
  const transcriptionResult = document.getElementById("transcriptionResultText");
  const transcriptButtons = Array.from(document.querySelectorAll(".transcript-summary-button"));

  if (!summaryResult && !transcriptButtons.length) {
    return;
  }

  const escapeHtml = (text) =>
    String(text || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");

  const renderItems = (title, items) => {
    const list = Array.isArray(items) && items.length
      ? items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")
      : "<li>候補なし</li>";
    return `<h4>${escapeHtml(title)}</h4><ul>${list}</ul>`;
  };

  const renderSummary = (result) => {
    if (!summaryResult) {
      return;
    }

    summaryResult.innerHTML = [
      `<h4>【要約】</h4><p>${escapeHtml(result.summary || "要約できる内容がありません。")}</p>`,
      renderItems("重要事項", result.important || []),
      renderItems("やること候補", result.todos || []),
      renderItems("予定候補", result.schedules || []),
    ].join("");
  };

  const summarizeText = async (text, button) => {
    const sourceText = String(text || "").trim();
    if (!sourceText || sourceText.includes("録音保存後に文字起こしを実行できます")) {
      if (summaryResult) {
        summaryResult.textContent = "要約する文字起こし結果または会話履歴がありません。";
      }
      return;
    }

    if (button) {
      button.disabled = true;
    }
    if (summaryResult) {
      summaryResult.textContent = "要約中です。";
    }

    try {
      const response = await fetch("/conversation/summarize", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ text: sourceText })
      });
      const result = await response.json();

      if (response.ok && result.ok) {
        renderSummary(result);
        document.querySelector(".summary-result")?.scrollIntoView({ behavior: "smooth", block: "nearest" });
      } else if (summaryResult) {
        summaryResult.textContent = result.message || "要約に失敗しました。";
      }
    } catch (error) {
      if (summaryResult) {
        summaryResult.textContent = "要約に失敗しました。";
      }
    } finally {
      if (button) {
        button.disabled = false;
      }
    }
  };

  if (summaryButton && transcriptionResult) {
    summaryButton.addEventListener("click", () => {
      const sourceText = "value" in transcriptionResult
        ? transcriptionResult.value
        : transcriptionResult.textContent;
      summarizeText(sourceText, summaryButton);
    });
  }

  transcriptButtons.forEach((button) => {
    button.addEventListener("click", () => {
      summarizeText(button.dataset.summaryText || "", button);
    });
  });
})();
