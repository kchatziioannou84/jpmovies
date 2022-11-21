"""Entrypoint script to run the Movies Worker"""
import sys
import os
import logging
import signal
from jpmovies.worker import WorkerHandler, WorkerManager


def run():
    """Run the worker"""
    def signal_handler(_sig, _frame):
        if manager.is_running():
            print('Stopping worker. Press one more time to exit immediately!')
            manager.stop()
        else:
            sys.exit(-1)

    bucket_name = os.environ.get("MOVIES_BUCKET_NAME")
    if not bucket_name:
        print("Please supply MOVIES_BUCKET_NAME to read from")
        sys.exit(-1)

    items_limit = os.environ.get("MOVIES_BUCKET_ITEMS_LIMIT", 50)
    no_updates_sleep_seconds = os.environ.get(
        "MOVIES_NO_UPDATED_SLEEPS_SECONDS", 60
    )
    verbose = os.environ.get("MOVIES_VERBOSE")

    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)

    handler = WorkerHandler(bucket_name=bucket_name, limit=items_limit)
    manager = WorkerManager(
        handler=handler, no_updates_sleep_seconds=no_updates_sleep_seconds
    )

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    manager.run()


if __name__ == '__main__':
    run()
