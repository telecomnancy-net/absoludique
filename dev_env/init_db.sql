-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS absoludique;
USE absoludique;

-- Create tables
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    google_id VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    admin BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS games (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    time INT NOT NULL,
    nb_player_min INT NOT NULL,
    nb_player_max INT NOT NULL
);

CREATE TABLE IF NOT EXISTS online_games (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    link VARCHAR(255) NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS reservations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    date VARCHAR(255) NOT NULL,
    game_id INT NOT NULL,
    status INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    date VARCHAR(255) NOT NULL,
    end_date VARCHAR(255),
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events_participant (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT NOT NULL,
    user_id INT NOT NULL,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Insert first admin user
INSERT INTO users (google_id, name, email, admin) 
VALUES ('105331217109355934878', 'Romain PONSON LISSALDE', 'romain.ponson-lissalde@telecomnancy.net', 1)
ON DUPLICATE KEY UPDATE google_id=google_id;