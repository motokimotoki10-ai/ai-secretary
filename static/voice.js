(() => {
  const button = document.getElementById("voiceButton");
  const status = document.getElementById("voiceStatus");
  const memoInput = document.getElementById("source_text");

  if (!button || !status || !memoInput) {
    return;
  }

  const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognition) {
    button.disabled = true;
    status.textContent = "このブラウザは音声入力に対応していません。";
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.lang = "ja-JP";
  recognition.interimResults = true;
  recognition.continuous = false;

  let isListening = false;
  let baseText = "";
  let finalText = "";

  const setListeningState = (listening) => {
    isListening = listening;
    button.disabled = false;
    button.classList.toggle("is-listening", listening);
    button.textContent = listening ? "聞き取り中" : "音声入力";
    status.textContent = listening
      ? "話してください。終わると自動で止まります。"
      : "音声入力できます。";
  };

  const appendTranscript = (text) => {
    const nextText = [baseText, text].filter(Boolean).join(baseText ? "\n" : "");
    memoInput.value = nextText;
    memoInput.dispatchEvent(new Event("input", { bubbles: true }));
  };

  recognition.onstart = () => {
    baseText = memoInput.value.trim();
    finalText = "";
    setListeningState(true);
  };

  recognition.onresult = (event) => {
    let interimText = "";
    for (let index = event.resultIndex; index < event.results.length; index += 1) {
      const transcript = event.results[index][0].transcript.trim();
      if (event.results[index].isFinal) {
        finalText = [finalText, transcript].filter(Boolean).join(" ");
      } else {
        interimText = [interimText, transcript].filter(Boolean).join(" ");
      }
    }
    appendTranscript([finalText, interimText].filter(Boolean).join(" "));
  };

  recognition.onerror = (event) => {
    setListeningState(false);
    status.textContent =
      event.error === "not-allowed"
        ? "マイクの許可が必要です。"
        : "音声入力でエラーが発生しました。";
  };

  recognition.onend = () => {
    setListeningState(false);
    if (!memoInput.value.trim()) {
      status.textContent = "音声入力できます。";
    }
  };

  button.addEventListener("click", () => {
    if (isListening) {
      recognition.stop();
      return;
    }

    try {
      recognition.start();
    } catch (error) {
      setListeningState(false);
      status.textContent = "音声入力を開始できませんでした。";
    }
  });

  setListeningState(false);
})();
