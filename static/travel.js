(() => {
  const originInput = document.getElementById("travelOriginInput");
  const destinationInput = document.getElementById("travelDestinationInput");
  const searchButton = document.getElementById("travelSearchButton");
  const status = document.getElementById("travelStatus");
  const result = document.getElementById("travelResult");
  const routeTitle = document.getElementById("travelRouteTitle");
  const distanceText = document.getElementById("travelDistanceText");
  const optionList = document.getElementById("travelOptionList");
  const recommendLabel = document.getElementById("travelRecommendLabel");
  const recommendReason = document.getElementById("travelRecommendReason");

  if (
    !originInput ||
    !destinationInput ||
    !searchButton ||
    !status ||
    !result ||
    !routeTitle ||
    !distanceText ||
    !optionList ||
    !recommendLabel ||
    !recommendReason
  ) {
    return;
  }

  const escapeHtml = (value) =>
    String(value || "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");

  const renderTravel = (travel) => {
    routeTitle.textContent = `${travel.origin} → ${travel.destination}`;
    distanceText.textContent = `距離目安：${travel.distance}`;
    optionList.innerHTML = (travel.options || [])
      .map(
        (option) => `
          <article class="travel-option-card">
            <h3>${escapeHtml(option.icon)} ${escapeHtml(option.label)}</h3>
            <p>所要時間：${escapeHtml(option.time)}</p>
            <p>料金：${escapeHtml(option.fee)}</p>
            <span>${escapeHtml(option.reason_note || "")}</span>
          </article>
        `
      )
      .join("");
    recommendLabel.textContent = travel.recommendation ? travel.recommendation.label : "";
    recommendReason.textContent = travel.recommendation ? travel.recommendation.reason : "";
    result.hidden = false;
  };

  searchButton.addEventListener("click", async () => {
    const origin = originInput.value.trim();
    const destination = destinationInput.value.trim();
    if (!origin || !destination) {
      status.textContent = "出発地と目的地を入力してください。";
      return;
    }

    searchButton.disabled = true;
    status.textContent = "移動候補を確認中です。";

    try {
      const response = await fetch("/travel/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ origin, destination })
      });
      const data = await response.json();

      if (response.ok && data.ok) {
        renderTravel(data.travel);
        status.textContent = "移動候補を表示しました。";
      } else {
        result.hidden = true;
        status.textContent = data.message || "移動候補を表示できませんでした。";
      }
    } catch (error) {
      result.hidden = true;
      status.textContent = "移動候補を表示できませんでした。";
    } finally {
      searchButton.disabled = false;
    }
  });
})();
