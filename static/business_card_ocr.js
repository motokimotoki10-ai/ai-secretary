(() => {
  const input = document.getElementById("businessCardInput");
  const preview = document.getElementById("businessCardPreview");
  const button = document.getElementById("businessCardOcrButton");
  const status = document.getElementById("businessCardOcrStatus");
  const ocrResult = document.getElementById("businessCardOcrResult");
  const ocrResultFields = {
    name: document.getElementById("ocrResultName"),
    company: document.getElementById("ocrResultCompany"),
    phone: document.getElementById("ocrResultPhone"),
    email: document.getElementById("ocrResultEmail")
  };
  const saveButton = document.getElementById("businessCardSaveButton");
  const saveStatus = document.getElementById("businessCardSaveStatus");
  const contactList = document.getElementById("contactList");
  const contactSearchInput = document.getElementById("contactSearchInput");
  const contactSearchClearButton = document.getElementById("contactSearchClearButton");
  const contactSearchResultCount = document.getElementById("contactSearchResultCount");
  let contactEmptyMessage = document.getElementById("contactEmptyMessage");
  const fields = {
    name: document.getElementById("contactNameInput"),
    company: document.getElementById("contactCompanyInput"),
    phone: document.getElementById("contactPhoneInput"),
    email: document.getElementById("contactEmailInput")
  };
  let tesseractLoaderPromise = null;

  const escapeHtml = (value) =>
    String(value || "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");

  const normalizeSearchText = (value) => String(value || "").trim().toLowerCase();

  const contactSearchText = (contact) =>
    [contact.name, contact.company, contact.phone, contact.email]
      .map((value) => String(value || ""))
      .join(" ");

  const updateContactSearch = () => {
    if (!contactList || !contactSearchResultCount) {
      return;
    }

    const query = normalizeSearchText(contactSearchInput ? contactSearchInput.value : "");
    const cards = Array.from(contactList.querySelectorAll(".contact-card"));
    let visibleCount = 0;

    cards.forEach((card) => {
      const target = normalizeSearchText(card.dataset.contactSearch || card.textContent);
      const isMatch = !query || target.includes(query);
      card.hidden = !isMatch;
      if (isMatch) {
        visibleCount += 1;
      }
    });

    contactSearchResultCount.textContent = `検索結果：${visibleCount}件`;
  };

  if (contactSearchInput) {
    contactSearchInput.addEventListener("input", updateContactSearch);
  }

  if (contactSearchClearButton && contactSearchInput) {
    contactSearchClearButton.addEventListener("click", () => {
      contactSearchInput.value = "";
      contactSearchInput.focus();
      updateContactSearch();
    });
  }

  if (contactList) {
    contactList.addEventListener("click", (event) => {
      const toggleButton = event.target.closest(".contact-export-toggle");
      if (!toggleButton) {
        return;
      }

      const card = toggleButton.closest(".contact-card");
      const exportBox = card ? card.querySelector(".contact-export-box") : null;
      if (!exportBox) {
        return;
      }

      exportBox.hidden = !exportBox.hidden;
      toggleButton.textContent = exportBox.hidden ? "連絡帳用に表示" : "閉じる";
    });
  }

  const fieldValue = (key) => (fields[key] ? fields[key].value.trim() : "");

  const clearFields = () => {
    Object.values(fields).forEach((field) => {
      if (field) {
        field.value = "";
      }
    });
  };

  const fillContactFields = (contact) => {
    Object.entries(fields).forEach(([key, field]) => {
      if (field) {
        field.value = contact && contact[key] ? contact[key] : "";
      }
    });
  };

  const loadTesseract = () => {
    if (window.Tesseract) {
      return Promise.resolve(window.Tesseract);
    }

    if (!tesseractLoaderPromise) {
      tesseractLoaderPromise = new Promise((resolve, reject) => {
        const script = document.createElement("script");
        script.src = "https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js";
        script.async = true;
        script.onload = () => {
          if (window.Tesseract) {
            resolve(window.Tesseract);
          } else {
            reject(new Error("Tesseract.jsを読み込めませんでした。"));
          }
        };
        script.onerror = () => reject(new Error("Tesseract.jsを読み込めませんでした。"));
        document.head.appendChild(script);
      });
    }

    return tesseractLoaderPromise;
  };

  const parseOcrText = async (text) => {
    const response = await fetch("/business-card/parse", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ text })
    });
    return response.json();
  };

  const recognizeOnDevice = async (file) => {
    status.textContent = "サーバー読み取りが使えないため、この端末で読み取りを試します。少し時間がかかります。";
    const Tesseract = await loadTesseract();
    const result = await Tesseract.recognize(file, "jpn+eng", {
      logger: (progress) => {
        if (progress.status === "recognizing text" && Number.isFinite(progress.progress)) {
          const percent = Math.round(progress.progress * 100);
          status.textContent = `この端末で名刺を読み取り中です。${percent}%`;
        }
      }
    });
    const text = result && result.data ? String(result.data.text || "").trim() : "";
    if (!text) {
      throw new Error("名刺の文字を読み取れませんでした。");
    }
    return parseOcrText(text);
  };

  const renderOcrResult = (contact) => {
    if (!ocrResult) {
      return;
    }

    Object.entries(ocrResultFields).forEach(([key, element]) => {
      if (element) {
        element.textContent = contact && contact[key] ? contact[key] : "";
      }
    });
    ocrResult.hidden = false;
  };

  const renderContact = (contact) => {
    if (!contactList || !contact || !contact.id) {
      return;
    }

    const safeId = String(contact.id).replaceAll('"', '\\"');
    const existingCard = contactList.querySelector(`[data-contact-id="${safeId}"]`);
    if (existingCard) {
      existingCard.remove();
    }

    if (contactEmptyMessage) {
      contactEmptyMessage.remove();
      contactEmptyMessage = null;
    }

    contactList.insertAdjacentHTML(
      "afterbegin",
      `
      <article
        class="contact-card"
        data-contact-id="${escapeHtml(contact.id)}"
        data-contact-search="${escapeHtml(contactSearchText(contact))}"
      >
        <strong>${escapeHtml(contact.name || "名前未設定")}</strong>
        <p>会社：${escapeHtml(contact.company || "未設定")}</p>
        <p>電話：${escapeHtml(contact.phone || "未設定")}</p>
        <p>メール：${escapeHtml(contact.email || "未設定")}</p>
        <p class="contact-date">${contact.updated ? "更新" : "登録"}：${escapeHtml(contact.created_at || "")}</p>
        <div class="contact-export-actions">
          <button type="button" class="contact-export-toggle">連絡帳用に表示</button>
          <a class="contact-vcf-link" href="/contacts/${encodeURIComponent(contact.id)}/vcf" download>
            スマホ連絡帳に追加
          </a>
        </div>
        <div class="contact-export-box" hidden>
          <h3>連絡帳用表示</h3>
          <pre>名前：${escapeHtml(contact.name || "")}
会社：${escapeHtml(contact.company || "")}
電話：${escapeHtml(contact.phone || "")}
メール：${escapeHtml(contact.email || "")}</pre>
        </div>
        <form method="post" action="/contacts/${encodeURIComponent(contact.id)}/delete">
          <button type="submit" class="task-action delete-action">削除</button>
        </form>
      </article>
      `
    );
    updateContactSearch();
  };

  updateContactSearch();

  if (!input || !preview || !button || !status || !saveButton || !saveStatus) {
    return;
  }

  input.addEventListener("change", () => {
    const file = input.files && input.files[0];
    if (!file) {
      preview.hidden = true;
      preview.removeAttribute("src");
      status.textContent = "名刺画像はまだ選択されていません。";
      return;
    }

    if (!file.type.startsWith("image/")) {
      preview.hidden = true;
      preview.removeAttribute("src");
      status.textContent = "画像ファイルを選択してください。";
      return;
    }

    preview.src = URL.createObjectURL(file);
    preview.hidden = false;
    status.textContent = "名刺画像を読み込みました。名刺読み取り、または手入力で保存できます。";
    if (ocrResult) {
      ocrResult.hidden = true;
    }
  });

  button.addEventListener("click", async () => {
    const file = input.files && input.files[0];
    if (!file) {
      status.textContent = "先に名刺画像を選択してください。";
      return;
    }

    if (!file.type.startsWith("image/")) {
      status.textContent = "画像ファイルを選択してください。";
      return;
    }

    const formData = new FormData();
    formData.append("image", file);
    button.disabled = true;
    status.textContent = "名刺を読み取り中です。少しお待ちください。";

    try {
      const response = await fetch("/business-card/ocr", {
        method: "POST",
        body: formData
      });
      const result = await response.json();

      if (response.ok && result.ok) {
        const contact = result.contact || {};
        fillContactFields(contact);
        renderOcrResult(contact);
        status.textContent = result.message || "読み取り結果を連絡先候補へ入力しました。";
      } else {
        const fallbackResult = await recognizeOnDevice(file);
        if (fallbackResult.ok) {
          const contact = fallbackResult.contact || {};
          fillContactFields(contact);
          renderOcrResult(contact);
          status.textContent = "端末側で読み取りました。必要に応じて修正して保存してください。";
        } else {
          status.textContent = fallbackResult.message || result.message || "名刺読み取りに失敗しました。手入力で保存できます。";
        }
      }
    } catch (error) {
      status.textContent = `${error.message || "名刺読み取りに失敗しました。"} 手入力で保存できます。`;
    } finally {
      button.disabled = false;
    }
  });

  saveButton.addEventListener("click", async () => {
    const contact = {
      name: fieldValue("name"),
      company: fieldValue("company"),
      phone: fieldValue("phone"),
      email: fieldValue("email")
    };

    if (!Object.values(contact).some(Boolean)) {
      saveStatus.textContent = "保存する連絡先候補がありません。";
      return;
    }

    saveButton.disabled = true;
    saveStatus.textContent = "保存中です。";

    try {
      const response = await fetch("/contacts", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(contact)
      });
      const result = await response.json();

      if (response.ok && result.ok) {
        saveStatus.textContent = result.message || "連絡先を保存しました。";
        renderContact(result.contact);
        clearFields();
      } else {
        saveStatus.textContent = result.message || "保存に失敗しました。";
      }
    } catch (error) {
      saveStatus.textContent = "保存に失敗しました。";
    } finally {
      saveButton.disabled = false;
    }
  });
})();
