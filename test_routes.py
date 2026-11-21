"""Tests for the Flask routes in app.py."""
import re
from io import BytesIO

from PIL import Image


def make_png():
    """Return an in-memory file containing a tiny valid PNG image."""
    buffer = BytesIO()
    Image.new("RGB", (10, 10), (255, 255, 255)).save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def get_csrf_token(client):
    """Load the home page and return the CSRF token from the upload form."""
    page = client.get("/").data.decode()
    match = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', page)
    assert match, "The upload form should contain a CSRF token"
    return match.group(1)


def test_home_page_loads(client):
    """The home page returns 200 and shows the app title."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Hand Sign Digit" in response.data


def test_valid_upload_shows_prediction(client, monkeypatch):
    """A valid image produces a page showing the predicted digit."""
    monkeypatch.setattr("app.predict_result", lambda _img: 7)
    response = client.post(
        "/prediction",
        data={"file": (make_png(), "digit.png"), "csrf_token": get_csrf_token(client)},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    assert b'font-weight-bold">7</h2>' in response.data
    assert b"File cannot be processed" not in response.data


def test_missing_file_is_handled(client):
    """A request with no uploaded file shows the error message."""
    response = client.post(
        "/prediction",
        data={"csrf_token": get_csrf_token(client)},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    assert b"File cannot be processed" in response.data


def test_non_image_file_is_handled(client):
    """A file that is not an image shows the error message."""
    response = client.post(
        "/prediction",
        data={
            "file": (BytesIO(b"this is not an image"), "invalid_file.txt"),
            "csrf_token": get_csrf_token(client),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    assert b"File cannot be processed" in response.data


def test_prediction_rejects_get_requests(client):
    """The prediction route only accepts POST."""
    response = client.get("/prediction")
    assert response.status_code == 405


def test_upload_without_csrf_token_is_rejected(client):
    """A POST without a CSRF token is refused before the image is processed."""
    response = client.post(
        "/prediction",
        data={"file": (make_png(), "digit.png")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    assert b"CSRF token is missing" in response.data
