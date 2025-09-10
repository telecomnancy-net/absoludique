"""
Abso'Ludique website

Version: 0.1
Author: rom100main
"""

#
#
#
#
# Initialization
import datetime
import io
import os

import mariadb
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import Flask, g, make_response, redirect, render_template, request, url_for
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from PIL import Image
# import rembg # as of now don't work with Docker, need more testing

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")

login_manager = LoginManager()
login_manager.init_app(app)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

oauth = OAuth(app)

CONF_URL = "https://accounts.google.com/.well-known/openid-configuration"
oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url=CONF_URL,
    client_kwargs={"scope": "openid email profile"},
)

if not os.path.exists("/src/static/data/games"):
    os.makedirs("/src/static/data/games")
if not os.path.exists("/src/static/data/online_games"):
    os.makedirs("/src/static/data/online_games")

#
#
#
#
# Database
DATABASE = {
    "host": os.getenv("MARIADB_HOST"),
    "port": int(os.getenv("MARIADB_PORT")),
    "user": os.getenv("MARIADB_USER"),
    "password": os.getenv("MARIADB_PASSWORD"),
    "database": os.getenv("MARIADB_DATABASE"),
}


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = mariadb.connect(**DATABASE)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


#
#
#
# User
class User(UserMixin):
    def __init__(
        self,
        name: str,
        password: bytes,
        id: int = -1,
        google_id: int = -1,
        admin: bool = False,
    ):
        self.id = id
        self.google_id = google_id
        self.name = name
        self.password = password
        self.admin = admin


@login_manager.user_loader
def load_user(user_id):
    return find_user(user_id)


def find_user(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE id = ?;
        """,
        (id,),
    )
    user = cursor.fetchone()
    if user is None:
        return None
    return User(id=id, google_id=user[1], name=user[2], password=user[3], admin=user[4])


def find_user_google_id(google_id: str):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT id
        FROM users
        WHERE google_id = ?;
        """,
        (google_id,),
    )
    id = cursor.fetchone()
    if id is None:
        return None
    id = id[0]

    return find_user(id)


def find_user_name(name: str):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT id
        FROM users
        WHERE name = ?;
        """,
        (name,),
    )
    id = cursor.fetchone()
    if id is None:
        return None
    id = id[0]

    return find_user(id)


#
#
#
#
# Images


def resize_and_convert_to_webp(file, max_width, max_height, quality=80):
    img = Image.open(file)
    # img = rembg.remove(img)
    
    original_width, original_height = img.size
    width_ratio = max_width / original_width
    height_ratio = max_height / original_height
    scaling_factor = max(width_ratio, height_ratio)
    new_width = int(original_width * scaling_factor)
    new_height = int(original_height * scaling_factor)
    img = img.resize((new_width, new_height), Image.LANCZOS)

    output = io.BytesIO()
    img.save(output, "WEBP", quality=quality)
    output.seek(0)

    return output


#
#
#
#
# Routes


@app.route("/", methods=["GET"])
def r_index():
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, name, date, description, end_date
        FROM events
        WHERE (end_date > CURDATE() - INTERVAL 1 DAY OR (end_date IS NULL AND date > CURDATE() - INTERVAL 1 DAY))
        ORDER BY date DESC;
        """
    )
    events = cursor.fetchall()

    cursor.execute(
        """
        SELECT id, name, link, description
        FROM online_games;
        """
    )
    online_games = cursor.fetchall()

    if current_user.is_authenticated:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM reservations
            """
        )
        nb_reservation = cursor.fetchone()[0]
        if nb_reservation >= 10:
            return render_template(
                "index.html",
                logged=current_user.is_authenticated,
                reservation_max=True,
                online_games=online_games,
            )

        cursor.execute(
            """
            SELECT name
            FROM games
            WHERE id NOT IN (SELECT game_id FROM reservations);
            """
        )
        games = cursor.fetchall()

        return render_template(
            "index.html",
            logged=current_user.is_authenticated,
            games=games,
            events=events,
            online_games=online_games,
        )

    return render_template(
        "index.html",
        logged=current_user.is_authenticated,
        events=events,
        online_games=online_games,
    )


@app.route("/catalog", methods=["GET"])
def r_catalog():
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT g.id, g.name, g.description, g.time, g.nb_player_min, g.nb_player_max, r.id
        FROM games AS g
        LEFT JOIN reservations AS r ON g.id = r.game_id
        """
    )
    games = cursor.fetchall()

    if current_user.is_authenticated:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM reservations
            """
        )
        nb_reservation = cursor.fetchone()[0]
        if nb_reservation >= 10:
            return render_template(
                "index.html",
                logged=current_user.is_authenticated,
                reservation_max=True,
                games=games,
            )

    return render_template(
        "catalog.html", logged=current_user.is_authenticated, games=games
    )


@app.route("/catalog", methods=["POST"])
def hx_catalog():
    db = get_db()
    cursor = db.cursor()

    name = request.form["name"]
    nb_player = request.form["nb_player"]
    max_time = request.form["max_time"]

    cursor.execute(
        """
        SELECT g.id, g.name, g.description, g.time, g.nb_player_min, g.nb_player_max, r.id
        FROM games AS g
        LEFT JOIN reservations AS r ON g.id = r.game_id
        WHERE
            ? BETWEEN g.nb_player_min AND g.nb_player_max
            AND g.time <= ?
            AND g.name LIKE CONCAT('%', ?, '%')
        """,
        (nb_player, max_time, name),
    )
    games = cursor.fetchall()

    logged = current_user.is_authenticated
    reservation_max = False
    if logged:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM reservations
            """
        )
        nb_reservation = cursor.fetchone()[0]
        if nb_reservation >= 10:
            reservation_max = True

    html = ""
    for game in games:
        html += f"""
        <li class="game" id="game-{ game[0] }">
            <div class="image" onclick="popUpDesc('{ game[0] }')" style="background-image: url('/static/data/games/{game[0]}.webp');" ></div>
            <b>{game[1]}</b>
            <ul>
                <li class="time">~{game[3]}min</li>
                <li class="nb-players">
                    {game[4]}
                    {f" - {game[5]}" if game[5] != game[4] else ""}
                    pers.
                </li>
            </ul>
            <form
                action="/reserve"
                method="post"

                hx-post="/reserve"
                hx-trigger="submit"
                hx-target="#info-catalog"
            >
                <input type="hidden" name="game" value="{game[1]}" />
                <button
                {"disabled" if not logged or reservation_max or game[6] else ""}
                >
                    Réserver
                </button>
            </form>
        </li>
        """

    if html == "":
        html = """
        <li class="game">
            Aucun jeu ne correspond à vos critères
        </li>
        """

    return html


@app.route("/reserve", methods=["POST"])
def hx_reserve():
    if not current_user.is_authenticated:
        return redirect("/?error=Vous devez être connecté pour réserver")

    game = request.form["game"]
    if game is None or game == "":
        return "Champs manquants"

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM reservations
        WHERE user_id = ?;
        """,
        (current_user.id,),
    )
    nb_reservation = cursor.fetchone()[0]
    if nb_reservation >= 10:
        return "Le nombre de réservations maximum a déjà été atteint"

    cursor.execute(
        """
        SELECT id
        FROM games
        WHERE name = ?
        AND id NOT IN (SELECT game_id FROM reservations);
        """,
        (game,),
    )
    game_id = cursor.fetchone()
    if game_id is None:
        return "Ce jeu n'existe pas ou est déjà réservé"
    game_id = game_id[0]

    cursor.execute(
        """
        SELECT id
        FROM reservations
        WHERE game_id = ?;
        """,
        (game_id,),
    )
    if cursor.fetchone() is not None:
        return "Ce jeu est déjà réservé"

    cursor.execute(
        """
        INSERT INTO reservations (user_id, date, game_id, status)
        VALUES (?, ?, ?, 0);
        """,
        (current_user.id, datetime.datetime.now().strftime("%Y-%m-%d"), game_id),
    )

    db.commit()

    return "Réservation effectuée"


@app.route("/event/<int:id>", methods=["GET"])
def r_events(id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, name, date, description
        FROM events
        WHERE id = ?;
        """,
        (id,),
    )
    event = cursor.fetchone()
    if event is None:
        return redirect("/?error=L'évènement n'existe pas")

    is_participant = False
    if current_user.is_authenticated:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM events_participant
            WHERE user_id = ?
            AND event_id = ?;
            """,
            (current_user.id, id),
        )
        is_participant = cursor.fetchone()[0] > 0

    return render_template(
        "events.html",
        logged=current_user.is_authenticated,
        event=event,
        is_participant=is_participant,
    )


@app.route("/event/<int:id>", methods=["POST"])
@login_required
def hx_event(id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM events_participant
        WHERE user_id = ?
        AND event_id = ?;
        """,
        (current_user.id, id),
    )
    is_participant = cursor.fetchone()[0] > 0

    if is_participant:
        cursor.execute(
            """
            DELETE FROM events_participant
            WHERE user_id = ?
            AND event_id = ?;
            """,
            (current_user.id, id),
        )
        db.commit()
        return "<button>S'inscrire</button>"

    cursor.execute(
        """
        INSERT INTO events_participant (event_id, user_id)
        VALUES (?, ?);
        """,
        (id, current_user.id),
    )
    db.commit()
    return "<button>Se désinscrire</button>"


@app.route("/user")
def r_user():
    if not current_user.is_authenticated:
        return redirect("/google")

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT r.id, g.name, r.date, r.status
        FROM reservations AS r
        JOIN games AS g ON r.game_id = g.id
        WHERE r.user_id = ?;
        """,
        (current_user.id,),
    )
    reservations = cursor.fetchall()

    cursor.execute(
        """
        SELECT id
        FROM reservations
        WHERE
            status = 1 AND
            user_id = ?
        AND date < CURDATE() - INTERVAL 14 DAY;
        """,
        (current_user.id,),
    )
    expired_reservations = cursor.fetchall()
    expired_reservations = [reservation[0] for reservation in expired_reservations]

    return render_template(
        "user.html",
        user=current_user,
        reservations=reservations,
        expired_reservations=expired_reservations,
    )


#
#
# Google


@app.route("/google/")
def google():
    # Redirect to google_auth function
    redirect_uri = url_for("google_auth", _external=True, _scheme="https")
    return oauth.google.authorize_redirect(redirect_uri)


@app.route("/google/auth/")
def google_auth():
    token = oauth.google.authorize_access_token()
    google_id = token["userinfo"]["sub"]

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT id
        FROM users
        WHERE google_id = ?;
        """,
        (google_id,),
    )
    user = cursor.fetchone()

    if user is not None:
        user_id = user[0]
        user = find_user(user_id)

    else:
        name = token["userinfo"]["name"]
        email = token["userinfo"]["email"]

        cursor.execute(
            """
            INSERT INTO users (google_id, name, email, admin)
            VALUES (?, ?, ?, ?);
            """,
            (google_id, name, email, False),
        )
        db.commit()

        user = find_user_google_id(google_id)

    login_user(user)

    return redirect("/?info=Connexion réussie")


@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    return redirect("/?info=Déconnexion réussie")


#
#
# Admin


@app.route("/admin", methods=["GET"])
@login_required
def r_admin():
    if not current_user.admin:
        return redirect("/?error=Accès refusé")

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT
            reservations.id,
            users.name AS user_name,
            reservations.date,
            games.name AS game_name,
            reservations.status
        FROM reservations
        JOIN games ON reservations.game_id = games.id
        JOIN users ON reservations.user_id = users.id
        LIMIT 10 OFFSET 0;
        """
    )
    reservations = cursor.fetchall()

    cursor.execute(
        """
        SELECT id
        FROM reservations
        WHERE status = 1
        AND date < CURDATE() - INTERVAL 14 DAY;
        """
    )
    expired_reservations = cursor.fetchall()
    expired_reservations = [reservation[0] for reservation in expired_reservations]

    cursor.execute(
        """
        SELECT id, name, date, description
        FROM events
        ORDER BY date DESC
        LIMIT 10 OFFSET 0;
        """
    )
    events = cursor.fetchall()

    cursor.execute(
        """
        SELECT id, name, date, description
        FROM events
        WHERE NOT (end_date > CURDATE() - INTERVAL 1 DAY OR (end_date IS NULL AND date > CURDATE() - INTERVAL 1 DAY))
        ORDER BY date DESC
        LIMIT 10 OFFSET 0;
        """
    )
    expired_events = cursor.fetchall()
    expired_events = [event[0] for event in expired_events]

    cursor.execute(
        """
        SELECT id, name
        FROM games
        LIMIT 10 OFFSET 0;
        """
    )
    games = cursor.fetchall()

    cursor.execute(
        """
        SELECT id, name, link, description
        FROM online_games
        LIMIT 10 OFFSET 0;
        """
    )
    online_games = cursor.fetchall()

    cursor.execute(
        """
        SELECT id, name, email, admin
        FROM users
        LIMIT 10 OFFSET 0;
        """
    )
    users = cursor.fetchall()

    return render_template(
        "admin.html",
        reservations=reservations,
        expired_reservations=expired_reservations,
        events=events,
        expired_events=expired_events,
        games=games,
        online_games=online_games,
        users=users,
    )


#
# Reservations


@app.route("/reservations/page/<int:page>", methods=["POST"])
@login_required
def hx_reservations_page(page):
    if not current_user.admin:
        response = make_response()
        response.headers["HX-Redirect"] = "/?error=Accès refusé"
        return response

    db = get_db()
    cursor = db.cursor()
    
    name_filter = ""
    if "name" in request.form:
        name_filter = request.form["name"]
    
    query = """
        SELECT
            reservations.id,
            users.name AS user_name,
            reservations.date,
            games.name AS game_name,
            reservations.status
        FROM reservations
        JOIN games ON reservations.game_id = games.id
        JOIN users ON reservations.user_id = users.id
    """
    
    params = []
    if name_filter:
        query += """
        WHERE users.name LIKE CONCAT('%', ?, '%')
        OR games.name LIKE CONCAT('%', ?, '%')
        """
        params.extend([name_filter, name_filter])
    
    query += " LIMIT 10 OFFSET ?;"
    params.append(page * 10)
    
    cursor.execute(query, tuple(params))
    reservations = cursor.fetchall()

    cursor.execute(
        """
        SELECT id
        FROM reservations
        WHERE status = 1
        AND date < CURDATE() - INTERVAL 14 DAY;
        """
    )
    expired_reservations = cursor.fetchall()
    expired_reservations = [reservation[0] for reservation in expired_reservations]

    html = ""
    for reservation in reservations:
        date_obj = datetime.datetime.strptime(reservation[2], "%Y-%m-%d")
        date_reservation = date_obj.strftime("%d/%m/%Y")

        html += f"""
            <tr id="reservation-{reservation[0]}">
                <td>{reservation[0]}</td>
                <td>{reservation[1]}</td>
                <td class="{"late" if reservation[0] in expired_reservations else ""}">{date_reservation}</td>
                <td>{reservation[3]}</td>
                <td>{"Emprunté" if reservation[4] == 0 else "Demandé"}</td>
                <td>
                    <button onclick="editReservation({reservation[0]}, {reservation[4]})">Éditer</button>
                    <form
                        action="/delete/reservation/{reservation[0]}"
                        method="post"

                        hx-post="/delete/reservation/{reservation[0]}"
                        hx-trigger="submit"
                        hx-target="#reservation-{reservation[0]}"
                    >
                        <button>Supprimer</button>
                    </form>
                </td>
            </tr>
        """

    return html


@app.route("/edit/reservation/<int:id>", methods=["POST"])
@login_required
def hx_edit_reservation(id):
    if not current_user.admin:
        response = make_response()
        response.headers["HX-Redirect"] = "/?error=Accès refusé"
        return response

    date = datetime.datetime.now().strftime("%Y-%m-%d")
    status = request.form["status"]

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        UPDATE reservations
        SET
            date = ?,
            status = ?
        WHERE id = ?;
        """,
        (date, status, id),
    )
    db.commit()

    return ""


@app.route("/delete/reservation/<int:id>", methods=["POST"])
@login_required
def hx_delete_reservation(id):
    if not current_user.admin:
        response = make_response()
        response.headers["HX-Redirect"] = "/?error=Accès refusé"
        return response

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        DELETE FROM reservations
        WHERE id = ?;
        """,
        (id,),
    )
    db.commit()

    return "<td class='deleted' colspan='6'>Supprimé</td>"


#
# Events


@app.route("/events/page/<int:page>", methods=["POST"])
@login_required
def hx_events_page(page):
    if not current_user.admin:
        response = make_response()
        response.headers["HX-Redirect"] = "/?error=Accès refusé"
        return response

    db = get_db()
    cursor = db.cursor()
    
    name_filter = ""
    if "name" in request.form:
        name_filter = request.form["name"]
    
    query = """
        SELECT id, name, date, description
        FROM events
    """
    
    params = []
    if name_filter:
        query += " WHERE name LIKE CONCAT('%', ?, '%')"
        params.append(name_filter)

    query += " ORDER BY date DESC LIMIT 10 OFFSET ?;"
    params.append(page * 10)
    
    cursor.execute(query, tuple(params))
    events = cursor.fetchall()

    cursor.execute(
        """
        SELECT id, name, date, description
        FROM events
        WHERE NOT (end_date > CURDATE() - INTERVAL 1 DAY OR (end_date IS NULL AND date > CURDATE() - INTERVAL 1 DAY))
        ORDER BY date DESC
        LIMIT 10 OFFSET 0;
        """
    )
    expired_events = cursor.fetchall()
    expired_events = [event[0] for event in expired_events]

    html = ""
    for event in events:
        try:
            date_obj = datetime.datetime.strptime(event[2], "%Y-%m-%dT%H:%M")
        except ValueError:
            date_obj = datetime.datetime.strptime(event[2], "%Y-%m-%d")
        date_event = date_obj.strftime("%d/%m/%Y %H:%M")
        html += f"""
            <tr id="event-{event[0]}">
                <td>{event[0]}</td>
                <td><a href="/event/{event[0]}">{event[1]}</a></td>
                <td class={"late" if event[0] in expired_events else ""} >{date_event}</td>
                <td>
                    <a class="button" href="/edit/event/{event[0]}">Éditer</a>
                    <form
                        action="/delete/event/{event[0]}"
                        method="post"

                        hx-post="/delete/event/{event[0]}"
                        hx-trigger="submit"
                        hx-target="#event-{event[0]}"
                    >
                        <button>Supprimer</button>
                    </form>
                </td>
            </tr>
        """

    return html


@app.route("/create/event", methods=["POST"])
@login_required
def hx_create_event():
    if not current_user.admin:
        response = make_response()
        response.headers["HX-Redirect"] = "/?error=Accès refusé"
        return response

    name = request.form["name"]
    date = request.form["date"]
    end_date = request.form["end_date"] if request.form["end_date"] != "" else None
    description = request.form["description"]

    if None in [name, date, description] or "" in [name, date, description]:
        return "Champs manquants"

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO events (name, date, end_date, description)
        VALUES (?, ?, ?, ?);
        """,
        (name, date, end_date, description),
    )
    db.commit()

    return "Nouvel évènement créé, rechargez la page pour le voir apparaître"


@app.route("/edit/event/<int:id>", methods=["GET"])
@login_required
def r_edit_event(id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, name, date, description
        FROM events
        WHERE id = ?;
        """,
        (id,),
    )
    event = cursor.fetchone()
    if event is None:
        return redirect("/admin?error=L'évènement n'existe pas")

    cursor.execute(
        """
        SELECT id, name, email
        FROM users
        WHERE id IN (SELECT user_id FROM events_participant WHERE event_id = ?);
        """,
        (id,),
    )
    participants = cursor.fetchall()

    return render_template(
        "edit_event.html",
        logged=current_user.is_authenticated,
        event=event,
        participants=participants,
    )


@app.route("/delete/event/<int:id>", methods=["POST"])
@login_required
def hx_delete_event(id):
    if not current_user.admin:
        response = make_response()
        response.headers["HX-Redirect"] = "/?error=Accès refusé"
        return response

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        DELETE FROM events
        WHERE id = ?;
        """,
        (id,),
    )
    db.commit()

    return "<td class='deleted' colspan='3'>Supprimé</td>"


@app.route("/purge/events", methods=["POST"])
@login_required
def hx_purge_events():
    if not current_user.admin:
        response = make_response()
        response.headers["HX-Redirect"] = "/?error=Accès refusé"
        return response

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        DELETE FROM events
        WHERE NOT (end_date > CURDATE() - INTERVAL 1 DAY OR (end_date IS NULL AND date > CURDATE() - INTERVAL 1 DAY));
        """
    )
    db.commit()

    return "Effetué avec succès, rechargez la page pour voir les changements"


@app.route("/edit/event/<int:id>", methods=["POST"])
@login_required
def hx_edit_event(id):
    if not current_user.admin:
        response = make_response()
        response.headers["HX-Redirect"] = "/?error=Accès refusé"
        return response

    name = request.form["name"]
    date = request.form["date"]
    description = request.form["description"]

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE events
        SET
            name = ?,
            date = ?,
            description = ?
        WHERE id = ?;
        """,
        (name, date, description, id),
    )
    db.commit()

    return "Modification effectuée"


#
# Games


@app.route("/games/page/<int:page>", methods=["POST"])
@login_required
def hx_games_page(page):
    if not current_user.admin:
        response = make_response()
        response.headers["HX-Redirect"] = "/?error=Accès refusé"
        return response

    db = get_db()
    cursor = db.cursor()
    
    name_filter = ""
    if "name" in request.form:
        name_filter = request.form["name"]
    
    query = """
        SELECT id, name
        FROM games
    """
    
    params = []
    if name_filter:
        query += " WHERE name LIKE CONCAT('%', ?, '%')"
        params.append(name_filter)
    
    query += " LIMIT 10 OFFSET ?;"
    params.append(page * 10)
    
    cursor.execute(query, tuple(params))
    games = cursor.fetchall()

    html = ""
    for game in games:
        html += f"""
            <tr id="game-{game[0]}">
                <td>{game[0]}</td>
                <td>{game[1]}</td>
                <td>
                    <a class="button" href="/edit/game/{game[0]}">Éditer</a>
                    <form
                        action="/delete/game/{game[0]}"
                        method="post"

                        hx-post="/delete/game/{game[0]}"
                        hx-trigger="submit"
                        hx-target="#game-{game[0]}"
                    >
                        <button>Supprimer</button>
                    </form>
                </td>
            </tr>
        """

    return html


@app.route("/create/game", methods=["POST"])
@login_required
def hx_create_game():
    if not current_user.admin:
        response = make_response()
        response.headers["HX-Redirect"] = "/?error=Accès refusé"
        return response

    name = request.form["name"]
    description = request.form["description"]
    time = request.form["time"]
    nb_player_min = request.form["nb_player_min"]
    nb_player_max = request.form["nb_player_max"]
    image = request.files["image"]

    if None in [name, time, nb_player_min, nb_player_max, image] or "" in [
        name,
        time,
        nb_player_min,
        nb_player_max,
    ]:
        return "Champs manquants"

    max_width = 175
    max_height = 200
    quality = 80
    image = resize_and_convert_to_webp(image, max_width, max_height, quality)

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        INSERT INTO games (name, description, time, nb_player_min, nb_player_max)
        VALUES (?, ?, ?, ?, ?);
        """,
        (name, description, time, nb_player_min, nb_player_max),
    )
    db.commit()

    game_id = cursor.lastrowid
    try:
        with open(f"static/data/games/{game_id}.webp", "wb") as f:
            f.write(image.getbuffer())
    except Exception as e:
        import traceback
        return f"Error saving image: {str(e)}\n{traceback.format_exc()}"

    return "Nouveau jeu créé, rechargez la page pour le voir apparaître"


@app.route("/delete/game/<int:id>", methods=["POST"])
@login_required
def hx_delete_game(id):
    if not current_user.admin:
        response = make_response()
        response.headers["HX-Redirect"] = "/?error=Accès refusé"
        return response

    image_path = f"static/data/games/{id}.webp"
    if os.path.exists(image_path):
        os.remove(image_path)

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        DELETE FROM games
        WHERE id = ?;
        """,
        (id,),
    )
    db.commit()

    return "<td class='deleted' colspan='3'>Supprimé</td>"


@app.route("/edit/game/<int:id>", methods=["GET"])
@login_required
def r_edit_game(id):
    if not current_user.admin:
        return redirect("/?error=Accès refusé")
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute(
        """
        SELECT id, name, description, time, nb_player_min, nb_player_max
        FROM games
        WHERE id = ?;
        """,
        (id,),
    )
    game = cursor.fetchone()
    if game is None:
        return redirect("/admin?error=Le jeu n'existe pas")
    
    return render_template(
        "edit_game.html",
        logged=current_user.is_authenticated,
        game=game,
    )


@app.route("/edit/game/<int:id>", methods=["POST"])
@login_required
def hx_edit_game(id):
    if not current_user.admin:
        response = make_response()
        response.headers["HX-Redirect"] = "/?error=Accès refusé"
        return response
    
    name = request.form["name"]
    description = request.form["description"]
    time = request.form["time"]
    nb_player_min = request.form["nb_player_min"]
    nb_player_max = request.form["nb_player_max"]
    image = request.files["image"]
    
    if None in [name, time, nb_player_min, nb_player_max] or "" in [
        name,
        time,
        nb_player_min,
        nb_player_max,
    ]:
        return "Champs manquants"
    
    db = get_db()
    cursor = db.cursor()
    
    # Update game information
    cursor.execute(
        """
        UPDATE games
        SET
            name = ?,
            description = ?,
            time = ?,
            nb_player_min = ?,
            nb_player_max = ?
        WHERE id = ?;
        """,
        (name, description, time, nb_player_min, nb_player_max, id),
    )
    
    # Handle image upload if provided
    if image and image.filename != "":
        max_width = 175
        max_height = 200
        quality = 80
        image = resize_and_convert_to_webp(image, max_width, max_height, quality)
        
        try:
            with open(f"static/data/games/{id}.webp", "wb") as f:
                f.write(image.getbuffer())
        except Exception as e:
            import traceback
            return f"Error saving image: {str(e)}\n{traceback.format_exc()}"
    
    db.commit()
    
    return "Modification effectuée"


#
# Online games


@app.route("/online-games/page/<int:page>", methods=["POST"])
@login_required
def hx_online_games_page(page):
    if not current_user.admin:
        response = make_response()
        response.headers["HX-Redirect"] = "/?error=Accès refusé"
        return response

    db = get_db()
    cursor = db.cursor()
    
    name_filter = ""
    if "name" in request.form:
        name_filter = request.form["name"]
    
    query = """
        SELECT id, name, link, description
        FROM online_games
    """
    
    params = []
    if name_filter:
        query += " WHERE name LIKE CONCAT('%', ?, '%')"
        params.append(name_filter)
    
    query += " LIMIT 10 OFFSET ?;"
    params.append(page * 10)
    
    cursor.execute(query, tuple(params))
    online_games = cursor.fetchall()

    html = ""
    for online_game in online_games:
        html += f"""
            <tr id="online-game-{online_game[0]}">
                <td>{online_game[0]}</td>
                <td>{online_game[1]}</td>
                <td>
                    <form
                        action="/delete/online-game/{online_game[0]}"
                        method="post"

                        hx-post="/delete/online-game/{online_game[0]}"
                        hx-trigger="submit"
                        hx-target="#online-game-{online_game[0]}"
                    >
                        <button>Supprimer</button>
                    </form>
                </td>
            </tr>
        """

    return html


@app.route("/create/online-game", methods=["POST"])
@login_required
def hx_create_online_game():
    if not current_user.admin:
        response = make_response()
        response.headers["HX-Redirect"] = "/?error=Accès refusé"
        return response

    name = request.form["name"]
    link = request.form["link"]
    description = request.form["description"]
    image = request.files["image"]

    if None in [name, link, description, image] or "" in [name, link, description]:
        return "Champs manquants"

    max_width = 150
    max_height = 200
    quality = 80
    image = resize_and_convert_to_webp(image, max_width, max_height, quality)

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        INSERT INTO online_games (name, description)
        VALUES (?, ?);
        """,
        (name, description),
    )
    db.commit()

    online_game_id = cursor.lastrowid
    with open(f"static/data/online_games/{online_game_id}.webp", "wb") as f:
        f.write(image.getbuffer())

    return "Nouveau jeu créé, rechargez la page pour le voir apparaître"


@app.route("/delete/online-game/<int:id>", methods=["POST"])
@login_required
def hx_delete_online_game(id):
    if not current_user.admin:
        response = make_response()
        response.headers["HX-Redirect"] = "/?error=Accès refusé"
        return response

    image_path = f"static/data/online_games/{id}.webp"
    if os.path.exists(image_path):
        os.remove(image_path)

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        DELETE FROM online_games
        WHERE id = ?;
        """,
        (id,),
    )
    db.commit()

    return "<td class='deleted' colspan='3'>Supprimé</td>"


#
# Users


@app.route("/users/page/<int:page>", methods=["POST"])
@login_required
def hx_users_page(page):
    if not current_user.admin:
        response = make_response()
        response.headers["HX-Redirect"] = "/?error=Accès refusé"
        return response

    db = get_db()
    cursor = db.cursor()
    
    name_filter = ""
    if "name" in request.form:
        name_filter = request.form["name"]
    
    query = """
        SELECT id, name, email, admin
        FROM users
    """
    
    params = []
    if name_filter:
        query += " WHERE name LIKE CONCAT('%', ?, '%')"
        params.append(name_filter)
    
    query += " LIMIT 10 OFFSET ?;"
    params.append(page * 10)
    
    cursor.execute(query, tuple(params))
    users = cursor.fetchall()

    html = ""
    for user in users:
        html += f"""
            <tr id="user-{user[0]}">
                <td>{user[0]}</td>
                <td>{user[1]}</td>
                <td>{user[2]}</td>
                <td>{"Oui" if user[3] == 1 else "Non"}</td>
                <td>
                    <button onclick="editUser({user[0]}, {user[3]})">Éditer</button>
                    <form
                        action="/delete/user/{user[0]}"
                        method="post"

                        hx-post="/delete/user/{user[0]}"
                        hx-trigger="submit"
                        hx-target="#user-{user[0]}"
                    >
                        <button>Supprimer</button>
                    </form>
                </td>
            </tr>
        """

    return html


@app.route("/edit/user/<int:id>", methods=["POST"])
@login_required
def hx_edit_user(id):
    if not current_user.admin:
        response = make_response()
        response.headers["HX-Redirect"] = "/?error=Accès refusé"
        return response

    admin = request.form["admin"]

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        UPDATE users
        SET admin = ?
        WHERE id = ?;
        """,
        (admin, id),
    )
    db.commit()

    return ""


@app.route("/delete/user/<int:id>", methods=["POST"])
@login_required
def hx_delete_user(id):
    if not current_user.admin:
        return redirect("/?error=Accès refusé")

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        DELETE FROM users
        WHERE id = ?;
        """,
        (id,),
    )
    db.commit()

    return "<td class='deleted' colspan='5'>Supprimé</td>"


#
#
#
#
# Run the app

# if __name__ == '__main__':
#    app.run(debug=True)
