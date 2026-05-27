"""
Database Connection Manager
Handles MySQL connection pooling and provides a context manager for safe queries.
"""

import time
import logging
import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager

from app.config import Config

logger = logging.getLogger(__name__)


def _build_connect_kwargs():
    """Build connection keyword arguments based on config."""
    kwargs = {
        "host": Config.DB_HOST,
        "port": Config.DB_PORT,
        "user": Config.DB_USERNAME,
        "password": Config.DB_PASSWORD,
        "database": Config.DB_DATABASE,
        "charset": "utf8mb4",
        "cursorclass": DictCursor,
        "autocommit": False,
    }

    # Use unix socket if provided, otherwise TCP
    if Config.DB_SOCKET:
        kwargs["unix_socket"] = Config.DB_SOCKET

    return kwargs


def get_connection():
    """Create and return a new database connection."""
    return pymysql.connect(**_build_connect_kwargs())


@contextmanager
def get_cursor():
    """
    Context manager that provides a database cursor with automatic
    commit/rollback and connection cleanup.

    Usage:
        with get_cursor() as cursor:
            cursor.execute("SELECT * FROM todos")
            results = cursor.fetchall()
    """
    connection = get_connection()
    try:
        cursor = connection.cursor()
        yield cursor
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def initialize_database(max_retries: int = 10, retry_delay: float = 3.0):
    """
    Create the required tables if they don't exist.
    Called once on application startup. Retries on connection failure
    to handle the Cloud SQL Auth Proxy startup latency.
    """
    create_table_query = """
    CREATE TABLE IF NOT EXISTS todos (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        description TEXT DEFAULT NULL,
        is_completed TINYINT(1) NOT NULL DEFAULT 0,
        priority ENUM('low', 'medium', 'high') NOT NULL DEFAULT 'medium',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            with get_cursor() as cursor:
                cursor.execute(create_table_query)
            logger.info("Database initialized successfully (attempt %d)", attempt)
            return
        except Exception as exc:
            last_error = exc
            logger.warning(
                "Database not ready (attempt %d/%d): %s — retrying in %.0fs",
                attempt, max_retries, exc, retry_delay,
            )
            if attempt < max_retries:
                time.sleep(retry_delay)

    raise RuntimeError(
        f"Could not connect to database after {max_retries} attempts"
    ) from last_error
