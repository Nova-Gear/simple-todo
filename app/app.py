"""
Application Factory
Creates and configures the Flask application instance.
"""

from flask import Flask, send_from_directory
from flask_cors import CORS

from app.database import initialize_database
from app.routes.todo_routes import todo_bp


def create_app():
    """Build and return a configured Flask application."""
    app = Flask(
        __name__,
        static_folder="../static",
        static_url_path="/static",
    )

    # Enable CORS for local development
    CORS(app)

    # Register API blueprints
    app.register_blueprint(todo_bp)

    # Serve the frontend SPA
    @app.route("/")
    def serve_index():
        return send_from_directory(app.static_folder, "index.html")

    # Initialize DB tables on first request context
    with app.app_context():
        initialize_database()

    return app
