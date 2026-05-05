"""
Application Configuration
Loads environment variables and provides a centralized config object.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Centralized application configuration loaded from environment variables."""

    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_DATABASE = os.getenv("DB_DATABASE", "todo_app")
    DB_USERNAME = os.getenv("DB_USERNAME", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_SOCKET = os.getenv("DB_SOCKET", "")

    # Flask
    DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    HOST = os.getenv("FLASK_HOST", "0.0.0.0")
    PORT = int(os.getenv("FLASK_PORT", 5001))
