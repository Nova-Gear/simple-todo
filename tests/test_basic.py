import pytest
from app.app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_page(client):
    """Test if index page loads correctly."""
    response = client.get('/')
    assert response.status_code == 200
