if (document.cookie.includes("tnnet.absoludique.dark=True")) {
  document.getElementById("dark-mode-chk").checked = true;
}

document.getElementById("dark-mode-btn").addEventListener("click", function () {
  if (document.cookie.includes("tnnet.absoludique.dark=True")) {
    document.cookie = "tnnet.absoludique.dark=False";
  } else {
    document.cookie = "tnnet.absoludique.dark=True";
  }
});
