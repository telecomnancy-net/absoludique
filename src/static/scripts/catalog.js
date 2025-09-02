let popUpElm = document.getElementById("pop-up-desc");

function popUpDesc(id) {
    let toDisplay = window.description[id];
    if (!toDisplay || toDisplay == "None") {
        toDisplay = "Pas des description disponible";
    }
    popUpElm.style.display = "flex";
    popUpElm.innerHTML = `
    <div>
      <img src="/static/images/icons/close.svg" alt="Fermer" />
      ${toDisplay}
    </div>
    `;
}

function closePopUpDesc() {
    popUpElm.style.display = "none";
}
