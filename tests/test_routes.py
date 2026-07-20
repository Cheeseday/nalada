"""
Route/view tests through the Flask test client - in-process, no browser.

The whole render pipeline runs on each request: URL routing -> view -> data_service
-> the build_* chart functions -> Jinja templates -> base.html. A 200 with the
expected marker means the chain assembled; a broken chart builder or template
surfaces here as a 500 or missing text, in milliseconds.

The unknown-slug 404 and the devtools probe short-circuit before any data call, so
they're plain unit tests. Every 200 page pulls live queries, so those are marked
`integration` and skip when Postgres is down (see conftest).
"""
import pytest

from app import create_app


@pytest.fixture(scope="module")
def client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


# --- Unit: routing contract, no database ---
def test_unknown_chapter_returns_404(client):
    # chapter() calls abort(404) before touching data_service.
    assert client.get("/chapters/does-not-exist").status_code == 404


def test_devtools_probe_returns_204(client):
    assert client.get("/.well-known/appspecific/com.chrome.devtools.json").status_code == 204


# --- Integration: full render pipeline ---
CHAPTER_MARKERS = [
    ("context",     b"Context"),
    ("decoupling",  b"Decoupling"),
    ("structure",   b"Structure"),
    ("synthesis",   b"Synthesis"),
    ("methodology", b"Methodology"),
]


@pytest.mark.integration
def test_index_renders(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Nalada" in resp.data


@pytest.mark.integration
@pytest.mark.parametrize("slug, marker", CHAPTER_MARKERS, ids=[s for s, _ in CHAPTER_MARKERS])
def test_chapter_renders(client, slug, marker):
    resp = client.get(f"/chapters/{slug}")
    assert resp.status_code == 200
    assert marker in resp.data
