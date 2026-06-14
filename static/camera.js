(() => {
  const input = document.getElementById("cameraInput");
  const preview = document.getElementById("cameraPreview");
  const status = document.getElementById("cameraStatus");

  if (!input || !preview || !status) {
    return;
  }

  input.addEventListener("change", () => {
    const file = input.files && input.files[0];
    if (!file) {
      preview.hidden = true;
      preview.removeAttribute("src");
      status.textContent = "画像はまだ選択されていません。";
      return;
    }

    if (!file.type.startsWith("image/")) {
      preview.hidden = true;
      preview.removeAttribute("src");
      status.textContent = "画像ファイルを選択してください。";
      return;
    }

    const imageUrl = URL.createObjectURL(file);
    preview.src = imageUrl;
    preview.hidden = false;
    status.textContent = "画像を読み込みました。";
  });
})();
