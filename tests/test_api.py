import uuid

import pytest
from fastapi.testclient import TestClient

from main import app

URL = 'http://0.0.0.0:8000'


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as cl:
        yield cl


def test_all_users(client: TestClient) -> None:
    users = client.get(f"{URL}/all").json()
    assert isinstance(users, list)
    assert users


def test_register_user(client: TestClient) -> None:
    resp = client.post(
        f"{URL}/register",
        json={
            "email": f"{uuid.uuid4().hex}@gmail.com",
            "full_name": "Name FA",
            "password": "123",
        },
    )
    assert resp.status_code == 200
