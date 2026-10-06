"""Guard tests for the static frontend that ships with the API.

The portal is served from plain files, so a broken script tag or a stray
selector typo silently breaks the whole page.  These tests fail fast when a
required asset disappears or when a known crash pattern creeps back in.
"""

import os

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FRONTEND = os.path.join(PROJECT_ROOT, "frontend")

REQUIRED_FILES = [
    "index.html",
    "login.html",
    "post.html",
    "admin.html",
    "page.html",
    os.path.join("js", "api.js"),
    os.path.join("js", "main.js"),
    os.path.join("js", "auth.js"),
    os.path.join("js", "post.js"),
    os.path.join("js", "admin.js"),
    os.path.join("js", "page.js"),
]


@pytest.mark.parametrize("relative_path", REQUIRED_FILES)
def test_frontend_file_exists(relative_path):
    assert os.path.isfile(os.path.join(FRONTEND, relative_path))


@pytest.mark.parametrize("script", ["main.js", "post.js", "admin.js", "page.js", "auth.js"])
def test_no_query_selector_on_document(script):
    """``$(document)`` resolves to ``null`` and crashes the page."""
    with open(os.path.join(FRONTEND, "js", script), encoding="utf-8") as handle:
        content = handle.read()

    assert "$(document)" not in content
