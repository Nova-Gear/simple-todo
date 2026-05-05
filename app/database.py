"""
Database Connection Manager
Handles MySQL connection pooling and provides a context manager for safe queries.
"""

import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager

from app.config import Config


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


def initialize_database():
    """
    Create the required tables if they don't exist.
    Called once on application startup.
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

    with get_cursor() as cursor:
        cursor.execute(create_table_query)
