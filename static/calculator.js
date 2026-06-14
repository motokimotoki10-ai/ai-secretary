(() => {
  const input = document.getElementById("voiceCalculatorInput");
  const calculateButton = document.getElementById("voiceCalculatorButton");
  const fromMemoButton = document.getElementById("voiceCalculatorFromMemoButton");
  const resultText = document.getElementById("voiceCalculatorResultText");
  const memoInput = document.getElementById("source_text");

  if (!input || !calculateButton || !fromMemoButton || !resultText) {
    return;
  }

  const calculate = async () => {
    const text = input.value.trim() || (memoInput ? memoInput.value.trim() : "");
    if (!text) {
      resultText.textContent = "計算する内容を入力してください。";
      return;
    }

    calculateButton.disabled = true;
    resultText.textContent = "計算中です。";

    try {
      const response = await fetch("/calculator/calculate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ text })
      });
      const result = await response.json();

      if (response.ok && result.ok) {
        resultText.textContent = result.result || "計算結果がありません。";
      } else {
        resultText.textContent = result.message || "計算できませんでした。";
      }
    } catch (error) {
      resultText.textContent = "計算できませんでした。";
    } finally {
      calculateButton.disabled = false;
    }
  };

  fromMemoButton.addEventListener("click", () => {
    if (!memoInput || !memoInput.value.trim()) {
      resultText.textContent = "メモ入力に計算したい内容がありません。";
      return;
    }
    input.value = memoInput.value.trim();
    input.focus();
  });

  calculateButton.addEventListener("click", calculate);
})();
