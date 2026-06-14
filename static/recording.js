(() => {
  const startButton = document.getElementById("recordStartButton");
  const stopButton = document.getElementById("recordStopButton");
  const saveButton = document.getElementById("recordSaveButton");
  const audioFileInput = document.getElementById("recordAudioFileInput");
  const transcriptionButton = document.getElementById("transcriptionButton");
  const organizeButton = document.getElementById("conversationOrganizeButton");
  const conversationSaveButton = document.getElementById("conversationSaveButton");
  const scheduleSaveButton = document.getElementById("scheduleSaveButton");
  const transcriptionResult = document.getElementById("transcriptionResultText");
  const transcriptionEditSaveButton = document.getElementById("transcriptionEditSaveButton");
  const transcriptionEditStatus = document.getElementById("transcriptionEditStatus");
  const conversationResult = document.getElementById("conversationResultText");
  const conversationSaveStatus = document.getElementById("conversationSaveStatus");
  const scheduleSaveStatus = document.getElementById("scheduleSaveStatus");
  const scheduleList = document.getElementById("scheduleList");
  const status = document.getElementById("recordingStatus");
  const audio = document.getElementById("recordingAudio");
  const supportNotice = document.getElementById("recordingSupportNotice");
  const tapNotice = document.getElementById("recordingTapNotice");
  const audioFileLabel = document.getElementById("recordAudioFileLabel");

  if (
    !startButton ||
    !stopButton ||
    !saveButton ||
    !transcriptionButton ||
    !organizeButton ||
    !conversationSaveButton ||
    !scheduleSaveButton ||
    !transcriptionResult ||
    !transcriptionEditSaveButton ||
    !transcriptionEditStatus ||
    !conversationResult ||
    !conversationSaveStatus ||
    !scheduleSaveStatus ||
    !status ||
    !audio
  ) {
    return;
  }

  let mediaRecorder = null;
  let audioChunks = [];
  let recordedBlob = null;
  let audioUrl = "";
  let savedAudioFileName = "";
  let transcribedText = "";
  let organizedTodos = [];
  let organizedSchedules = [];
  let savedSchedules = [];

  const showSupportNotice = (message) => {
    if (!supportNotice) {
      return;
    }
    supportNotice.textContent = message;
    supportNotice.hidden = false;
  };

  const showTapNotice = (message) => {
    if (!tapNotice) {
      return;
    }
    tapNotice.textContent = message;
    tapNotice.hidden = false;
  };

  const showRecordingFallback = (message) => {
    status.textContent = message;
    showSupportNotice(message);
    showTapNotice("直接録音が使えない場合は、下の「録音ファイルを選ぶ」から音声を保存できます。");
    if (audioFileLabel) {
      audioFileLabel.classList.add("is-recommended");
      audioFileLabel.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  };

  const hideSupportNotice = () => {
    if (!supportNotice) {
      return;
    }
    supportNotice.textContent = "";
    supportNotice.hidden = true;
  };

  const getTranscriptionText = () => transcriptionResult.value.trim();

  const setTranscriptionText = (text) => {
    transcriptionResult.value = text;
  };

  const setSelectedAudioFile = (file) => {
    if (!file) {
      return;
    }

    recordedBlob = file;
    savedAudioFileName = "";
    transcribedText = "";
    organizedTodos = [];
    organizedSchedules = [];
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
    }
    audioUrl = URL.createObjectURL(file);
    audio.src = audioUrl;
    audio.hidden = false;
    saveButton.disabled = false;
    transcriptionButton.disabled = true;
    organizeButton.disabled = true;
    conversationSaveButton.disabled = true;
    scheduleSaveButton.disabled = true;
    transcriptionEditSaveButton.disabled = true;
    setTranscriptionText("録音保存後に文字起こしを実行できます。");
    transcriptionEditStatus.textContent = "";
    conversationResult.textContent = "文字起こし後に会話を整理できます。";
    conversationSaveStatus.textContent = "";
    scheduleSaveStatus.textContent = "";
    status.textContent = "録音ファイルを選択しました。保存できます。";
  };

  if (audioFileInput) {
    audioFileInput.addEventListener("change", () => {
      const file = audioFileInput.files && audioFileInput.files[0];
      setSelectedAudioFile(file);
      if (audioFileLabel) {
        audioFileLabel.classList.remove("is-recommended");
      }
    });
  }

  const isLocalhost = ["localhost", "127.0.0.1", "::1"].includes(window.location.hostname);
  const canUseDirectRecording =
    (window.isSecureContext || isLocalhost) &&
    navigator.mediaDevices &&
    typeof navigator.mediaDevices.getUserMedia === "function" &&
    window.MediaRecorder;

  if (!canUseDirectRecording) {
    startButton.disabled = false;
    stopButton.disabled = true;
    transcriptionButton.disabled = true;
    organizeButton.disabled = true;
    conversationSaveButton.disabled = true;
    scheduleSaveButton.disabled = true;
    const notice = window.isSecureContext || isLocalhost
      ? "このブラウザでは直接録音が使えません。録音ファイルを選ぶと保存できます。"
      : "スマホの安全設定により、この画面では直接録音が使えません。ボイスメモで録音してから、録音ファイルを選んでください。";
    status.textContent = notice;
    showSupportNotice(notice);
    startButton.addEventListener("click", () => {
      showRecordingFallback(notice);
    });
    return;
  }

  hideSupportNotice();

  const escapeHtml = (text) =>
    text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");

  const renderList = (title, items) => {
    const listItems = items.length
      ? items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")
      : "<li>候補なし</li>";
    return `<h4>${title}</h4><ul>${listItems}</ul>`;
  };

  const renderConversationResult = (result) => {
    conversationResult.innerHTML = [
      renderList("【やること候補】", result.todos),
      renderList("【予定候補】", result.schedules),
    ].join("");
  };

  const renderScheduleList = () => {
    if (!scheduleList) {
      savedSchedules = [];
      return;
    }

    const emptyMessage = document.getElementById("scheduleEmptyMessage");
    if (emptyMessage && savedSchedules.length) {
      emptyMessage.remove();
    }

    scheduleList.insertAdjacentHTML(
      "afterbegin",
      savedSchedules
        .map(
          (schedule) => `
            <article class="schedule-card" data-schedule-id="${escapeHtml(String(schedule.id))}">
              <div>
                <strong>${escapeHtml(schedule.title)}</strong>
                <p>${escapeHtml(schedule.scheduled_at)}</p>
              </div>
              <form method="post" action="/schedules/${encodeURIComponent(schedule.id)}/google-calendar" class="google-calendar-register-form">
                <button type="submit" class="google-calendar-register-button">
                  外部予定表へ登録
                </button>
              </form>
              <form method="post" action="/schedules/${encodeURIComponent(schedule.id)}/delete">
                <button type="submit" class="task-action delete-action">削除</button>
              </form>
            </article>
          `
        )
        .join("")
    );
    savedSchedules = [];
  };

  const setRecordingState = (isRecording) => {
    startButton.disabled = isRecording;
    stopButton.disabled = !isRecording;
    status.textContent = isRecording ? "録音中" : "待機中";
  };

  startButton.addEventListener("click", async () => {
    status.textContent = "録音開始を押しました。マイクの許可を確認しています。";
    showTapNotice("反応しています。マイク許可の画面が出た場合は許可してください。");
    hideSupportNotice();
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunks = [];
      recordedBlob = null;
      savedAudioFileName = "";
      transcribedText = "";
      organizedTodos = [];
      organizedSchedules = [];
      saveButton.disabled = true;
      transcriptionButton.disabled = true;
      organizeButton.disabled = true;
      conversationSaveButton.disabled = true;
      scheduleSaveButton.disabled = true;
      transcriptionEditSaveButton.disabled = true;
      setTranscriptionText("録音保存後に文字起こしを実行できます。");
      transcriptionEditStatus.textContent = "";
      conversationResult.textContent = "文字起こし後に会話を整理できます。";
      conversationSaveStatus.textContent = "";
      scheduleSaveStatus.textContent = "";
      const mimeType = [
        "audio/mp4",
        "audio/aac",
        "audio/webm;codecs=opus",
        "audio/webm",
      ].find((type) => MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported(type));
      mediaRecorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);

      mediaRecorder.addEventListener("dataavailable", (event) => {
        if (event.data.size > 0) {
          audioChunks.push(event.data);
        }
      });

      mediaRecorder.addEventListener("stop", () => {
        const audioBlob = new Blob(audioChunks, { type: mediaRecorder.mimeType });
        recordedBlob = audioBlob;
        if (audioUrl) {
          URL.revokeObjectURL(audioUrl);
        }
        audioUrl = URL.createObjectURL(audioBlob);
        audio.src = audioUrl;
        audio.hidden = false;
        saveButton.disabled = false;
        status.textContent = "録音完了";
        stream.getTracks().forEach((track) => track.stop());
      });

      audio.hidden = true;
      audio.removeAttribute("src");
      mediaRecorder.start();
      setRecordingState(true);
      showTapNotice("録音中です。話し終わったら録音停止を押してください。");
    } catch (error) {
      setRecordingState(false);
      if (error && error.name === "NotAllowedError") {
        showRecordingFallback("マイクが許可されていません。ブラウザの設定でマイクを許可するか、録音ファイルを選んでください。");
      } else if (error && error.name === "NotFoundError") {
        showRecordingFallback("マイクが見つかりませんでした。録音ファイルを選ぶ方法を使ってください。");
      } else if (!window.isSecureContext && !isLocalhost) {
        showRecordingFallback("この画面では直接録音が使えません。安全な接続で開くか、録音ファイルを選んでください。");
      } else {
        showRecordingFallback("録音を開始できませんでした。録音ファイルを選ぶ方法も使えます。");
      }
    }
  });

  stopButton.addEventListener("click", () => {
    if (mediaRecorder && mediaRecorder.state === "recording") {
      mediaRecorder.stop();
      setRecordingState(false);
    }
  });

  saveButton.addEventListener("click", async () => {
    if (!recordedBlob) {
      status.textContent = "保存する録音がありません。";
      return;
    }

    const formData = new FormData();
    const extension = recordedBlob.name && recordedBlob.name.includes(".")
      ? recordedBlob.name.split(".").pop()
      : recordedBlob.type.includes("mp4")
        ? "m4a"
        : "webm";
    formData.append("audio", recordedBlob, `recording.${extension}`);
    saveButton.disabled = true;
    status.textContent = "録音を保存中";

    try {
      const response = await fetch("/recordings", {
        method: "POST",
        body: formData,
      });
      const result = await response.json();
      status.textContent = result.message || "録音を保存しました。";
      if (result.ok) {
        savedAudioFileName = result.file_name || "";
        transcriptionButton.disabled = false;
      } else {
        saveButton.disabled = false;
      }
    } catch (error) {
      status.textContent = "録音保存に失敗しました。";
      saveButton.disabled = false;
    }
  });

  transcriptionButton.addEventListener("click", async () => {
    if (!savedAudioFileName) {
      setTranscriptionText("先に録音を保存してください。保存後に会話を文字にするを押してください。");
      return;
    }

    transcriptionButton.disabled = true;
    transcriptionEditSaveButton.disabled = true;
    setTranscriptionText("文字起こし中です。少しお待ちください。");
    transcriptionEditStatus.textContent = "";

    try {
      const response = await fetch("/recordings/transcribe", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ file_name: savedAudioFileName })
      });
      const result = await response.json();

      if (response.ok && result.ok) {
        setTranscriptionText(result.text || "文字起こし結果が空でした。");
        transcribedText = result.text || "";
        organizeButton.disabled = !transcribedText;
        transcriptionEditSaveButton.disabled = !transcribedText;
        transcriptionButton.disabled = false;
      } else {
        setTranscriptionText(result.message || "文字起こしに失敗しました。");
        transcribedText = "";
        organizeButton.disabled = true;
        transcriptionEditSaveButton.disabled = true;
        transcriptionButton.disabled = false;
      }
    } catch (error) {
      setTranscriptionText("文字起こしに失敗しました。");
      transcribedText = "";
      organizeButton.disabled = true;
      transcriptionEditSaveButton.disabled = true;
      transcriptionButton.disabled = false;
    }
  });

  transcriptionResult.addEventListener("input", () => {
    const hasText = Boolean(getTranscriptionText());
    transcriptionEditSaveButton.disabled = !hasText;
    organizeButton.disabled = !hasText;
    transcriptionEditStatus.textContent = hasText ? "修正できます。保存すると整理・要約に反映されます。" : "";
  });

  transcriptionEditSaveButton.addEventListener("click", () => {
    const editedText = getTranscriptionText();
    if (!editedText) {
      transcriptionEditStatus.textContent = "保存する文字起こし結果がありません。";
      organizeButton.disabled = true;
      return;
    }

    transcribedText = editedText;
    organizeButton.disabled = false;
    transcriptionEditStatus.textContent = "修正を保存しました。整理・要約に反映されます。";
  });

  organizeButton.addEventListener("click", async () => {
    transcribedText = getTranscriptionText();
    if (!transcribedText) {
      conversationResult.textContent = "整理する文字起こし結果がありません。";
      return;
    }

    organizeButton.disabled = true;
    conversationResult.textContent = "整理中です。";

    try {
      const response = await fetch("/conversation/organize", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ text: transcribedText })
      });
      const result = await response.json();

      if (response.ok && result.ok) {
        renderConversationResult(result);
        organizedTodos = Array.isArray(result.todos) ? result.todos : [];
        organizedSchedules = Array.isArray(result.schedules) ? result.schedules : [];
        conversationSaveButton.disabled = organizedTodos.length === 0;
        scheduleSaveButton.disabled = organizedSchedules.length === 0;
        conversationSaveStatus.textContent = "";
        scheduleSaveStatus.textContent = "";
      } else {
        conversationResult.textContent = result.message || "整理に失敗しました。";
        organizedTodos = [];
        organizedSchedules = [];
        conversationSaveButton.disabled = true;
        scheduleSaveButton.disabled = true;
      }
    } catch (error) {
      conversationResult.textContent = "整理に失敗しました。";
      organizedTodos = [];
      organizedSchedules = [];
      conversationSaveButton.disabled = true;
      scheduleSaveButton.disabled = true;
    } finally {
      organizeButton.disabled = false;
    }
  });

  conversationSaveButton.addEventListener("click", async () => {
    if (!organizedTodos.length) {
      conversationSaveStatus.textContent = "保存するやること候補がありません。";
      return;
    }

    conversationSaveButton.disabled = true;
    conversationSaveStatus.textContent = "保存中です。";

    try {
      const response = await fetch("/conversation/save-todos", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          todos: organizedTodos,
          source_text: transcribedText
        })
      });
      const result = await response.json();

      if (response.ok && result.ok) {
        conversationSaveStatus.textContent = result.message || "保存しました";
      } else {
        conversationSaveStatus.textContent = result.message || "保存に失敗しました。";
        conversationSaveButton.disabled = false;
      }
    } catch (error) {
      conversationSaveStatus.textContent = "保存に失敗しました。";
      conversationSaveButton.disabled = false;
    }
  });

  scheduleSaveButton.addEventListener("click", async () => {
    if (!organizedSchedules.length) {
      scheduleSaveStatus.textContent = "保存する予定候補がありません。";
      return;
    }

    scheduleSaveButton.disabled = true;
    scheduleSaveStatus.textContent = "予定を保存中です。";

    try {
      const response = await fetch("/conversation/save-schedules", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ schedules: organizedSchedules })
      });
      const result = await response.json();

      if (response.ok && result.ok) {
        savedSchedules = savedSchedules.concat(result.schedules || []);
        renderScheduleList();
        scheduleSaveStatus.textContent = result.message || "予定を保存しました";
      } else {
        scheduleSaveStatus.textContent = result.message || "予定保存に失敗しました。";
        scheduleSaveButton.disabled = false;
      }
    } catch (error) {
      scheduleSaveStatus.textContent = "予定保存に失敗しました。";
      scheduleSaveButton.disabled = false;
    }
  });
})();
