"""
Automated tests for Collab Docs.

Covers the core claims made in the architecture note:
  - Documents persist and reload with formatting intact
  - Access control: non-owners are blocked until sharing is granted
  - Sharing grants edit access, and can be revoked
  - Unsupported file uploads are rejected, not crashed on

Run with:  pytest
"""
import io
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from app import create_app
from extensions import db


@pytest.fixture
def app(tmp_path):
    db_path = tmp_path / "test.db"
    test_app = create_app(test_config={
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
    })
    yield test_app


@pytest.fixture
def alice_client(app):
    client = app.test_client()
    client.post("/login", data={"username": "alice", "password": "password123"},
                follow_redirects=True)
    return client


@pytest.fixture
def bob_client(app):
    client = app.test_client()
    client.post("/login", data={"username": "bob", "password": "password123"},
                follow_redirects=True)
    return client


def test_document_persists_with_formatting_after_reload(alice_client):
    """Core Task 1 + Task 4 claim: rich text formatting survives save/reload."""
    alice_client.post("/documents", follow_redirects=True)

    formatted_content = json.dumps({
        "ops": [
            {"insert": "Important Heading", "attributes": {"header": 1}},
            {"insert": "\n"},
            {"insert": "bold text", "attributes": {"bold": True}},
            {"insert": "\n"},
        ]
    })
    r = alice_client.patch("/api/documents/1", json={"content": formatted_content})
    assert r.status_code == 200

    r = alice_client.get("/documents/1")
    assert r.status_code == 200
    assert b"header" in r.data          # heading formatting preserved
    assert b"bold" in r.data            # bold formatting preserved


def test_non_owner_blocked_until_shared(alice_client, bob_client):
    """Core Task 3 claim: access control works before and after sharing."""
    alice_client.post("/documents", follow_redirects=True)

    r = bob_client.get("/documents/1")
    assert r.status_code == 403

    r = alice_client.post("/documents/1/share", data={"username": "bob"},
                          follow_redirects=True)
    assert b"Shared with" in r.data

    r = bob_client.get("/documents/1")
    assert r.status_code == 200

    r = bob_client.patch("/api/documents/1", json={"title": "Edited by Bob"})
    assert r.status_code == 200


def test_revoked_share_blocks_access_again(alice_client, bob_client):
    alice_client.post("/documents", follow_redirects=True)
    alice_client.post("/documents/1/share", data={"username": "bob"})

    assert bob_client.get("/documents/1").status_code == 200

    alice_client.post("/documents/1/share/2/revoke", follow_redirects=True)

    assert bob_client.get("/documents/1").status_code == 403


def test_unsupported_file_type_rejected_cleanly(alice_client):
    """Task 2 claim: bad uploads are rejected, not crashed on."""
    data = {"file": (io.BytesIO(b"not a real document"), "malware.exe")}
    r = alice_client.post("/documents/upload", data=data,
                          content_type="multipart/form-data",
                          follow_redirects=True)
    assert r.status_code == 200
    assert b"not supported" in r.data


def test_txt_upload_creates_editable_document(alice_client):
    data = {"file": (io.BytesIO(b"Line one.\nLine two.\n"), "notes.txt")}
    r = alice_client.post("/documents/upload", data=data,
                          content_type="multipart/form-data",
                          follow_redirects=True)
    assert r.status_code == 200
    assert b"Imported" in r.data
    assert b"Line one" in r.data