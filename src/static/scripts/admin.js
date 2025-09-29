//
//
// Before request
function beforeRequest(el_char) {
    el = document.getElementById(el_char);
    el.getElementsByClassName("response")[0].innerHTML =
        "En cours de téléversement...";
}

//
//
// Dates

document.addEventListener("DOMContentLoaded", function () {
    const inputs = document.querySelectorAll('input[type="datetime-local"]');
    inputs.forEach((input) => {
        if (input.value) {
            input.style.color = "var(--c-text)";
        }
        input.addEventListener("input", function () {
            if (input.value) {
                input.style.color = "var(--c-text)";
            } else {
                input.style.color = "var(--c-min-text)";
            }
        });
    });
});

//
//
// Tables
// quand on clique sur le button `edit` change la ligne pour pouvoir modifier les valeurs

//
// Reservation

function editReservation(id, status) {
    let reservation = document.getElementById("reservation-" + id);
    let tds = reservation.getElementsByTagName("td");

    tds[4].innerHTML = `
      <select name="status">
        <option value="0" ${status == 0 ? "selected" : ""}>Demandé</option>
        <option value="1" ${status == 1 ? "selected" : ""}>Emprunté</option>
      </select>
    `;

    tds[5].innerHTML = `
    <button onclick="editedReservation(${id})">Modifier</button>
    `;
}

function editedReservation(id) {
    let reservation = document.getElementById("reservation-" + id);
    let tds = reservation.getElementsByTagName("td");

    let status = tds[4].getElementsByTagName("select")[0].value;
    status = parseInt(status);

    fetch("/edit/reservation/" + id, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({
            status: status,
        }),
    });

    tds[4].innerHTML = `${status === 1 ? "Emprunté" : "Demandé"}`;
    tds[5].innerHTML = `
    <button onclick="editReservation(${id}, ${status})">Éditer</button>
    <form
        action="/delete/reservation/${id}"
        method="post"

        hx-post="/delete/reservation/${id}"
        hx-trigger="submit"
        hx-target="#reservation-${id}"
    >
        <button>Supprimer</button>
    </form>
    `;

    htmx.process(tds[5]);
}

//
// Users

function editUser(id, admin) {
    let user = document.getElementById("user-" + id);
    let tds = user.getElementsByTagName("td");

    tds[3].innerHTML = `
      <input type="checkbox" name="admin" ${admin ? "checked" : ""} />
    `;

    tds[4].innerHTML = `
    <button onclick="editedUser(${id})">Modifier</button>
    `;
}

function editedUser(id) {
    let user = document.getElementById("user-" + id);
    let tds = user.getElementsByTagName("td");

    let admin = tds[3].getElementsByTagName("input")[0].checked;
    if (admin) {
        admin = 1;
    } else {
        admin = 0;
    }

    fetch("/edit/user/" + id, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({
            admin: admin,
        }),
    });

    tds[3].innerHTML = `${admin === 1 ? "Oui" : "Non"}`;
    tds[4].innerHTML = `
    <button onclick="editUser(${id}, ${admin})">Éditer</button>
    <form
        action="/delete/user/${id}"
        method="post"

        hx-post="/delete/user/${id}"
        hx-trigger="submit"
        hx-target="#user-${id}"
    >
        <button>Supprimer</button>
    </form>
    `;

    htmx.process(tds[4]);
}

//
//
// Pages

//
// Reservations

function changePageReservations(page) {
    let reservations = document.getElementById("reservations");
    let pageNav = reservations.getElementsByClassName("page-nav")[0];
    let buttons = pageNav.getElementsByTagName("button");
    let pageDiv = pageNav.getElementsByTagName("div")[0];

    let prevPage = Math.max(0, page - 1);
    let nextPage = page + 1;

    pageDiv.innerHTML = page + 1;

    buttons[0].setAttribute("hx-post", "/reservations/page/" + prevPage);
    buttons[0].setAttribute(
        "hx-on::before-request",
        "changePageReservations(" + prevPage + ")",
    );

    buttons[1].setAttribute("hx-post", "/reservations/page/" + nextPage);
    buttons[1].setAttribute(
        "hx-on::before-request",
        "changePageReservations(" + nextPage + ")",
    );

    htmx.process(buttons[0]);
    htmx.process(buttons[1]);
}

//
// Events

function changePageEvents(page) {
    let events = document.getElementById("events");
    let pageNav = events.getElementsByClassName("page-nav")[0];
    let buttons = pageNav.getElementsByTagName("button");
    let pageDiv = pageNav.getElementsByTagName("div")[0];

    let prevPage = Math.max(0, page - 1);
    let nextPage = page + 1;

    pageDiv.innerHTML = page + 1;

    buttons[0].setAttribute("hx-post", "/events/page/" + prevPage);
    buttons[0].setAttribute(
        "hx-on::before-request",
        "changePageEvents(" + prevPage + ")",
    );

    buttons[1].setAttribute("hx-post", "/events/page/" + nextPage);
    buttons[1].setAttribute(
        "hx-on::before-request",
        "changePageEvents(" + nextPage + ")",
    );

    htmx.process(buttons[0]);
    htmx.process(buttons[1]);
}

//
// Games

function changePageGames(page) {
    let games = document.getElementById("games");
    let pageNav = games.getElementsByClassName("page-nav")[0];
    let buttons = pageNav.getElementsByTagName("button");
    let pageDiv = pageNav.getElementsByTagName("div")[0];

    let prevPage = Math.max(0, page - 1);
    let nextPage = page + 1;

    pageDiv.innerHTML = page + 1;

    buttons[0].setAttribute("hx-post", "/games/page/" + prevPage);
    buttons[0].setAttribute(
        "hx-on::before-request",
        "changePageGames(" + prevPage + ")",
    );

    buttons[1].setAttribute("hx-post", "/games/page/" + nextPage);
    buttons[1].setAttribute(
        "hx-on::before-request",
        "changePageGames(" + nextPage + ")",
    );

    htmx.process(buttons[0]);
    htmx.process(buttons[1]);
}

//
// Online games

function changePageOnlineGames(page) {
    let onlineGames = document.getElementById("online-games");
    let pageNav = onlineGames.getElementsByClassName("page-nav")[0];
    let buttons = pageNav.getElementsByTagName("button");
    let pageDiv = pageNav.getElementsByTagName("div")[0];

    let prevPage = Math.max(0, page - 1);
    let nextPage = page + 1;

    pageDiv.innerHTML = page + 1;
    buttons[0].setAttribute("hx-post", "/online-games/page/" + prevPage);
    buttons[0].setAttribute(
        "hx-on::before-request",
        "changePageOnlineGames(" + prevPage + ")",
    );
    buttons[1].setAttribute("hx-post", "/online-games/page/" + nextPage);
    buttons[1].setAttribute(
        "hx-on::before-request",
        "changePageOnlineGames(" + nextPage + ")",
    );

    htmx.process(buttons[0]);
    htmx.process(buttons[1]);
}

//
// Users

function changePageUsers(page) {
    let users = document.getElementById("users");
    let pageNav = users.getElementsByClassName("page-nav")[0];
    let buttons = pageNav.getElementsByTagName("button");
    let pageDiv = pageNav.getElementsByTagName("div")[0];

    let prevPage = Math.max(0, page - 1);
    let nextPage = page + 1;

    pageDiv.innerHTML = page + 1;

    buttons[0].setAttribute("hx-post", "/users/page/" + prevPage);
    buttons[0].setAttribute(
        "hx-on::before-request",
        "changePageUsers(" + prevPage + ")",
    );

    buttons[1].setAttribute("hx-post", "/users/page/" + nextPage);
    buttons[1].setAttribute(
        "hx-on::before-request",
        "changePageUsers(" + nextPage + ")",
    );

    htmx.process(buttons[0]);
    htmx.process(buttons[1]);
}
