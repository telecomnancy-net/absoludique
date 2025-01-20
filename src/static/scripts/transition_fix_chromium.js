if (!!window.chrome) {
  var styleElm = document.createElement("style");
  var cssRules = "* {transition: unset !important}";
  styleElm.textContent = cssRules;
  document.head.appendChild(styleElm);
}
