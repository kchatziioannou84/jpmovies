CREATE DATABASE movies;

CREATE TABLE movie
(
  id INT PRIMARY KEY AUTO_INCREMENT,
  title VARCHAR(255) NOT NULL UNIQUE,
  year INT NOT NULL,
  data TEXT,
  INDEX (year)
) ENGINE=InnoDB;

CREATE TABLE movie_cast
(
  cast VARCHAR(255) NOT NULL,
  movie_id INT NOT NULL REFERENCES movie(id),
  PRIMARY KEY(cast, movie_id)
) ENGINE=InnoDB;

CREATE TABLE movie_genre
(
  genre VARCHAR(255) NOT NULL,
  movie_id INT NOT NULL REFERENCES movie(id),
  PRIMARY KEY(genre, movie_id)
) ENGINE=InnoDB;
