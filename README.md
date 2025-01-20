# Abso'Ludique site web


## Configuration

### Projet Google

1. Allez sur [Google Cloud Console](https://console.cloud.google.com/)
2. Créer un projet Google
3. Naviguer dans `APIs & Services` > `Credentials`
4. Créer des identifiants OAuth
5. Ajouter `http://127.0.0.1:8000/google/auth/` dans les URI autorisées
6. Copiez le `Client ID` et le `Client Secret` dans le fichier `.env` à la racine du projet

### MariaDB

1. Installer MariaDB
2. Créer une base de donnée `absoludique_db`
3. Créer un utilisateur `admin_abso` avec un mot de passe
4. Donner les droits à l'utilisateur sur la base de donnée
5. Remplir les informations dans le fichier `.env`

```sql
CREATE DATABASE absoludique_db;
CREATE USER 'admin_abso'@'localhost IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON absoludique_db.* TO 'admin_abso'@'localhost;
FLUSH PRIVILEGES;
```


## Lancer le projet

### Avec une venv Python

Créer un environnement virtuel et l'activer
```bash
python3 -m venv venv
source venv/bin/activate
```

Installer les dépendances
```bash
pip install -r requirements.txt
```

Initialiser la base de donnée
```bash
python3 src/init_db.py
```

Lancer le projet
```bash
flask --app src/app.py run --port 8000
```
fixer le port en fonction du paramétrage du Oauth Google

### Avec Docker

```bash
docker-compose up --build
```

> [!WARNING]
> `MARIADB_HOST=` doit être fixé à `host.docker.internal` et non `127.0.0.1` si vous utilisez le MariaDB de votre machine.


## Technologie utilisée

**Front-end**
- HTML
- CSS vanilla
- JavaScript vanilla
- [HTMX](https://htmx.org)

**Back-end**
- Python avec [Flask](https://flask.palletsprojects.com/en/3.0.x/) + [Flask Login](https://flask-login.readthedocs.io/en/latest/) + [authlib](https://docs.authlib.org/en/latest/client/flask.html)
- [MariaDB](https://mariadb.com)


## Front-end

Chaque page a un CSS dedié. `main.css` applique le style de base.

**Schéma templating**
```
inclure head
import CSS et JS
inclure header
PAGE
inclure footer
```

### Scripts

Commun à toutes les pages :
- `cookie.js` : gère les cookies, en particulier le thème sombre
- `request_args.js` : récupère les arguments `error` ou `info` de la page et injecte le texte dans la page
- `transition_fix_chromium.js` : fixe un bug de transition sur Chromium

`catalog.js` : rajoute un popup avec la description du jeu quand on clique sur l'image

Espaces admin :  
Arboréscence `admin.js`
```
Dates
Tables
  Reservation
  User
Pages
  Reservation
  Events
  Games
  Online games
  Users
```


## Back-end

### Intéraction client <-> serveur

Pour les éléments qui changent dynamiquement comme par exemple les formulaires ou le catalogue, on utilise HTMX pour envoyer les requêtes et gérer les réponses.  
HTMX envoie une rêquete avec potentiellement des données avec, puis le serveur renvoie du HTML déjà construit qui sera ensuite remplacé par HTMX dans la page.

### Organisation du back-end

- `r_: "requête GET" -> template HTML` : Route
- `hx_: "requête POST HTMX" -> HTML` : Fonction qui intéragie avec HTMX

**Arboréscence du code Flask**
```
Initialization
Database
User
Images
Routes
  Google
  Admin
    Reservations
    Events
    Games
    Online games
    Users
```


## Arboréscence du projet

```
src/
  static/
    fonts/
    images/
      games/
        Image des jeux
      icons/
        **.svg
      online_games/
        Image des jeux en ligne
    scripts/
      **.js
    styles/
      **.css
  templates/
    **.html
  app.py
  init_db.py
.env
docker-compose.yml
Dockerfile
requirements.txt
```


## Routes

**GET**
- `/`
- `/catalog`
- `/event/<int:id>`
- `/google` connexion CETEN
- `/user` profile (c)
- `/admin` (a)
- `/edit/event/<int:id>` (a)

**POST**
- `/catalog` met à jour les items du catalogue
- `/reserve` (c)
- `/event/<int:id>` s'inscrit à l'évent (c)
- `/logout`
- `/reservations/page/<int:page>` (a)
- `/edit/reservation/<int:id>` (a)
- `/delete/reservation/<int:id>` (a)
- `/events/page/<int:page>` (a)
- `/create/event` (a)
- `/edit/event/<int:id>` (a)
- `/delete/event/<int:id>` (a)
- `/games/page/<int:page>` (a)
- `/create/game` (a)
- `/delete/game/<int:id>` (a)
- `/online-games/page/<int:page>` (a)
- `/create/online-game` (a)
- `/delete/online-game/<int:id>` (a)
- `/users/page/<int:page>` (a)
- `/edit/user/<int:id>` (a)
- `/delete/user/<int:id>` (a)

(c) besoin d'être connecté  
(a) besoin d'être admin


## Base de donnée

Voir fichier `init_db.py` pour la structure de la base de donnée.
