"""Movies API"""
from typing import List, Optional
from flask import Flask, jsonify, request, make_response
from werkzeug.urls import url_encode
from jpmovies.database import get_db_session
from jpmovies.models import (
    MovieData,
    MoviesApiResponse,
    IndexApiResponse,
    MovieDBRecord,
    MovieCastDBRecord,
    MovieGenreDBRecord,
    MovieApiResponse
)


app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
db_session = get_db_session()


@app.route("/")
def index_handler():
    """
    Index handler
    """
    return jsonify(IndexApiResponse(movies_url="/movies"))


@app.errorhandler(404)
def not_found():
    """Catch all errors handler"""
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.route('/health', methods=['GET'])
def health():
    """API Health handler"""
    return make_response(jsonify({'status': 'ok'}), 200)


def make_next_url(
    movies: List[MovieApiResponse], query_limit: int
) -> Optional[str]:
    """
    Generates the next url when traversing movies

    :param movies: List[MovieApiResponse] the list of movies
    :param query_limit: int how many movies are returned per cursor
    :returns the url that to go to next cursor. None when no more results exist
    """
    if len(movies) < query_limit:
        return None

    min_movie_id = min((item.id for item in movies), default=0)
    if not min_movie_id:
        return None

    request_args = request.args.copy()
    request_args["start"] = min_movie_id

    return f"{request.path}?{url_encode(request_args)}"


def make_movie_response(movies_db_item: MovieDBRecord) -> MovieApiResponse:
    """Creates a response from the given moviee db item"""
    # pylint: disable=no-member
    movie_data = MovieData.schema().loads(movies_db_item.data)

    return MovieApiResponse(
        id=movies_db_item.id,
        title=movie_data.title,
        year=movie_data.year,
        cast=movie_data.cast,
        genres=movie_data.genres,
        self_url=f"/movies/{movies_db_item.id}"
    )


@app.route("/movies/<int:movie_id>")
def movie_handler(movie_id):
    """Single Movie handler"""
    movies_db_item = db_session.query(MovieDBRecord).filter(
        MovieDBRecord.id == movie_id
    ).first()
    if movies_db_item is None:
        return make_response(jsonify({'error': 'Not found'}), 404)

    return jsonify(make_movie_response(movies_db_item))


@app.route("/movies")
def movies_handler():
    """All movies handler"""
    filter_title = request.args.get('title', type=str)
    filter_year = request.args.get('year', type=int)
    filter_cast = request.args.get('cast', type=str)
    filter_genre = request.args.get('genre', type=str)
    filter_start = request.args.get('start', type=int)
    query_limit = max(min(request.args.get('limit', 25, type=int), 25), 1)

    movies_db_query = db_session.query(MovieDBRecord).order_by(
        MovieDBRecord.id.desc()
    )

    if filter_title:
        movies_db_query = movies_db_query.filter(
            MovieDBRecord.title == filter_title
        )

    if filter_year:
        movies_db_query = movies_db_query.filter(
            MovieDBRecord.year == filter_year
        )

    if filter_start:
        movies_db_query = movies_db_query.filter(
            MovieDBRecord.id < filter_start
        )

    if filter_cast:
        movies_db_query = movies_db_query.filter(MovieDBRecord.id.in_(
            db_session.query(MovieCastDBRecord.movie_id).filter(
                MovieCastDBRecord.cast == filter_cast)
            )
        )

    if filter_genre:
        movies_db_query = movies_db_query.filter(MovieDBRecord.id.in_(
            db_session.query(MovieGenreDBRecord.movie_id).filter(
                MovieGenreDBRecord.genre == filter_genre)
            )
        )

    movies = [
        make_movie_response(movies_db_item)
        for movies_db_item in movies_db_query.limit(query_limit)
    ]

    response = MoviesApiResponse(
        movies=movies,
        next_url=make_next_url(movies, query_limit)
    )

    return jsonify(response)
