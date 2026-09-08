from unittest.mock import MagicMock, patch
import psycopg2
import pytest
from app import app as flask_app

PATCH_TARGET = 'routes.auth_routes.db_cursor'


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client


@patch(PATCH_TARGET)
def test_auth_register_success(mock_db_cursor, client):
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = {'id': 1}
    mock_db_cursor.return_value.__enter__.return_value = mock_cursor

    payload = {'username': 'newuser', 'password': 'password123'}
    response = client.post('/auth/register', json=payload)

    assert response.status_code == 201
    assert response.get_json()['id'] == 1


@patch(PATCH_TARGET)
def test_auth_register_duplicate_username(mock_db_cursor, client):
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = psycopg2.errors.UniqueViolation()
    mock_db_cursor.return_value.__enter__.return_value = mock_cursor

    payload = {'username': 'existing_user', 'password': 'password123'}
    response = client.post('/auth/register', json=payload)

    assert response.status_code == 400


@patch(PATCH_TARGET)
def test_auth_register_db_connection_error(mock_db_cursor, client):
    mock_db_cursor.return_value.__enter__.side_effect = ConnectionError()

    payload = {'username': 'testuser', 'password': 'password123'}
    response = client.post('/auth/register', json=payload)

    assert response.status_code == 500


@patch(PATCH_TARGET)
def test_auth_register_missing_fields(mock_db_cursor, client):
    payload = {'username': 'onlyusername'}
    response = client.post('/auth/register', json=payload)

    assert response.status_code == 400