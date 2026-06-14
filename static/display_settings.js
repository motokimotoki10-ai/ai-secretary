(() => {
  const DISPLAY_SIZE_KEY = "aiSecretaryDisplaySize";
  const BUTTON_SIZE_KEY = "aiSecretaryButtonSize";
  const displayInputs = document.querySelectorAll('input[name="displaySize"]');
  const buttonInputs = document.querySelectorAll('input[name="buttonSize"]');

  if (!displayInputs.length || !buttonInputs.length) {
    return;
  }

  const allowedDisplaySizes = ["standard", "large", "xlarge"];
  const allowedButtonSizes = ["standard", "large"];

  const applyDisplaySize = (size) => {
    document.body.classList.remove("display-large", "display-xlarge");
    if (size === "large") {
      document.body.classList.add("display-large");
    }
    if (size === "xlarge") {
      document.body.classList.add("display-xlarge");
    }
  };

  const applyButtonSize = (size) => {
    document.body.classList.remove("button-large");
    if (size === "large") {
      document.body.classList.add("button-large");
    }
  };

  const setCheckedValue = (inputs, value) => {
    inputs.forEach((input) => {
      input.checked = input.value === value;
    });
  };

  const savedDisplaySize = localStorage.getItem(DISPLAY_SIZE_KEY);
  const displaySize = allowedDisplaySizes.includes(savedDisplaySize)
    ? savedDisplaySize
    : "standard";
  const savedButtonSize = localStorage.getItem(BUTTON_SIZE_KEY);
  const buttonSize = allowedButtonSizes.includes(savedButtonSize)
    ? savedButtonSize
    : "standard";

  applyDisplaySize(displaySize);
  applyButtonSize(buttonSize);
  setCheckedValue(displayInputs, displaySize);
  setCheckedValue(buttonInputs, buttonSize);

  displayInputs.forEach((input) => {
    input.addEventListener("change", () => {
      localStorage.setItem(DISPLAY_SIZE_KEY, input.value);
      applyDisplaySize(input.value);
    });
  });

  buttonInputs.forEach((input) => {
    input.addEventListener("change", () => {
      localStorage.setItem(BUTTON_SIZE_KEY, input.value);
      applyButtonSize(input.value);
    });
  });
})();
