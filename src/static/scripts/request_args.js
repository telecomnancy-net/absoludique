const urlParams = new URLSearchParams(window.location.search);
const error = urlParams.get("error");
const info = urlParams.get("info");

const errorElm = document.querySelector("#error");
const infoElm = document.querySelector("#info");

if (error) {
  errorElm.textContent += error;
}
if (info) {
  infoElm.textContent += info;
}
