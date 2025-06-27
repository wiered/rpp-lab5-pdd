import pytest
from aioresponses import aioresponses
import aiohttp

from src import AsyncApiClient

@pytest.fixture
async def client(event_loop):
    base_url = "http://localhost:8083"
    client = AsyncApiClient(base_url)
    yield client
    # cleanup
    if client.session and not client.session.closed:
        await client.close()

@pytest.mark.asyncio
async def test_set_token_and_headers(client):
    # Ensure set_token updates the Authorization header correctly
    token = "testtoken123"
    client.set_token(token)
    assert client.token == token
    assert client.headers["Authorization"] == f"Bearer {token}"

@pytest.mark.asyncio
async def test_authenticate(client):
    username = "a"
    password = "a"
    with aioresponses() as m:
        m.post(f"{client.base_url}/api/auth/login", payload={"access_token": "testtoken123"})
        token_data = await client.login(username, password)
        assert token_data == {"access_token": "testtoken123"}
        assert client.token == "testtoken123"

@pytest.mark.asyncio
async def test_list_articles(client):
    expected = [{"id": 1, "title": "Test Article", "content": "Hello", "content_type": "markdown"}]
    with aioresponses() as m:
        m.get(f"{client.base_url}/articles", payload=expected)
        result = await client.list_articles()
        assert result == expected

@pytest.mark.asyncio
async def test_get_article(client):
    article_id = 42
    expected = {"id": article_id, "title": "Article 42", "content": "Content", "content_type": "html"}
    with aioresponses() as m:
        m.get(f"{client.base_url}/articles/{article_id}", payload=expected)
        result = await client.get_article(article_id)
        assert result == expected

@pytest.mark.asyncio
async def test_create_article(client):
    payload = {
        "category_id": 5,
        "title": "New Article",
        "content": "Lorem ipsum",
        "content_type": "markdown"
    }
    response = {**payload, "id": 99}
    with aioresponses() as m:
        m.post(f"{client.base_url}/articles", payload=response, status=201)
        result = await client.create_article(**payload)
        assert result == response

@pytest.mark.asyncio
async def test_update_article(client):
    article_id = 7
    updates = {"title": "Updated Title", "content": "Updated Content"}
    response = {"id": article_id, **updates, "content_type": "markdown"}
    with aioresponses() as m:
        m.put(f"{client.base_url}/articles/{article_id}", payload=response)
        result = await client.update_article(article_id, **updates)
        assert result == response

@pytest.mark.asyncio
async def test_delete_article(client):
    article_id = 3
    with aioresponses() as m:
        m.delete(f"{client.base_url}/articles/{article_id}", status=204)
        result = await client.delete_article(article_id)
        assert result is None

@pytest.mark.asyncio
async def test_login_and_me(client):
    # Mock login response
    login_data = {"access_token": "abc123"}
    with aioresponses() as m:
        m.post(f"{client.base_url}/auth/login", payload=login_data)
        token_data = await client.login("user1", "pass1")
        assert token_data == login_data
        assert client.token == login_data["access_token"]

        # Mock me response
        me_data = {"id": 1, "username": "user1"}
        m.get(f"{client.base_url}/auth/me", payload=me_data)
        user_info = await client.me()
        assert user_info == me_data

@pytest.mark.asyncio
async def test_list_assignments_with_filters(client):
    expected = [{"id": 1, "user_id": 2, "group_id": None, "category_id": 3}]
    with aioresponses() as m:
        m.get(f"{client.base_url}/assignments?user_id=2&category_id=3", payload=expected)
        result = await client.list_assignments(user_id=2, category_id=3)
        assert result == expected
