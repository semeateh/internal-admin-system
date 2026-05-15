from contextlib import contextmanager

from ..db import db_cursor


@contextmanager
def process_cursor(commit=False):
    with db_cursor(commit=commit) as cursor:
        yield cursor
