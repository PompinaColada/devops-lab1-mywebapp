import pytest
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app  # noqa: E402


@pytest.fixture
def mock_db_resources():
    mock_cursor = AsyncMock()
    mock_cursor.execute = AsyncMock()
    mock_cursor.fetchall = AsyncMock(return_value=[])
    mock_cursor.fetchone = AsyncMock(return_value=None)
    mock_cursor.lastrowid = 1

    mock_conn = AsyncMock()

    mock_conn_ctx = MagicMock()
    mock_conn_ctx.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_conn_ctx.__aexit__ = AsyncMock(return_value=None)

    mock_cursor_ctx = MagicMock()
    mock_cursor_ctx.__aenter__ = AsyncMock(return_value=mock_cursor)
    mock_cursor_ctx.__aexit__ = AsyncMock(return_value=None)

    mock_conn.cursor = MagicMock(return_value=mock_cursor_ctx)

    mock_pool = MagicMock()
    mock_pool.acquire = MagicMock(return_value=mock_conn_ctx)
    mock_pool.close = MagicMock()
    mock_pool.wait_closed = AsyncMock()

    return mock_pool, mock_cursor


@pytest.fixture(autouse=True)
async def apply_db_mock(mock_db_resources):
    mock_pool, mock_cursor = mock_db_resources
    with patch("aiomysql.create_pool", AsyncMock(return_value=mock_pool)):
        import app.main
        app.main.db_pool = mock_pool
        yield mock_pool, mock_cursor
        app.main.db_pool = None


@pytest.mark.asyncio
async def test_read_root():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert "Simple Inventory Business Logic Endpoints" in response.text


@pytest.mark.asyncio
async def test_health_alive():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health/alive")
    assert response.status_code == 200
    assert response.text == "OK"


@pytest.mark.asyncio
async def test_health_ready_success():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health/ready")
    assert response.status_code == 200
    assert response.text == "Ready"


@pytest.mark.asyncio
async def test_health_ready_failure(mock_db_resources):
    mock_pool, _ = mock_db_resources
    mock_pool.acquire.side_effect = Exception("DB connection timeout")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health/ready")
    assert response.status_code == 500
    assert "Database connection failed" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_items_json(mock_db_resources):
    _, mock_cursor = mock_db_resources
    mock_cursor.fetchall.return_value = [
        {"id": 1, "name": "Server R740"},
        {"id": 2, "name": "Switch Cisco"}
    ]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/items")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Server R740"


@pytest.mark.asyncio
async def test_get_items_html(mock_db_resources):
    _, mock_cursor = mock_db_resources
    mock_cursor.fetchall.return_value = [
        {"id": 1, "name": "Server R740"}
    ]

    headers = {"Accept": "text/html"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/items", headers=headers)
    assert response.status_code == 200
    assert "Inventory Items" in response.text
    assert "Server R740" in response.text


@pytest.mark.asyncio
async def test_create_item(mock_db_resources):
    _, mock_cursor = mock_db_resources
    mock_cursor.lastrowid = 42

    payload = {"name": "Router Juniper", "quantity": 5}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/items", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 42
    assert data["name"] == "Router Juniper"
    assert data["quantity"] == 5


@pytest.mark.asyncio
async def test_get_item_details_success(mock_db_resources):
    import datetime
    _, mock_cursor = mock_db_resources
    mock_cursor.fetchone.return_value = {
        "id": 1,
        "name": "Server R740",
        "quantity": 3,
        "created_at": datetime.datetime(2026, 6, 15, 12, 0, 0)
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/items/1")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Server R740"
    assert data["quantity"] == 3


@pytest.mark.asyncio
async def test_get_item_details_html(mock_db_resources):
    import datetime
    _, mock_cursor = mock_db_resources
    mock_cursor.fetchone.return_value = {
        "id": 1,
        "name": "Server R740",
        "quantity": 3,
        "created_at": datetime.datetime(2026, 6, 15, 12, 0, 0)
    }

    headers = {"Accept": "text/html"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/items/1", headers=headers)
    assert response.status_code == 200
    assert "Item Details" in response.text
    assert "Server R740" in response.text


@pytest.mark.asyncio
async def test_get_item_details_not_found(mock_db_resources):
    _, mock_cursor = mock_db_resources
    mock_cursor.fetchone.return_value = None

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/items/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Item not found"
