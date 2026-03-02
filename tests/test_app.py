from copy import deepcopy
import pytest

from fastapi.testclient import TestClient

from src import app as app_module

client = TestClient(app_module.app)

# keep a pristine copy of the original activities state
ORIGINAL_ACTIVITIES = deepcopy(app_module.activities)


def reset_activities():
    """Restore activities dict to its original contents.
    Called before each test to avoid state bleed.
    """
    app_module.activities.clear()
    app_module.activities.update(deepcopy(ORIGINAL_ACTIVITIES))


@pytest.fixture(autouse=True)
def activity_fixture():
    # runs before each test automatically
    reset_activities()
    yield
    # (no teardown needed beyond automatic reset)


def test_get_activities_returns_all():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # check a known activity exists
    assert "Chess Club" in data


def test_signup_successful():
    resp = client.post("/activities/Chess%20Club/signup?email=test@mergington.edu")
    assert resp.status_code == 200
    assert "Signed up test@mergington.edu" in resp.json()["message"]
    assert "test@mergington.edu" in app_module.activities["Chess Club"]["participants"]


def test_signup_duplicate():
    # michael already registered in initial state
    resp = client.post("/activities/Chess%20Club/signup?email=michael@mergington.edu")
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Student is already signed up"


def test_signup_nonexistent_activity():
    resp = client.post("/activities/Nonexistent/signup?email=foo@bar.com")
    assert resp.status_code == 404


def test_signup_full_activity():
    # fill up a small activity artificially
    activity = app_module.activities["Chess Club"]
    activity["participants"] = [f"u{i}@x.com" for i in range(activity["max_participants"])]
    resp = client.post("/activities/Chess%20Club/signup?email=new@x.com")
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Activity is full"


def test_remove_participant_success():
    resp = client.delete("/activities/Chess%20Club/participants?email=michael@mergington.edu")
    assert resp.status_code == 200
    assert "Removed michael@mergington.edu" in resp.json()["message"]
    assert "michael@mergington.edu" not in app_module.activities["Chess Club"]["participants"]


def test_remove_nonexistent_participant():
    resp = client.delete("/activities/Chess%20Club/participants?email=ghost@x.com")
    assert resp.status_code == 404


def test_remove_from_nonexistent_activity():
    resp = client.delete("/activities/Nope/participants?email=foo@bar.com")
    assert resp.status_code == 404
