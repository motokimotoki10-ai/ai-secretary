(() => {
  const input = document.getElementById("weatherLocationInput");
  const button = document.getElementById("weatherFetchButton");
  const status = document.getElementById("weatherStatus");
  const result = document.getElementById("weatherResult");
  const locationName = document.getElementById("weatherLocationName");
  const todayText = document.getElementById("weatherTodayText");
  const tomorrowText = document.getElementById("weatherTomorrowText");
  const updatedAt = document.getElementById("weatherUpdatedAt");

  if (!input || !button || !status || !result || !locationName || !todayText || !tomorrowText || !updatedAt) {
    return;
  }

  const formatDay = (day) => {
    if (!day) {
      return "取得できませんでした。";
    }
    return `${day.date} / ${day.weather} / 最高 ${day.max_temp}℃ / 最低 ${day.min_temp}℃`;
  };

  button.addEventListener("click", async () => {
    const location = input.value.trim();
    if (!location) {
      status.textContent = "地域名を入力してください。";
      return;
    }

    button.disabled = true;
    status.textContent = "天気を取得中です。";

    try {
      const response = await fetch("/weather", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ location })
      });
      const data = await response.json();

      if (response.ok && data.ok) {
        const weather = data.weather;
        locationName.textContent = weather.location;
        todayText.textContent = formatDay(weather.today);
        tomorrowText.textContent = formatDay(weather.tomorrow);
        updatedAt.textContent = `更新時刻：${weather.updated_at}`;
        result.hidden = false;
        status.textContent = "天気を取得しました。";
      } else {
        result.hidden = true;
        status.textContent = data.message || "天気を取得できませんでした。";
      }
    } catch (error) {
      result.hidden = true;
      status.textContent = "天気を取得できませんでした。";
    } finally {
      button.disabled = false;
    }
  });
})();
