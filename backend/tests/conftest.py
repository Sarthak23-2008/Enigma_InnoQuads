import os
import sys
import tempfile

_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["JWT_SECRET"] = "test-secret-not-for-production-0123456789"
os.environ["APP_ENV"] = "test"
os.environ["DEMO_MODE"] = "true"
os.environ.setdefault("OCR_PROVIDER", "tesseract")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def new_user(client):
    import uuid
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/api/auth/register", json={"name": "Test User", "email": email, "password": "Passw0rdX",
                                                "confirm_password": "Passw0rdX"})
    assert r.status_code == 201, r.text
    tok = r.json()["access_token"]
    return {"email": email, "password": "Passw0rdX", "headers": {"Authorization": f"Bearer {tok}", "X-Timezone": "Asia/Kolkata"}}


@pytest.fixture()
def demo_headers(client):
    r = client.post("/api/auth/demo")
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}", "X-Timezone": "Asia/Kolkata"}
