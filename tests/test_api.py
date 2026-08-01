import pytest

from app import create_app, db


class TestConfig:
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "test"
    SHORT_CODE_LENGTH = 6


@pytest.fixture
def client():
    app = create_app(config_object=TestConfig)
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()


def test_shorten_rejects_invalid_url(client):
    res = client.post("/api/shorten", json={"long_url": "not-a-url"})
    assert res.status_code == 400


def test_shorten_creates_short_link(client):
    res = client.post("/api/shorten", json={"long_url": "https://example.com/some/long/path"})
    assert res.status_code == 201
    body = res.get_json()
    assert "short_code" in body
    assert len(body["short_code"]) == 6


def test_custom_alias_conflict(client):
    client.post("/api/shorten", json={"long_url": "https://example.com/a", "custom_alias": "myalias"})
    res = client.post("/api/shorten", json={"long_url": "https://example.com/b", "custom_alias": "myalias"})
    assert res.status_code == 409


def test_invalid_alias_format_rejected(client):
    res = client.post("/api/shorten", json={"long_url": "https://example.com/a", "custom_alias": "a"})
    assert res.status_code == 400


def test_redirect_follows_short_link(client):
    create_res = client.post("/api/shorten", json={"long_url": "https://example.com/target"})
    short_code = create_res.get_json()["short_code"]

    res = client.get(f"/{short_code}", follow_redirects=False)
    assert res.status_code == 302
    assert res.headers["Location"] == "https://example.com/target"


def test_unknown_short_code_returns_404(client):
    res = client.get("/doesnotexist")
    assert res.status_code == 404


def test_stats_tracks_click_count(client):
    create_res = client.post("/api/shorten", json={"long_url": "https://example.com/target"})
    short_code = create_res.get_json()["short_code"]

    client.get(f"/{short_code}")
    client.get(f"/{short_code}")

    stats_res = client.get(f"/api/stats/{short_code}")
    assert stats_res.status_code == 200
    assert stats_res.get_json()["click_count"] == 2


def test_short_codes_are_unique_and_deterministic(client):
    codes = set()
    for i in range(5):
        res = client.post("/api/shorten", json={"long_url": f"https://example.com/page-{i}"})
        codes.add(res.get_json()["short_code"])
    assert len(codes) == 5


def test_list_links_is_paginated(client):
    for i in range(3):
        client.post("/api/shorten", json={"long_url": f"https://example.com/page-{i}"})

    res = client.get("/api/links?page=1&per_page=2")
    assert res.status_code == 200
    body = res.get_json()
    assert len(body["links"]) == 2
    assert body["total"] == 3
    assert body["has_next"] is True

    res_page_2 = client.get("/api/links?page=2&per_page=2")
    assert len(res_page_2.get_json()["links"]) == 1
    assert res_page_2.get_json()["has_next"] is False


def test_delete_link_removes_it(client):
    create_res = client.post("/api/shorten", json={"long_url": "https://example.com/target"})
    short_code = create_res.get_json()["short_code"]

    del_res = client.delete(f"/api/links/{short_code}")
    assert del_res.status_code == 204

    res = client.get(f"/{short_code}")
    assert res.status_code == 404


def test_delete_unknown_link_returns_404(client):
    res = client.delete("/api/links/doesnotexist")
    assert res.status_code == 404


def test_expired_link_returns_410(client):
    create_res = client.post("/api/shorten", json={
        "long_url": "https://example.com/target",
        "expires_in_days": -1,
    })
    short_code = create_res.get_json()["short_code"]

    res = client.get(f"/{short_code}")
    assert res.status_code == 410
