(() => {
  const mainButton = document.getElementById("homeVoiceButton");
  const panel = document.getElementById("homeVoicePanel");
  const closeButton = document.getElementById("homeVoiceCloseButton");
  const status = document.getElementById("homeVoiceStatus");
  const listeningBox = document.getElementById("homeVoiceListening");
  const transcriptBox = document.getElementById("homeVoiceTranscript");
  const transcriptText = transcriptBox ? transcriptBox.querySelector("p") : null;
  const fallback = document.getElementById("homeVoiceFallback");
  const textInput = document.getElementById("homeVoiceTextInput");
  const textSubmit = document.getElementById("homeVoiceTextSubmit");
  const retryButton = document.getElementById("homeVoiceRetryButton");
  const homeButton = document.getElementById("homeVoiceHomeButton");
  const resultBox = document.getElementById("homeVoiceResult");

  if (!mainButton || !panel || !closeButton || !status || !resultBox) {
    return;
  }

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const isLocalhost = ["localhost", "127.0.0.1", "::1"].includes(window.location.hostname);
  const canUseDirectRecording =
    (window.isSecureContext || isLocalhost) &&
    navigator.mediaDevices &&
    typeof navigator.mediaDevices.getUserMedia === "function" &&
    window.MediaRecorder;

  const LONG_PRESS_MS = 620;
  const MIN_RECORDING_MS = 800;
  let recognition = null;
  let isListening = false;
  let longPressTimer = 0;
  let pressStartedAt = 0;
  let longPressStarted = false;
  let isRecording = false;
  let mediaRecorder = null;
  let recordStream = null;
  let audioChunks = [];

  const getVoiceUnavailableMessage = () => {
    if (!window.isSecureContext) {
      return "安全な接続ではないため、音声入力が使えない可能性があります。Safariで開き、マイク許可を確認してください。";
    }
    if (!SpeechRecognition) {
      return "このブラウザでは音声入力が使えない可能性があります。Safariで開くか、文字入力を使ってください。";
    }
    return "音声入力が使えません。iPhoneのSafariとマイク許可を確認してください。";
  };

  const getRecordingUnavailableMessage = () => {
    if (!window.isSecureContext && !isLocalhost) {
      return "安全な接続ではないため、この画面では録音できません。Safariで安全なURLから開くか、録音ファイルを選んでください。";
    }
    if (!navigator.mediaDevices || typeof navigator.mediaDevices.getUserMedia !== "function") {
      return "このブラウザでは直接録音が使えません。録音ファイルを選ぶ方法を使ってください。";
    }
    if (!window.MediaRecorder) {
      return "このブラウザでは録音保存機能が使えません。録音ファイルを選ぶ方法を使ってください。";
    }
    return "録音を開始できません。iPhoneのSafariとマイク許可を確認してください。";
  };

  const escapeHtml = (value) =>
    String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");

  const openPanel = () => {
    panel.hidden = false;
    mainButton.setAttribute("aria-expanded", "true");
  };

  const stopActiveRecognition = () => {
    if (recognition && isListening) {
      recognition.abort();
    }
    isListening = false;
    mainButton.classList.remove("is-listening");
  };

  const stopRecordStream = () => {
    if (recordStream) {
      recordStream.getTracks().forEach((track) => track.stop());
      recordStream = null;
    }
  };

  const resetActivity = () => {
    stopActiveRecognition();
    if (mediaRecorder && mediaRecorder.state === "recording") {
      mediaRecorder.stop();
    }
    stopRecordStream();
    isRecording = false;
    mediaRecorder = null;
    audioChunks = [];
    mainButton.classList.remove("is-recording");
    if (listeningBox) {
      listeningBox.hidden = true;
    }
  };

  const closePanel = () => {
    clearTimeout(longPressTimer);
    resetActivity();
    panel.hidden = true;
    mainButton.setAttribute("aria-expanded", "false");
    status.textContent = "マイクを確認しています。";
  };

  const preparePanel = () => {
    openPanel();
    resultBox.innerHTML = "";
    if (transcriptBox) {
      transcriptBox.hidden = true;
    }
    if (fallback) {
      fallback.hidden = true;
    }
  };

  const showFallback = (message) => {
    openPanel();
    status.textContent = message;
    if (listeningBox) {
      listeningBox.hidden = true;
    }
    if (fallback) {
      fallback.hidden = false;
    }
    if (textInput) {
      textInput.focus();
    }
  };

  const showActivity = (title, description) => {
    if (!listeningBox) {
      return;
    }
    const titleNode = listeningBox.querySelector("strong");
    const descriptionNode = listeningBox.querySelector("p");
    if (titleNode) {
      titleNode.textContent = title;
    }
    if (descriptionNode) {
      descriptionNode.textContent = description;
    }
    listeningBox.hidden = false;
  };

  const showTranscript = (text) => {
    if (!transcriptBox || !transcriptText) {
      return;
    }
    transcriptText.textContent = text;
    transcriptBox.hidden = false;
  };

  const renderCandidates = (candidates) => {
    if (!candidates || !candidates.length) {
      resultBox.innerHTML = '<p class="empty">候補を見つけられませんでした。文字で少し詳しく入力してください。</p>';
      return;
    }

    resultBox.innerHTML = candidates
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

  const routeText = async (text) => {
    const cleanText = String(text || "").trim();
    if (!cleanText) {
      showFallback("聞き取れませんでした。文字で入力してください。");
      return;
    }

    openPanel();
    if (listeningBox) {
      listeningBox.hidden = true;
    }
    showTranscript(cleanText);
    status.textContent = "秘書が内容を整理しています。";

    try {
      const response = await fetch("/secretary/route", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ text: cleanText })
      });
      const result = await response.json();

      if (response.ok && result.ok) {
        renderCandidates(result.candidates || []);
        status.textContent = "候補を整理しました。必要なものを選んでください。";
      } else {
        showFallback(result.message || "内容を整理できませんでした。文字で入力してください。");
      }
    } catch (error) {
      showFallback("通信に失敗しました。文字で入力して、もう一度お試しください。");
    }
  };

  const startListening = () => {
    preparePanel();
    status.textContent = "音声入力を開始します。マイク許可が出たら許可してください。";

    if (!SpeechRecognition || !window.isSecureContext) {
      showFallback(`${getVoiceUnavailableMessage()} 文字入力に切り替えました。`);
      return;
    }

    recognition = new SpeechRecognition();
    recognition.lang = "ja-JP";
    recognition.interimResults = false;
    recognition.continuous = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      isListening = true;
      mainButton.classList.add("is-listening");
      showActivity("聞き取り中です", "予定、支出、名刺、やることなどをそのまま話してください。");
      status.textContent = "聞いています。話し終わると秘書が内容を整理します。";
    };

    recognition.onresult = (event) => {
      const text = Array.from(event.results)
        .map((result) => result[0] && result[0].transcript ? result[0].transcript : "")
        .join("")
        .trim();
      routeText(text);
    };

    recognition.onerror = (event) => {
      mainButton.classList.remove("is-listening");
      const message =
        event.error === "not-allowed"
          ? "マイクが許可されていません。iPhoneの設定でSafariのマイクを許可してください。文字入力に切り替えました。"
          : "音声を聞き取れませんでした。文字入力に切り替えました。";
      showFallback(message);
    };

    recognition.onend = () => {
      isListening = false;
      mainButton.classList.remove("is-listening");
      if (listeningBox && !isRecording) {
        listeningBox.hidden = true;
      }
    };

    try {
      recognition.start();
    } catch (error) {
      showFallback("音声入力を開始できませんでした。文字入力に切り替えました。");
    }
  };

  const selectMimeType = () =>
    [
      "audio/mp4",
      "audio/aac",
      "audio/webm;codecs=opus",
      "audio/webm"
    ].find((type) => MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported(type));

  const saveRecordingBlob = async (audioBlob) => {
    const formData = new FormData();
    const extension = audioBlob.type.includes("mp4") || audioBlob.type.includes("aac") ? "m4a" : "webm";
    formData.append("audio", audioBlob, `home_recording.${extension}`);

    const response = await fetch("/recordings", {
      method: "POST",
      body: formData
    });
    const result = await response.json();
    if (!response.ok || !result.ok) {
      throw new Error(result.message || "録音を保存できませんでした。");
    }
    return result.file_name;
  };

  const transcribeSavedRecording = async (fileName) => {
    const response = await fetch("/recordings/transcribe", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ file_name: fileName })
    });
    const result = await response.json();
    if (!response.ok || !result.ok) {
      throw new Error(result.message || "文字起こしできませんでした。");
    }
    return result.text || "";
  };

  const finishHomeRecording = async (audioBlob) => {
    if (!audioBlob || audioBlob.size === 0) {
      showFallback("録音データを作成できませんでした。もう一度長押しするか、文字入力を使ってください。");
      return;
    }

    status.textContent = "録音を保存しています。";
    showActivity("保存中です", "録音した内容を秘書が受け取っています。");

    try {
      const fileName = await saveRecordingBlob(audioBlob);
      status.textContent = "文字起こししています。少しお待ちください。";
      showActivity("文字起こし中です", "録音した内容を文章にしています。");
      const text = await transcribeSavedRecording(fileName);
      await routeText(text);
    } catch (error) {
      showFallback(`${error.message || "録音処理に失敗しました。"} 録音ファイルを選ぶか、文字入力を使ってください。`);
    }
  };

  const startHomeRecording = async () => {
    longPressStarted = true;
    preparePanel();
    stopActiveRecognition();
    status.textContent = "長押し録音を開始します。離すと保存して文字起こしします。";

    if (!canUseDirectRecording) {
      showFallback(getRecordingUnavailableMessage());
      return;
    }

    try {
      recordStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunks = [];
      const mimeType = selectMimeType();
      mediaRecorder = mimeType
        ? new MediaRecorder(recordStream, { mimeType })
        : new MediaRecorder(recordStream);

      mediaRecorder.addEventListener("dataavailable", (event) => {
        if (event.data && event.data.size > 0) {
          audioChunks.push(event.data);
        }
      });

      mediaRecorder.addEventListener("stop", () => {
        const audioBlob = new Blob(audioChunks, { type: mediaRecorder.mimeType || "audio/webm" });
        stopRecordStream();
        isRecording = false;
        mainButton.classList.remove("is-recording");
        finishHomeRecording(audioBlob);
      });

      mediaRecorder.start();
      isRecording = true;
      mainButton.classList.add("is-recording");
      showActivity("長押し録音中です", "話し終わったら指を離してください。保存して文字起こしします。");
      status.textContent = "録音中です。指を離すと秘書が整理します。";
    } catch (error) {
      isRecording = false;
      mainButton.classList.remove("is-recording");
      stopRecordStream();
      const message =
        error && error.name === "NotAllowedError"
          ? "マイクが許可されていません。iPhoneの設定でSafariのマイクを許可してください。"
          : getRecordingUnavailableMessage();
      showFallback(`${message} 録音ファイルを選ぶか、文字入力を使ってください。`);
    }
  };

  const stopHomeRecording = () => {
    if (!isRecording || !mediaRecorder || mediaRecorder.state !== "recording") {
      return;
    }

    const elapsed = Date.now() - pressStartedAt;
    const stopRecorder = () => {
      status.textContent = "録音を停止しました。保存準備をしています。";
      mediaRecorder.stop();
    };

    if (elapsed < MIN_RECORDING_MS) {
      window.setTimeout(stopRecorder, MIN_RECORDING_MS - elapsed);
    } else {
      stopRecorder();
    }
  };

  const beginPress = (event) => {
    if (event && event.pointerType === "mouse" && event.button !== 0) {
      return;
    }
    clearTimeout(longPressTimer);
    pressStartedAt = Date.now();
    longPressStarted = false;
    mainButton.classList.add("is-pressing");
    status.textContent = "短く押すと音声入力、長押しで録音します。";
    longPressTimer = window.setTimeout(() => {
      startHomeRecording();
    }, LONG_PRESS_MS);
  };

  const endPress = (event) => {
    if (event) {
      event.preventDefault();
    }
    clearTimeout(longPressTimer);
    mainButton.classList.remove("is-pressing");

    if (longPressStarted) {
      stopHomeRecording();
      return;
    }

    if (!panel.hidden) {
      closePanel();
      return;
    }
    startListening();
  };

  const cancelPress = () => {
    clearTimeout(longPressTimer);
    mainButton.classList.remove("is-pressing");
    if (longPressStarted) {
      stopHomeRecording();
    }
  };

  mainButton.addEventListener("contextmenu", (event) => event.preventDefault());

  if (window.PointerEvent) {
    mainButton.addEventListener("pointerdown", (event) => {
      mainButton.setPointerCapture(event.pointerId);
      beginPress(event);
    });
    mainButton.addEventListener("pointerup", endPress);
    mainButton.addEventListener("pointercancel", cancelPress);
    mainButton.addEventListener("lostpointercapture", cancelPress);
  } else {
    mainButton.addEventListener("touchstart", beginPress, { passive: true });
    mainButton.addEventListener("touchend", endPress);
    mainButton.addEventListener("touchcancel", cancelPress);
    mainButton.addEventListener("mousedown", beginPress);
    mainButton.addEventListener("mouseup", endPress);
  }

  mainButton.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      startListening();
    }
  });

  closeButton.addEventListener("click", closePanel);

  if (homeButton) {
    homeButton.addEventListener("click", closePanel);
  }

  if (retryButton) {
    retryButton.addEventListener("click", startListening);
  }

  if (textSubmit && textInput) {
    textSubmit.addEventListener("click", () => {
      routeText(textInput.value);
    });
  }
})();
