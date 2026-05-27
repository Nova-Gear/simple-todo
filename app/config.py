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
    # Support both DB_DATABASE and DB_NAME (K8s ConfigMap uses DB_NAME)
    DB_DATABASE = os.getenv("DB_DATABASE") or os.getenv("DB_NAME", "todo_app")
    # Support both DB_USERNAME and DB_USER (K8s Secret uses DB_USER)
    DB_USERNAME = os.getenv("DB_USERNAME") or os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_SOCKET = os.getenv("DB_SOCKET", "")

    # Flask
    DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    HOST = os.getenv("FLASK_HOST", "0.0.0.0")
    PORT = int(os.getenv("FLASK_PORT", 5001))
