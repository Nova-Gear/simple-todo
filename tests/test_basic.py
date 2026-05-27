import pytest
from unittest.mock import patch
from app.app import create_app


@pytest.fixture
def client():
    # Patch database init so tests run without a real MySQL connection in CI
    with patch("app.app.initialize_database"):
        app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index_page(client):
    """Test that the index page serves the SPA HTML."""
    response = client.get("/")
    assert response.status_code == 200
