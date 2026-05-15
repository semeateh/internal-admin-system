from contextlib import contextmanager

import mysql.connector
from mysql.connector import pooling

from .config import config


_pool = None


def get_pool():
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="internal_admin_pool",
            pool_size=5,
            host=config.MYSQL_HOST,
            port=config.MYSQL_PORT,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            database=config.MYSQL_DATABASE,
            charset="utf8mb4",
            collation="utf8mb4_0900_ai_ci",
        )
    return _pool


@contextmanager
def db_cursor(commit=False):
    connection = get_pool().get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        yield cursor
        if commit:
            connection.commit()
    except Exception:
        if commit:
            connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()
