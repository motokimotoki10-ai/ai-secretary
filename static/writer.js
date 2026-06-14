(() => {
  const kindInput = document.getElementById("writerKindInput");
  const recipientInput = document.getElementById("writerRecipientInput");
  const contentInput = document.getElementById("writerContentInput");
  const generateButton = document.getElementById("writerGenerateButton");
  const suggestButton = document.getElementById("writerSuggestButton");
  const suggestionsBox = document.getElementById("writerSuggestions");
  const suggestionList = document.getElementById("writerSuggestionList");
  const copyButton = document.getElementById("writerCopyButton");
  const resultText = document.getElementById("writerResultText");
  const status = document.getElementById("writerStatus");

  if (
    !kindInput ||
    !recipientInput ||
    !contentInput ||
    !generateButton ||
    !suggestButton ||
    !suggestionsBox ||
    !suggestionList ||
    !copyButton ||
    !resultText ||
    !status
  ) {
    return;
  }

  const generateWriterText = async () => {
    generateButton.disabled = true;
    status.textContent = "文章を生成中です。";

    try {
      const response = await fetch("/writer/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          kind: kindInput.value,
          recipient: recipientInput.value,
          content: contentInput.value
        })
      });
      const result = await response.json();

      if (response.ok && result.ok) {
        resultText.textContent = result.text || "";
        copyButton.disabled = !resultText.textContent.trim();
        status.textContent = "生成しました。";
      } else {
        status.textContent = result.message || "生成できませんでした。";
      }
    } catch (error) {
      status.textContent = "生成できませんでした。";
    } finally {
      generateButton.disabled = false;
    }
  };

  const applySuggestion = async (suggestion) => {
    kindInput.value = suggestion.kind || "自由入力";
    recipientInput.value = suggestion.recipient || "";
    contentInput.value = suggestion.content || "";
    status.textContent = `「${suggestion.title}」を反映しました。`;
    await generateWriterText();
  };

  const renderSuggestions = (suggestions) => {
    suggestionList.textContent = "";
    suggestionsBox.hidden = false;

    if (!suggestions.length) {
      const empty = document.createElement("p");
      empty.className = "writer-suggestion-empty";
      empty.textContent = "おすすめ文章はまだありません。";
      suggestionList.appendChild(empty);
      return;
    }

    suggestions.forEach((suggestion) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "writer-suggestion-button";
      button.textContent = suggestion.title || "文章候補";
      button.addEventListener("click", () => applySuggestion(suggestion));
      suggestionList.appendChild(button);
    });
  };

  generateButton.addEventListener("click", generateWriterText);

  suggestButton.addEventListener("click", async () => {
    suggestButton.disabled = true;
    status.textContent = "保存済みデータから文章候補を探しています。";

    try {
      const response = await fetch("/writer/suggestions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({})
      });
      const result = await response.json();

      if (response.ok && result.ok) {
        renderSuggestions(result.suggestions || []);
        status.textContent = `おすすめ文章を${(result.suggestions || []).length}件表示しました。`;
      } else {
        status.textContent = result.message || "文章候補を作れませんでした。";
      }
    } catch (error) {
      status.textContent = "文章候補を作れませんでした。";
    } finally {
      suggestButton.disabled = false;
    }
  });

  copyButton.addEventListener("click", async () => {
    const text = resultText.textContent.trim();
    if (!text) {
      status.textContent = "コピーする文章がありません。";
      return;
    }

    try {
      await navigator.clipboard.writeText(text);
      status.textContent = "コピーしました。";
    } catch (error) {
      status.textContent = "コピーできませんでした。文章を選択してコピーしてください。";
    }
  });
})();
