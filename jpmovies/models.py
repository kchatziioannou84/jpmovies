"""MoviesDB Models"""
from typing import List, Optional
from dataclasses import dataclass
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from dataclasses_json import dataclass_json


Base = declarative_base()


@dataclass_json
@dataclass
class MovieData:
    """Represents the movie data as retrieved from S3"""
    title: str
    year: int
    cast: List[str]
    genres: List[str]


@dataclass
class IndexApiResponse:
    """Represents the index api response"""
    movies_url: str


@dataclass
class MovieApiResponse:
    """Represents a single movie api response"""
    id: int  # pylint: disable=invalid-name
    title: str
    year: int
    cast: List[str]
    genres: List[str]
    self_url: str


@dataclass
class MoviesApiResponse:
    """Represents multiple movies api response"""
    movies: List[MovieApiResponse]
    next_url: Optional[str]


class MovieDBRecord(Base):  # pylint: disable=too-few-public-methods
    """Represents a movie db record"""
    __tablename__ = "movie"

    id = Column(Integer, primary_key=True)
    title = Column(String(512))
    year = Column(Integer)
    data = Column(Text)


class MovieCastDBRecord(Base):  # pylint: disable=too-few-public-methods
    """Represents a movie cast db record"""
    __tablename__ = "movie_cast"

    movie_id = Column(Integer, primary_key=True)
    cast = Column(String(255), primary_key=True)


class MovieGenreDBRecord(Base):  # pylint: disable=too-few-public-methods
    """Represents a movie genre db record"""
    __tablename__ = "movie_genre"

    movie_id = Column(Integer, primary_key=True)
    genre = Column(String(255), primary_key=True)
