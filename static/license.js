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

  const unlock = () => {
    gate.hidden = true;
    document.body.classList.remove("is-locked");
  };

  const lock = () => {
    gate.hidden = false;
    document.body.classList.add("is-locked");
    input.focus();
  };

  if (localStorage.getItem(APPROVED_KEY) === "true") {
    unlock();
    return;
  }

  lock();

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const licenseKey = input.value.trim();

    if (!licenseKey) {
      message.textContent = "利用キーを入力してください。";
      return;
    }

    message.textContent = "利用キーを確認中です。";

    try {
      const response = await fetch("/license/verify", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ license_key: licenseKey })
      });
      const result = await response.json();

      if (response.ok && result.ok) {
        localStorage.setItem(APPROVED_KEY, "true");
        localStorage.setItem(SAVED_LICENSE_KEY, licenseKey);
        message.textContent = "利用できます。";
        unlock();
        return;
      }

      localStorage.removeItem(APPROVED_KEY);
      localStorage.removeItem(SAVED_LICENSE_KEY);
      message.textContent = result.message || "利用キーが正しくありません";
    } catch (error) {
      message.textContent = "利用キーを確認できませんでした。";
    }
  });
})();
