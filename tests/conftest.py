"""Pytest bootstrap for the News Portal test-suite.

Everything here is intentionally deterministic and offline:

* The test SECRET_KEY is forced *before* ``app`` is imported so that
  ``utils.auth`` always picks it up (``load_dotenv`` never overrides an
  already-present environment variable).  Using a >= 32 byte key also keeps
  PyJWT from emitting ``InsecureKeyLengthWarning``.
* Tests never talk to a real PostgreSQL instance - every route test patches
  ``get_db_connection`` / ``db_cursor`` in the module under test.
"""

import datetime
import os
import sys

# --- must happen before ``app`` / ``utils.auth`` are imported -----------------
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest-only-0123456789abcdef"
os.environ.setdefault("FLASK_DEBUG", "False")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import jwt  # noqa: E402
import pytest  # noqa: E402

from app import app  # noqa: E402
from utils.auth import SECRET_KEY  # noqa: E402


def make_token(role="admin", user_id=1, expires_in_hours=1):
    """Create a real signed JWT usable by ``token_required``."""
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(hours=expires_in_hours),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


@pytest.fixture
def flask_app():
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(flask_app):
    with flask_app.test_client() as test_client:
        yield test_client


@pytest.fixture
def admin_token():
    return make_token(role="admin")


@pytest.fixture
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def editor_token():
    return make_token(role="editor")


@pytest.fixture
def editor_headers(editor_token):
    return {"Authorization": f"Bearer {editor_token}"}


@pytest.fixture
def expired_token():
    return make_token(role="admin", expires_in_hours=-1)


@pytest.fixture
def expired_headers(expired_token):
    return {"Authorization": f"Bearer {expired_token}"}
