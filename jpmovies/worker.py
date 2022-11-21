"""Worker Module"""
import time
import logging
from json.decoder import JSONDecodeError
from marshmallow.exceptions import ValidationError
import boto3
from jpmovies.database import get_db_session
from jpmovies.models import (
    MovieData,
    MovieDBRecord,
    MovieCastDBRecord,
    MovieGenreDBRecord
)


class WorkerManager:
    """Worker Manager"""

    def __init__(self, handler, no_updates_sleep_seconds) -> None:
        """Initialisation function"""
        self._running = False
        self._handler = handler
        self._no_updates_sleep_seconds = no_updates_sleep_seconds

    def stop(self) -> None:
        """Sets the worker manager to start gracefully stopping"""
        self._running = False

    def is_running(self) -> bool:
        """Checks if manager is running"""
        return self._running

    def sleep(self) -> None:
        """Sleeps when no updates where found to avoid s3 bombarding"""
        logging.info("Sleeping for %d seconds", self._no_updates_sleep_seconds)
        for _ in range(self._no_updates_sleep_seconds):
            if self._running:
                time.sleep(1)

    def run(self) -> None:
        """Runs the manager"""
        if self._running:
            raise ValueError("Already running")

        self._running = True

        while self._running:
            with get_db_session() as db_session:
                updates_count = self._handler.run(db_session=db_session)

            logging.info("Parsed %d movie updates", updates_count)
            if not updates_count:
                self.sleep()

        logging.info("Manager stoppped")


class WorkerHandler:  # pylint: disable=too-few-public-methods
    """Worker Handler"""

    def __init__(self, bucket_name, limit) -> None:
        self._bucket_name = bucket_name
        self._limit = limit

    @staticmethod
    def sync_db_movie(db_session, movie_update) -> MovieDBRecord:
        """Creates or updates the db movie entry"""
        movie_record = db_session.query(MovieDBRecord).filter(
            MovieDBRecord.title == movie_update.title
        ).first()
        if movie_record:
            logging.info("Updating: %s", movie_update)
        else:
            logging.info("Adding: %s", movie_update)
            movie_record = MovieDBRecord(title=movie_update.title)

        movie_record.year = movie_update.year
        movie_record.data = movie_update.to_json()

        db_session.merge(movie_record)
        db_session.commit()

        return db_session.query(MovieDBRecord)\
            .filter(MovieDBRecord.title == movie_update.title).first()

    @staticmethod
    def sync_db_movie_cast(db_session, movie_record, movie_update) -> None:
        """Syncs cast to the given movie record"""
        movie_update_cast_set = set(movie_update.cast)
        movie_cast_records = db_session.query(MovieCastDBRecord).filter(
            MovieCastDBRecord.movie_id == movie_record.id
        ).all()
        for movie_cast_record in movie_cast_records:
            if movie_cast_record.cast in movie_update_cast_set:
                movie_update_cast_set.remove(movie_cast_record.cast)
            else:
                db_session.delete(movie_cast_record)

        for item in movie_update_cast_set:
            new_movie_cast_record = MovieCastDBRecord(
                movie_id=movie_record.id, cast=item
            )
            db_session.add(new_movie_cast_record)
            db_session.commit()

    @staticmethod
    def sync_db_movie_genres(db_session, movie_record, movie_update) -> None:
        """Syncs genre to the given movie record"""
        movie_update_genres_set = set(movie_update.genres)
        movie_genre_records = db_session.query(MovieGenreDBRecord).filter(
            MovieGenreDBRecord.movie_id == movie_record.id
        ).all()
        for movie_genre_record in movie_genre_records:
            if movie_genre_record.genre in movie_update_genres_set:
                movie_update_genres_set.remove(movie_genre_record.genre)
            else:
                db_session.delete(movie_genre_record)

        for item in movie_update_genres_set:
            new_movie_genre_record = MovieGenreDBRecord(
                movie_id=movie_record.id, genre=item
            )
            db_session.add(new_movie_genre_record)
            db_session.commit()

    def run(self, db_session) -> int:
        """
        Runs the worker execution loop

        Worker will do the following:
        1 - Fetch self._limit items from bucket
        2 - Parse the items contents. Invalid formatted items are deleted
        3 - Update database for each item
        4 - Delete item from s3 bucket
        """
        s3_resource = boto3.resource("s3")
        bucket = s3_resource.Bucket(name=self._bucket_name)

        # Fetch movie updates from S3
        movie_updates = {}
        for item in bucket.objects.limit(count=self._limit):
            try:
                # pylint: disable=no-member
                movie_update = MovieData.schema().loads(
                    item.get()['Body'].read()
                )
                movie_updates[item.key] = movie_update
            except (ValidationError, JSONDecodeError) as exc:
                logging.error(exc)
                logging.error("Deleting invalid bucket key: %s", item.key)
                s3_resource.Object(self._bucket_name, item.key).delete()

        if not movie_updates:
            return 0

        # Update database
        for bucket_item, movie_update in movie_updates.items():
            movie_record = self.sync_db_movie(
                db_session=db_session,
                movie_update=movie_update,
            )

            self.sync_db_movie_cast(
                db_session=db_session,
                movie_record=movie_record,
                movie_update=movie_update,
            )

            self.sync_db_movie_genres(
                db_session=db_session,
                movie_record=movie_record,
                movie_update=movie_update,
            )

            logging.info("Deleting bucket key: %s", {bucket_item})
            s3_resource.Object(self._bucket_name, bucket_item).delete()

        return len(movie_updates)
