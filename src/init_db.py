import os
import mariadb
from dotenv import load_dotenv

load_dotenv()

# Read environment variables
DATABASE = {
    "host": os.getenv("MARIADB_HOST"),
    "port": int(os.getenv("MARIADB_PORT")),
    "user": os.getenv("MARIADB_USER"),
    "password": os.getenv("MARIADB_PASSWORD"),
    "database": os.getenv("MARIADB_DATABASE")
}

# Connect to MariaDB
db = mariadb.connect(**DATABASE)
cursor = db.cursor()

# Clear database
#tables = cursor.execute("SHOW TABLES;").fetchall()
#for table in tables:
#    cursor.execute(f"DROP TABLE IF EXISTS {table[0]};")


# Create tables
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        google_id VARCHAR(255) NOT NULL UNIQUE,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL,
        admin BOOLEAN NOT NULL DEFAULT TRUE
    );
    """
)
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS games (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL UNIQUE,
        description TEXT,
        time INT NOT NULL,
        nb_player_min INT NOT NULL,
        nb_player_max INT NOT NULL
    );
    """
)
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS online_games (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        link VARCHAR(255) NOT NULL,
        description TEXT
    );
    """
)
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS reservations (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        date VARCHAR(255) NOT NULL,
        game_id INT NOT NULL,
        status INT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE
    );
    """
)
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS events (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        date VARCHAR(255) NOT NULL,
        end_date VARCHAR(255),
        description TEXT NOT NULL
    );
    """
)
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS events_participant (
        id INT AUTO_INCREMENT PRIMARY KEY,
        event_id INT NOT NULL,
        user_id INT NOT NULL,
        FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """
)


# Insert first admin user
ADMIN_GOOGLE_ID = '105331217109355934878'
ADMIN_NAME = 'Romain PONSON LISSALDE'
ADMIN_EMAIL = 'romain.ponson-lissalde@telecomnancy.net'

cursor.execute(
    """
    SELECT *
    FROM users
    WHERE google_id = %s;
    """,
    (ADMIN_GOOGLE_ID,)
)
user = cursor.fetchone()
if user is None:
    cursor.execute(
        """
        INSERT INTO users (google_id, name, email, admin)
        VALUES (%s, %s, %s, %s);
        """,
        (ADMIN_GOOGLE_ID, ADMIN_NAME, ADMIN_EMAIL, 1)
    )
    db.commit()
