"""
Application Entry Point
Run with: python run.py
"""

from app.app import create_app
from app.config import Config

application = create_app()

if __name__ == "__main__":
    print(f"\n🚀 Simple Todo API running at http://localhost:{Config.PORT}")
    print(f"📦 Database: {Config.DB_DATABASE}@{Config.DB_HOST}:{Config.DB_PORT}\n")
    application.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG,
    )
