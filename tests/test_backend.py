"""End-to-end backend tests for the News Portal API.

These tests are fully deterministic and offline.  Instead of touching a real
PostgreSQL instance every route test swaps the module level
``get_db_connection`` (or ``db_cursor`` for auth) for a small fake that returns
*real* Python objects (``dict`` / ``list``).  Returning real objects is what
keeps Flask's JSON encoder happy - a bare ``MagicMock`` cannot be serialised
and was the original cause of ``TypeError: Object of type MagicMock is not
JSON serializable``.
"""

from io import BytesIO
from unittest.mock import patch

import bcrypt
import psycopg2
import pytest

from app import app as flask_app

POSTS_PATCH = "routes.post_routes.get_db_connection"
CATS_PATCH = "routes.category_routes.get_db_connection"
COMMENTS_PATCH = "routes.comment_routes.get_db_connection"
PRODUCTS_PATCH = "routes.product_routes.get_db_connection"
PAGES_PATCH = "routes.page_routes.get_db_connection"
AUTH_CURSOR_PATCH = "routes.auth_routes.db_cursor"


# --------------------------------------------------------------------------- #
# Fake database layer
# --------------------------------------------------------------------------- #
class FakeCursor:
    """Minimal stand-in for a psycopg2 cursor that yields real objects."""

    def __init__(
        self,
        fetchone=None,
        fetchall=None,
        fetchones=None,
        fetchalls=None,
        execute_raises=None,
        execute_raises_at=None,
    ):
        self._fetchone = fetchone
        self._fetchall = [] if fetchall is None else fetchall
        self._fetchones = list(fetchones) if fetchones is not None else None
        self._fetchalls = list(fetchalls) if fetchalls is not None else None
        self._execute_raises = execute_raises
        self._execute_raises_at = execute_raises_at
        self.executed = []
        self.closed = False

    def execute(self, query, params=None):
        index = len(self.executed)
        self.executed.append((query, params))
        if self._execute_raises is not None and (
            self._execute_raises_at is None or index == self._execute_raises_at
        ):
            raise self._execute_raises

    def fetchone(self):
        if self._fetchones:
            return self._fetchones.pop(0)
        return self._fetchone

    def fetchall(self):
        if self._fetchalls:
            return self._fetchalls.pop(0)
        return self._fetchall

    def close(self):
        self.closed = True

    # psycopg2 cursors can also be used as context managers
    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()
        return False


class FakeConnection:
    """Minimal stand-in for a psycopg2 connection."""

    def __init__(self, cursors=None):
        self._cursors = list(cursors or [])
        self.opened_cursors = []
        self.commit_count = 0
        self.rollback_count = 0
        self.closed = False

    def cursor(self, *args, **kwargs):  # accepts cursor_factory=...
        cursor = self._cursors.pop(0) if self._cursors else FakeCursor()
        self.opened_cursors.append(cursor)
        return cursor

    def commit(self):
        self.commit_count += 1

    def rollback(self):
        self.rollback_count += 1

    def close(self):
        self.closed = True


def conn_with(*cursors):
    return FakeConnection(list(cursors))


# --------------------------------------------------------------------------- #
# Auth: register / login (uses the db_cursor context manager)
# --------------------------------------------------------------------------- #
@patch(AUTH_CURSOR_PATCH)
def test_register_success(mock_db_cursor, client):
    cursor = FakeCursor(fetchone={"id": 1})
    mock_db_cursor.return_value.__enter__.return_value = cursor

    resp = client.post("/auth/register", json={"username": "newuser", "password": "password123"})

    assert resp.status_code == 201
    assert resp.get_json()["id"] == 1


@patch(AUTH_CURSOR_PATCH)
def test_register_duplicate_username(mock_db_cursor, client):
    cursor = FakeCursor(execute_raises=psycopg2.errors.UniqueViolation())
    mock_db_cursor.return_value.__enter__.return_value = cursor

    resp = client.post("/auth/register", json={"username": "dup", "password": "password123"})

    assert resp.status_code == 400
    assert "band" in resp.get_json()["message"]


@patch(AUTH_CURSOR_PATCH)
def test_register_db_connection_error(mock_db_cursor, client):
    mock_db_cursor.return_value.__enter__.side_effect = ConnectionError()

    resp = client.post("/auth/register", json={"username": "x", "password": "password123"})

    assert resp.status_code == 500


@patch(AUTH_CURSOR_PATCH)
def test_register_missing_fields(mock_db_cursor, client):
    resp = client.post("/auth/register", json={"username": "onlyusername"})

    assert resp.status_code == 400


@patch(AUTH_CURSOR_PATCH)
def test_login_success(mock_db_cursor, client):
    hashed = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8")
    cursor = FakeCursor(fetchone={"id": 1, "username": "admin", "password": hashed, "role": "admin"})
    mock_db_cursor.return_value.__enter__.return_value = cursor

    resp = client.post("/auth/login", json={"username": "admin", "password": "password123"})

    assert resp.status_code == 200
    assert resp.get_json()["token"]


@patch(AUTH_CURSOR_PATCH)
def test_login_wrong_password(mock_db_cursor, client):
    hashed = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8")
    cursor = FakeCursor(fetchone={"id": 1, "username": "admin", "password": hashed, "role": "admin"})
    mock_db_cursor.return_value.__enter__.return_value = cursor

    resp = client.post("/auth/login", json={"username": "admin", "password": "wrong"})

    assert resp.status_code == 401


@patch(AUTH_CURSOR_PATCH)
def test_login_unknown_user(mock_db_cursor, client):
    cursor = FakeCursor(fetchone=None)
    mock_db_cursor.return_value.__enter__.return_value = cursor

    resp = client.post("/auth/login", json={"username": "nobody", "password": "password123"})

    assert resp.status_code == 401


@patch(AUTH_CURSOR_PATCH)
def test_login_missing_fields(mock_db_cursor, client):
    resp = client.post("/auth/login", json={"username": "admin"})

    assert resp.status_code == 400


@patch(AUTH_CURSOR_PATCH)
def test_login_db_connection_error(mock_db_cursor, client):
    mock_db_cursor.return_value.__enter__.side_effect = ConnectionError()

    resp = client.post("/auth/login", json={"username": "admin", "password": "password123"})

    assert resp.status_code == 500


# --------------------------------------------------------------------------- #
# API index / swagger / static uploads
# --------------------------------------------------------------------------- #
def test_health_endpoint(client):
    resp = client.get("/health")

    assert resp.status_code == 200
    assert resp.get_json()["status"] == "active"


def test_web_app_root_serves_the_portal(client):
    """The bot's WebApp button opens `/`; it must be the portal, not status JSON."""
    resp = client.get("/")

    assert resp.status_code == 200
    assert "html" in resp.mimetype
    assert b"Yangiliklar Portali" in resp.data
    assert b"js/main.js" in resp.data
    resp.close()


@pytest.mark.parametrize("page", ["index.html", "login.html", "post.html", "admin.html", "page.html"])
def test_frontend_pages_are_served(client, page):
    resp = client.get(f"/{page}")

    assert resp.status_code == 200
    assert "html" in resp.mimetype
    assert b"<html" in resp.data.lower()
    resp.close()


@pytest.mark.parametrize("asset", ["api.js", "main.js", "auth.js", "post.js", "admin.js", "page.js"])
def test_frontend_js_is_served(client, asset):
    resp = client.get(f"/js/{asset}")

    assert resp.status_code == 200
    assert "javascript" in resp.mimetype
    assert resp.data
    resp.close()


def test_unknown_frontend_page_is_rejected(client):
    """The static route must be an allow-list, not an open file reader."""
    assert client.get("/secrets.html").status_code == 404
    assert client.get("/dostuff.html").status_code == 404


def test_swagger_yaml_is_served(client):
    resp = client.get("/static/swagger.yaml")

    assert resp.status_code == 200
    assert b"openapi" in resp.data or b"swagger" in resp.data
    resp.close()


def test_uploaded_file_served(flask_app, client, tmp_path):
    (tmp_path / "sample.png").write_bytes(b"png-bytes")
    old_folder = flask_app.config["UPLOAD_FOLDER"]
    flask_app.config["UPLOAD_FOLDER"] = str(tmp_path)
    try:
        resp = client.get("/uploads/sample.png")
        assert resp.status_code == 200
        assert resp.data == b"png-bytes"
        resp.close()
        missing = client.get("/uploads/nope.png")
        assert missing.status_code == 404
        missing.close()
    finally:
        flask_app.config["UPLOAD_FOLDER"] = old_folder


# --------------------------------------------------------------------------- #
# Posts
# --------------------------------------------------------------------------- #
@patch(POSTS_PATCH)
def test_posts_list_empty(mock_get, client):
    mock_get.return_value = conn_with(FakeCursor(fetchall=[]))

    resp = client.get("/api/posts")

    assert resp.status_code == 200
    assert resp.get_json() == []


@patch(POSTS_PATCH)
def test_posts_list_with_data(mock_get, client):
    rows = [
        {
            "id": 1,
            "title": "Salom",
            "content": "Matn",
            "category_id": 2,
            "category_name": "Sport",
            "image_url": None,
            "created_at": "2026-01-01T00:00:00",
        }
    ]
    conn = conn_with(FakeCursor(fetchall=rows))
    mock_get.return_value = conn

    resp = client.get("/api/posts")

    assert resp.status_code == 200
    assert resp.get_json()[0]["title"] == "Salom"
    assert conn.closed is True


@patch(POSTS_PATCH)
def test_posts_list_db_down(mock_get, client):
    mock_get.return_value = None

    resp = client.get("/api/posts")

    assert resp.status_code == 500


@patch(POSTS_PATCH)
def test_posts_list_title_filter_rejects_digits(mock_get, client):
    mock_get.return_value = conn_with(FakeCursor(fetchall=[]))

    resp = client.get("/api/posts?title=ab1")

    assert resp.status_code == 400


@patch(POSTS_PATCH)
def test_posts_list_title_filter_rejects_long_value(mock_get, client):
    mock_get.return_value = conn_with(FakeCursor(fetchall=[]))

    resp = client.get("/api/posts?title=abcd")

    assert resp.status_code == 400


@patch(POSTS_PATCH)
def test_posts_list_title_filter_ok(mock_get, client):
    mock_get.return_value = conn_with(FakeCursor(fetchall=[]))

    resp = client.get("/api/posts?title=abc")

    assert resp.status_code == 200


@patch(POSTS_PATCH)
def test_post_detail_success(mock_get, client):
    post = {
        "id": 1,
        "title": "Sarlavha",
        "content": "Matn",
        "image_url": None,
        "created_at": "2026-01-01T00:00:00",
        "category_name": "Sport",
    }
    comments = [{"id": 1, "post_id": 1, "text": "Ajoyib"}]
    mock_get.return_value = conn_with(FakeCursor(fetchone=post, fetchall=comments))

    resp = client.get("/api/posts/1")
    body = resp.get_json()

    assert resp.status_code == 200
    assert body["title"] == "Sarlavha"
    assert body["comment_count"] == 1


@patch(POSTS_PATCH)
def test_post_detail_not_found(mock_get, client):
    mock_get.return_value = conn_with(FakeCursor(fetchone=None))

    resp = client.get("/api/posts/999")

    assert resp.status_code == 404


@patch(POSTS_PATCH)
def test_post_detail_db_down(mock_get, client):
    mock_get.return_value = None

    resp = client.get("/api/posts/1")

    assert resp.status_code == 500


@patch(POSTS_PATCH)
def test_create_post_requires_token(mock_get, client):
    resp = client.post("/api/posts", json={"title": "Sarlavha", "content": "Matn", "category_id": 1})

    assert resp.status_code == 401
    mock_get.assert_not_called()


@patch(POSTS_PATCH)
def test_create_post_non_bearer_header(mock_get, client):
    resp = client.post(
        "/api/posts",
        json={"title": "Sarlavha", "content": "Matn", "category_id": 1},
        headers={"Authorization": "Basic abc"},
    )

    assert resp.status_code == 401


@patch(POSTS_PATCH)
def test_create_post_invalid_token(mock_get, client):
    resp = client.post(
        "/api/posts",
        json={"title": "Sarlavha", "content": "Matn", "category_id": 1},
        headers={"Authorization": "Bearer not.a.valid.jwt"},
    )

    assert resp.status_code == 401


@patch(POSTS_PATCH)
def test_create_post_expired_token(mock_get, expired_headers, client):
    resp = client.post(
        "/api/posts",
        json={"title": "Sarlavha", "content": "Matn", "category_id": 1},
        headers=expired_headers,
    )

    assert resp.status_code == 401


@patch(POSTS_PATCH)
def test_create_post_forbidden_role(mock_get, editor_headers, client):
    resp = client.post(
        "/api/posts",
        json={"title": "Sarlavha", "content": "Matn", "category_id": 1},
        headers=editor_headers,
    )

    assert resp.status_code == 403


@patch(POSTS_PATCH)
def test_create_post_validation_error(mock_get, auth_headers, client):
    resp = client.post("/api/posts", json={"title": "t"}, headers=auth_headers)

    assert resp.status_code == 400


@patch(POSTS_PATCH)
def test_create_post_non_numeric_category(mock_get, auth_headers, client):
    resp = client.post(
        "/api/posts",
        json={"title": "Sarlavha", "content": "Matn", "category_id": "abc"},
        headers=auth_headers,
    )

    assert resp.status_code == 400


@patch(POSTS_PATCH)
def test_create_post_unknown_category(mock_get, auth_headers, client):
    mock_get.return_value = conn_with(FakeCursor(fetchone=None))

    resp = client.post(
        "/api/posts",
        json={"title": "Sarlavha", "content": "Matn", "category_id": 999},
        headers=auth_headers,
    )

    assert resp.status_code == 400


@patch(POSTS_PATCH)
def test_create_post_success(mock_get, auth_headers, client):
    check_conn = conn_with(FakeCursor(fetchone={"id": 1}))
    insert_conn = conn_with(FakeCursor(fetchone={"id": 7, "created_at": "2026-01-01T00:00:00"}))
    mock_get.side_effect = [check_conn, insert_conn]

    resp = client.post(
        "/api/posts",
        json={"title": "Sarlavha", "content": "Matn", "category_id": 1},
        headers=auth_headers,
    )

    assert resp.status_code == 201
    assert resp.get_json()["post"]["id"] == 7
    assert insert_conn.commit_count == 1


@patch(POSTS_PATCH)
def test_create_post_db_down(mock_get, auth_headers, client):
    mock_get.return_value = None

    resp = client.post(
        "/api/posts",
        json={"title": "Sarlavha", "content": "Matn", "category_id": 1},
        headers=auth_headers,
    )

    assert resp.status_code == 500


@patch(POSTS_PATCH)
def test_update_post_requires_token(mock_get, client):
    resp = client.put("/api/posts/1", json={"title": "Yangi sarlavha"})

    assert resp.status_code == 401


@patch(POSTS_PATCH)
def test_update_post_empty_body(mock_get, auth_headers, client):
    resp = client.put("/api/posts/1", json={}, headers=auth_headers)

    assert resp.status_code == 400


@patch(POSTS_PATCH)
def test_update_post_success(mock_get, auth_headers, client):
    conn = conn_with(FakeCursor(fetchone={"id": 1}))
    mock_get.return_value = conn

    resp = client.put("/api/posts/1", json={"title": "Yangi sarlavha"}, headers=auth_headers)

    assert resp.status_code == 200
    assert conn.commit_count == 1


@patch(POSTS_PATCH)
def test_update_post_not_found(mock_get, auth_headers, client):
    mock_get.return_value = conn_with(FakeCursor(fetchone=None))

    resp = client.put("/api/posts/999", json={"title": "Yangi sarlavha"}, headers=auth_headers)

    assert resp.status_code == 404


@patch(POSTS_PATCH)
def test_update_post_unknown_category(mock_get, auth_headers, client):
    mock_get.return_value = conn_with(FakeCursor(fetchone=None))

    resp = client.put("/api/posts/1", json={"category_id": 999}, headers=auth_headers)

    assert resp.status_code == 400


@patch(POSTS_PATCH)
def test_delete_post_success(mock_get, auth_headers, client):
    conn = conn_with(FakeCursor(fetchone={"id": 1}))
    mock_get.return_value = conn

    resp = client.delete("/api/posts/1", headers=auth_headers)

    assert resp.status_code == 200
    assert conn.commit_count == 1


@patch(POSTS_PATCH)
def test_delete_post_not_found(mock_get, auth_headers, client):
    mock_get.return_value = conn_with(FakeCursor(fetchone=None))

    resp = client.delete("/api/posts/999", headers=auth_headers)

    assert resp.status_code == 404


@patch(POSTS_PATCH)
def test_delete_post_requires_token(mock_get, client):
    resp = client.delete("/api/posts/1")

    assert resp.status_code == 401


@patch(POSTS_PATCH)
def test_upload_post_image_requires_file(mock_get, auth_headers, client):
    resp = client.post("/api/posts/1/image", headers=auth_headers)

    assert resp.status_code == 400
    mock_get.assert_not_called()


@patch(POSTS_PATCH)
def test_upload_post_image_rejects_extension(mock_get, auth_headers, client):
    data = {"image": (BytesIO(b"data"), "evil.exe")}

    resp = client.post("/api/posts/1/image", headers=auth_headers, data=data, content_type="multipart/form-data")

    assert resp.status_code == 400


@patch(POSTS_PATCH)
def test_upload_post_image_post_not_found(mock_get, flask_app, auth_headers, client, tmp_path):
    flask_app.config["UPLOAD_FOLDER"] = str(tmp_path)
    mock_get.return_value = conn_with(FakeCursor(fetchone=None))

    resp = client.post(
        "/api/posts/999/image",
        headers=auth_headers,
        data={"image": (BytesIO(b"data"), "pic.png")},
        content_type="multipart/form-data",
    )
    resp.close()

    assert resp.status_code == 404


@patch(POSTS_PATCH)
def test_upload_post_image_success(mock_get, flask_app, auth_headers, client, tmp_path):
    flask_app.config["UPLOAD_FOLDER"] = str(tmp_path)
    conn = conn_with(FakeCursor(fetchones=[{"image_url": None}, {"id": 1}]))
    mock_get.return_value = conn

    resp = client.post(
        "/api/posts/1/image",
        headers=auth_headers,
        data={"image": (BytesIO(b"png-bytes"), "pic.png")},
        content_type="multipart/form-data",
    )

    assert resp.status_code == 200
    assert resp.get_json()["image_url"].startswith("/uploads/")
    assert len(list(tmp_path.iterdir())) == 1


# --------------------------------------------------------------------------- #
# Categories
# --------------------------------------------------------------------------- #
@patch(CATS_PATCH)
def test_categories_list_empty(mock_get, client):
    mock_get.return_value = conn_with(FakeCursor(fetchall=[]))

    resp = client.get("/api/categories")

    assert resp.status_code == 200
    assert resp.get_json() == []


@patch(CATS_PATCH)
def test_categories_list_with_data(mock_get, client):
    mock_get.return_value = conn_with(FakeCursor(fetchall=[{"id": 1, "name": "Sport"}]))

    resp = client.get("/api/categories")

    assert resp.status_code == 200
    assert resp.get_json()[0]["name"] == "Sport"


@patch(CATS_PATCH)
def test_categories_list_db_down(mock_get, client):
    mock_get.return_value = None

    resp = client.get("/api/categories")

    assert resp.status_code == 500


@patch(CATS_PATCH)
def test_create_category_requires_token(mock_get, client):
    resp = client.post("/api/categories", json={"name": "Sport"})

    assert resp.status_code == 401


@patch(CATS_PATCH)
def test_create_category_missing_name(mock_get, auth_headers, client):
    resp = client.post("/api/categories", json={}, headers=auth_headers)

    assert resp.status_code == 400


@patch(CATS_PATCH)
def test_create_category_success(mock_get, auth_headers, client):
    conn = conn_with(FakeCursor(fetchall=[], fetchone={"id": 1, "name": "Sport"}))
    mock_get.return_value = conn

    resp = client.post("/api/categories", json={"name": "Sport"}, headers=auth_headers)

    assert resp.status_code == 201
    assert resp.get_json()["category"]["name"] == "Sport"


@patch(CATS_PATCH)
def test_create_category_duplicate_slug(mock_get, auth_headers, client):
    conn = conn_with(FakeCursor(fetchall=[{"id": 1, "name": "Sport"}]))
    mock_get.return_value = conn

    resp = client.post("/api/categories", json={"name": "sport"}, headers=auth_headers)

    assert resp.status_code == 400


@patch(CATS_PATCH)
def test_create_category_unique_violation(mock_get, auth_headers, client):
    conn = conn_with(
        FakeCursor(fetchall=[], execute_raises=psycopg2.errors.UniqueViolation(), execute_raises_at=1)
    )
    mock_get.return_value = conn

    resp = client.post("/api/categories", json={"name": "Sport"}, headers=auth_headers)

    assert resp.status_code == 400
    assert conn.rollback_count == 1


@patch(CATS_PATCH)
def test_create_category_db_error(mock_get, auth_headers, client):
    conn = conn_with(FakeCursor(fetchall=[], execute_raises=Exception("boom"), execute_raises_at=1))
    mock_get.return_value = conn

    resp = client.post("/api/categories", json={"name": "Sport"}, headers=auth_headers)

    assert resp.status_code == 500


@patch(CATS_PATCH)
def test_update_category_requires_name(mock_get, auth_headers, client):
    resp = client.put("/api/categories/1", json={}, headers=auth_headers)

    assert resp.status_code == 400


@patch(CATS_PATCH)
def test_update_category_success(mock_get, auth_headers, client):
    conn = conn_with(FakeCursor(fetchall=[], fetchone={"id": 1, "name": "Yangi"}))
    mock_get.return_value = conn

    resp = client.put("/api/categories/1", json={"name": "Yangi"}, headers=auth_headers)

    assert resp.status_code == 200
    assert resp.get_json()["category"]["name"] == "Yangi"


@patch(CATS_PATCH)
def test_update_category_duplicate_slug(mock_get, auth_headers, client):
    conn = conn_with(FakeCursor(fetchall=[{"id": 2, "name": "Sport"}]))
    mock_get.return_value = conn

    resp = client.put("/api/categories/1", json={"name": "sport"}, headers=auth_headers)

    assert resp.status_code == 400


@patch(CATS_PATCH)
def test_update_category_not_found(mock_get, auth_headers, client):
    conn = conn_with(FakeCursor(fetchall=[], fetchone=None))
    mock_get.return_value = conn

    resp = client.put("/api/categories/999", json={"name": "Yangi"}, headers=auth_headers)

    assert resp.status_code == 404


@patch(CATS_PATCH)
def test_update_category_unique_violation(mock_get, auth_headers, client):
    conn = conn_with(
        FakeCursor(fetchall=[], execute_raises=psycopg2.errors.UniqueViolation(), execute_raises_at=1)
    )
    mock_get.return_value = conn

    resp = client.put("/api/categories/1", json={"name": "Yangi"}, headers=auth_headers)

    assert resp.status_code == 400


@patch(CATS_PATCH)
def test_delete_category_success(mock_get, auth_headers, client):
    conn = conn_with(FakeCursor(fetchone={"id": 1}))
    mock_get.return_value = conn

    resp = client.delete("/api/categories/1", headers=auth_headers)

    assert resp.status_code == 200
    assert conn.commit_count == 1


@patch(CATS_PATCH)
def test_delete_category_not_found(mock_get, auth_headers, client):
    mock_get.return_value = conn_with(FakeCursor(fetchone=None))

    resp = client.delete("/api/categories/999", headers=auth_headers)

    assert resp.status_code == 404


@patch(CATS_PATCH)
def test_delete_category_requires_token(mock_get, client):
    resp = client.delete("/api/categories/1")

    assert resp.status_code == 401


# --------------------------------------------------------------------------- #
# Comments
# --------------------------------------------------------------------------- #
@patch(COMMENTS_PATCH)
def test_comments_list_empty(mock_get, client):
    mock_get.return_value = conn_with(FakeCursor(fetchall=[]))

    resp = client.get("/api/comments")

    assert resp.status_code == 200
    assert resp.get_json() == []


@patch(COMMENTS_PATCH)
def test_comments_list_with_data(mock_get, client):
    rows = [{"id": 1, "post_id": 2, "text": "Zo'r"}]
    mock_get.return_value = conn_with(FakeCursor(fetchall=rows))

    resp = client.get("/api/comments")

    assert resp.status_code == 200
    assert resp.get_json() == rows


@patch(COMMENTS_PATCH)
def test_comments_list_db_down(mock_get, client):
    mock_get.return_value = None

    resp = client.get("/api/comments")

    assert resp.status_code == 500


@patch(COMMENTS_PATCH)
def test_create_comment_requires_token(mock_get, client):
    resp = client.post("/api/comments", json={"post_id": 1, "text": "Salom dunyo"})

    assert resp.status_code == 401


@patch(COMMENTS_PATCH)
def test_create_comment_missing_fields(mock_get, auth_headers, client):
    resp = client.post("/api/comments", json={"post_id": 1}, headers=auth_headers)

    assert resp.status_code == 400


@patch(COMMENTS_PATCH)
def test_create_comment_bad_post_id_type(mock_get, auth_headers, client):
    resp = client.post("/api/comments", json={"post_id": "x", "text": "Salom dunyo"}, headers=auth_headers)

    assert resp.status_code == 400


@patch(COMMENTS_PATCH)
def test_create_comment_text_too_short(mock_get, auth_headers, client):
    resp = client.post("/api/comments", json={"post_id": 1, "text": "Yo"}, headers=auth_headers)

    assert resp.status_code == 400


@patch(COMMENTS_PATCH)
def test_create_comment_text_too_long(mock_get, auth_headers, client):
    resp = client.post("/api/comments", json={"post_id": 1, "text": "a" * 1001}, headers=auth_headers)

    assert resp.status_code == 400


@patch(COMMENTS_PATCH)
def test_create_comment_post_not_found(mock_get, auth_headers, client):
    mock_get.return_value = conn_with(FakeCursor(fetchone=None))

    resp = client.post("/api/comments", json={"post_id": 999, "text": "Salom dunyo"}, headers=auth_headers)

    assert resp.status_code == 404


@patch(COMMENTS_PATCH)
def test_create_comment_success(mock_get, auth_headers, client):
    conn = conn_with(FakeCursor(fetchones=[{"id": 1}, {"id": 42}]))
    mock_get.return_value = conn

    resp = client.post("/api/comments", json={"post_id": 1, "text": "Salom dunyo"}, headers=auth_headers)

    assert resp.status_code == 201
    assert resp.get_json()["id"] == 42
    assert conn.commit_count == 1


# --------------------------------------------------------------------------- #
# Products
# --------------------------------------------------------------------------- #
def _product_row():
    return {
        "id": 1,
        "name": "Noutbuk",
        "description": "Yaxshi",
        "price": 10000,
        "image_url": None,
        "category_id": 2,
        "category_name": "Texnika",
        "created_at": "2026-01-01T00:00:00",
    }


@patch(PRODUCTS_PATCH)
def test_products_list_empty(mock_get, client):
    mock_get.return_value = conn_with(FakeCursor(fetchall=[]))

    resp = client.get("/api/products")

    assert resp.status_code == 200
    assert resp.get_json() == []


@patch(PRODUCTS_PATCH)
def test_products_list_with_data(mock_get, client):
    mock_get.return_value = conn_with(FakeCursor(fetchall=[_product_row()]))

    resp = client.get("/api/products")

    assert resp.status_code == 200
    assert resp.get_json()[0]["category"]["name"] == "Texnika"


@patch(PRODUCTS_PATCH)
def test_products_list_db_down(mock_get, client):
    mock_get.return_value = None

    resp = client.get("/api/products")

    assert resp.status_code == 500


@patch(PRODUCTS_PATCH)
def test_product_detail_success(mock_get, client):
    mock_get.return_value = conn_with(FakeCursor(fetchone=_product_row()))

    resp = client.get("/api/products/1")

    assert resp.status_code == 200
    assert resp.get_json()["name"] == "Noutbuk"


@patch(PRODUCTS_PATCH)
def test_product_detail_not_found(mock_get, client):
    mock_get.return_value = conn_with(FakeCursor(fetchone=None))

    resp = client.get("/api/products/999")

    assert resp.status_code == 404


@patch(PRODUCTS_PATCH)
def test_create_product_requires_token(mock_get, client):
    resp = client.post("/api/products", json={"name": "Noutbuk", "price": 100, "category_id": 1})

    assert resp.status_code == 401


@patch(PRODUCTS_PATCH)
def test_create_product_forbidden_role(mock_get, editor_headers, client):
    resp = client.post(
        "/api/products",
        json={"name": "Noutbuk", "price": 100, "category_id": 1},
        headers=editor_headers,
    )

    assert resp.status_code == 403


@patch(PRODUCTS_PATCH)
def test_create_product_validation_error(mock_get, auth_headers, client):
    resp = client.post("/api/products", json={"name": "N"}, headers=auth_headers)

    assert resp.status_code == 400


@patch(PRODUCTS_PATCH)
def test_create_product_unknown_category(mock_get, auth_headers, client):
    mock_get.return_value = conn_with(FakeCursor(fetchone=None))

    resp = client.post(
        "/api/products",
        json={"name": "Noutbuk", "price": 100, "category_id": 999},
        headers=auth_headers,
    )

    assert resp.status_code == 400


@patch(PRODUCTS_PATCH)
def test_create_product_success(mock_get, auth_headers, client):
    conn = conn_with(FakeCursor(fetchones=[{"id": 2}, {"id": 5}]))
    mock_get.return_value = conn

    resp = client.post(
        "/api/products",
        json={"name": "Noutbuk", "price": 10000, "category_id": 2},
        headers=auth_headers,
    )

    assert resp.status_code == 201
    assert resp.get_json()["id"] == 5
    assert conn.commit_count == 1


@patch(PRODUCTS_PATCH)
def test_create_product_db_down(mock_get, auth_headers, client):
    mock_get.return_value = None

    resp = client.post(
        "/api/products",
        json={"name": "Noutbuk", "price": 10000, "category_id": 2},
        headers=auth_headers,
    )

    assert resp.status_code == 500


@patch(PRODUCTS_PATCH)
def test_update_product_requires_token(mock_get, client):
    resp = client.put("/api/products/1", json={"name": "Yangi nom"})

    assert resp.status_code == 401


@patch(PRODUCTS_PATCH)
def test_update_product_empty_body(mock_get, auth_headers, client):
    resp = client.put("/api/products/1", json={}, headers=auth_headers)

    assert resp.status_code == 400


@patch("routes.product_routes.notify_product")
@patch(PRODUCTS_PATCH)
def test_update_product_success(mock_get, mock_notify, auth_headers, client):
    conn = conn_with(FakeCursor(fetchones=[{"id": 1}, _product_row()]))
    mock_get.return_value = conn

    resp = client.put("/api/products/1", json={"name": "Yangi nom"}, headers=auth_headers)

    assert resp.status_code == 200
    assert conn.commit_count == 1
    mock_notify.assert_called_once()


@patch(PRODUCTS_PATCH)
def test_update_product_unknown_category(mock_get, auth_headers, client):
    mock_get.return_value = conn_with(FakeCursor(fetchone=None))

    resp = client.put("/api/products/1", json={"category_id": 999}, headers=auth_headers)

    assert resp.status_code == 400


@patch(PRODUCTS_PATCH)
def test_update_product_not_found(mock_get, auth_headers, client):
    mock_get.return_value = conn_with(FakeCursor(fetchone=None))

    resp = client.put("/api/products/999", json={"name": "Yangi nom"}, headers=auth_headers)

    assert resp.status_code == 404


@patch(PRODUCTS_PATCH)
def test_update_product_db_down(mock_get, auth_headers, client):
    mock_get.return_value = None

    resp = client.put("/api/products/1", json={"name": "Yangi nom"}, headers=auth_headers)

    assert resp.status_code == 500


@patch(PRODUCTS_PATCH)
def test_upload_product_image_requires_file(mock_get, auth_headers, client):
    resp = client.post("/api/products/1/image", headers=auth_headers)

    assert resp.status_code == 400
    mock_get.assert_not_called()


@patch(PRODUCTS_PATCH)
def test_upload_product_image_not_found(mock_get, auth_headers, client):
    mock_get.return_value = conn_with(FakeCursor(fetchone=None))

    resp = client.post(
        "/api/products/999/image",
        headers=auth_headers,
        data={"image": (BytesIO(b"data"), "pic.png")},
        content_type="multipart/form-data",
    )

    assert resp.status_code == 404


@patch("routes.product_routes.notify_product")
@patch(PRODUCTS_PATCH)
def test_upload_product_image_success(mock_get, mock_notify, flask_app, auth_headers, client, tmp_path):
    flask_app.config["UPLOAD_FOLDER"] = str(tmp_path)
    conn = conn_with(FakeCursor(fetchones=[{"id": 1}, _product_row()]))
    mock_get.return_value = conn

    resp = client.post(
        "/api/products/1/image",
        headers=auth_headers,
        data={"image": (BytesIO(b"png-bytes"), "pic.png")},
        content_type="multipart/form-data",
    )

    assert resp.status_code == 200
    assert resp.get_json()["image_url"].startswith("/uploads/")
    mock_notify.assert_called_once()


@patch(PRODUCTS_PATCH)
def test_upload_product_image_db_down(mock_get, auth_headers, client):
    mock_get.return_value = None

    resp = client.post(
        "/api/products/1/image",
        headers=auth_headers,
        data={"image": (BytesIO(b"data"), "pic.png")},
        content_type="multipart/form-data",
    )

    assert resp.status_code == 500


def test_delete_product_not_allowed(client):
    resp = client.delete("/api/products/1")

    assert resp.status_code == 405


# --------------------------------------------------------------------------- #
# Pages
# --------------------------------------------------------------------------- #
@patch(PAGES_PATCH)
def test_pages_list(mock_get, client):
    mock_get.return_value = conn_with(FakeCursor(fetchall=[{"id": 1, "title": "Haqida", "content": "x", "slug": "about"}]))

    resp = client.get("/api/pages")

    assert resp.status_code == 200
    assert resp.get_json()[0]["slug"] == "about"


@patch(PAGES_PATCH)
def test_pages_list_db_down(mock_get, client):
    mock_get.return_value = None

    resp = client.get("/api/pages")

    assert resp.status_code == 500


@patch(PAGES_PATCH)
def test_create_page_requires_token(mock_get, client):
    resp = client.post("/api/pages", json={"title": "Haqida", "content": "x", "slug": "about"})

    assert resp.status_code == 401


@patch(PAGES_PATCH)
def test_create_page_validation_error(mock_get, auth_headers, client):
    resp = client.post("/api/pages", json={"title": "Haqida"}, headers=auth_headers)

    assert resp.status_code == 400


@patch(PAGES_PATCH)
def test_create_page_success(mock_get, auth_headers, client):
    mock_get.return_value = conn_with(FakeCursor(fetchone={"id": 1}))

    resp = client.post(
        "/api/pages",
        json={"title": "Haqida", "content": "Salom", "slug": "about"},
        headers=auth_headers,
    )

    assert resp.status_code == 201
    assert resp.get_json()["page"]["id"] == 1


@patch(PAGES_PATCH)
def test_create_page_duplicate_slug(mock_get, auth_headers, client):
    conn = conn_with(FakeCursor(execute_raises=psycopg2.errors.UniqueViolation()))
    mock_get.return_value = conn

    resp = client.post(
        "/api/pages",
        json={"title": "Haqida", "content": "Salom", "slug": "about"},
        headers=auth_headers,
    )

    assert resp.status_code == 400
    assert conn.rollback_count == 1


@patch(PAGES_PATCH)
def test_update_page_empty_body(mock_get, auth_headers, client):
    resp = client.put("/api/pages/1", json={}, headers=auth_headers)

    assert resp.status_code == 400


@patch(PAGES_PATCH)
def test_update_page_success(mock_get, auth_headers, client):
    conn = conn_with(FakeCursor(fetchone={"id": 1}))
    mock_get.return_value = conn

    resp = client.put("/api/pages/1", json={"title": "Yangi"}, headers=auth_headers)

    assert resp.status_code == 200
    assert conn.commit_count == 1


@patch(PAGES_PATCH)
def test_update_page_not_found(mock_get, auth_headers, client):
    mock_get.return_value = conn_with(FakeCursor(fetchone=None))

    resp = client.put("/api/pages/999", json={"title": "Yangi"}, headers=auth_headers)

    assert resp.status_code == 404
