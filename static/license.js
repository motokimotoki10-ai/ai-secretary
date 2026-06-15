(() => {
  const APPROVED_KEY = "aiSecretaryLicenseApproved";
  const SAVED_LICENSE_KEY = "aiSecretaryLicenseKey";

  const gate = document.getElementById("licenseGate");
  const form = document.getElementById("licenseForm");
  const input = document.getElementById("licenseKeyInput");
  const message = document.getElementById("licenseMessage");

  if (!gate || !form || !input || !message) {
    document.body.classList.remove("is-locked");
    return;
  }

  const savedLicenseKey = () => (localStorage.getItem(SAVED_LICENSE_KEY) || "").trim();

  const isLicenseOnlyPage = () =>
    document.body.dataset.page === "license" ||
    window.location.pathname.includes("license");

  const unlock = () => {
    gate.hidden = true;
    document.body.classList.remove("is-locked");
  };

  const lock = () => {
    gate.hidden = false;
    document.body.classList.add("is-locked");
    window.setTimeout(() => input.focus(), 80);
  };

  const clearSavedLicense = () => {
    localStorage.removeItem(APPROVED_KEY);
    localStorage.removeItem(SAVED_LICENSE_KEY);
  };

  const saveLicense = (licenseKey) => {
    localStorage.setItem(APPROVED_KEY, "true");
    localStorage.setItem(SAVED_LICENSE_KEY, licenseKey);
  };

  const verifyLicense = async (licenseKey, options = {}) => {
    const { silent = false } = options;

    if (!licenseKey) {
      if (!silent) {
        message.textContent = "利用キーを入力してください。";
      }
      return false;
    }

    if (!silent) {
      message.textContent = "利用キーを確認しています。";
    }

    try {
      const response = await fetch("/license/verify", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        body: JSON.stringify({ license_key: licenseKey })
      });
      const result = await response.json();

      if (response.ok && result.ok) {
        saveLicense(licenseKey);
        message.textContent = "確認できました。この端末では次回から自動で開きます。";
        unlock();
        if (isLicenseOnlyPage()) {
          window.location.href = "/";
        }
        return true;
      }

      clearSavedLicense();
      if (!silent) {
        message.textContent = result.message || "利用キーが正しくありません。";
      }
      return false;
    } catch (error) {
      if (!silent) {
        message.textContent = "利用キーを確認できませんでした。通信状態を確認してください。";
      }
      return false;
    }
  };

  const checkServerApproval = async () => {
    try {
      const response = await fetch("/license/status", {
        headers: {
          "Accept": "application/json"
        }
      });
      const result = await response.json();
      if (response.ok && result.ok) {
        localStorage.setItem(APPROVED_KEY, "true");
        unlock();
        return true;
      }
    } catch (error) {
      // オフラインや一時的な通信失敗時は、入力画面を表示したままにします。
    }

    localStorage.removeItem(APPROVED_KEY);
    return false;
  };

  const savedKey = savedLicenseKey();
  if (savedKey) {
    input.value = savedKey;
  }

  lock();

  checkServerApproval().then(async (serverApproved) => {
    if (serverApproved) {
      return;
    }

    const key = savedLicenseKey();
    if (key) {
      message.textContent = "保存済みの利用キーを確認しています。";
      const autoApproved = await verifyLicense(key, { silent: true });
      if (!autoApproved) {
        lock();
        message.textContent = "保存済みの利用キーを確認できませんでした。もう一度入力してください。";
      }
    }
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const licenseKey = input.value.trim();
    await verifyLicense(licenseKey);
  });
})();
