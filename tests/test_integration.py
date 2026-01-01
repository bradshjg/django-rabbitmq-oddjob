import time
from urllib.parse import urlparse

import pytest

@pytest.fixture
def user1_client(client, django_user_model):
    username = "user1"
    user = django_user_model.objects.create_user(username=username, password="password")
    client.force_login(user)
    yield client

@pytest.fixture
def user2_client(client, django_user_model):
    username = "user2"
    user = django_user_model.objects.create_user(username=username, password="password")
    client.force_login(user)
    yield client


def test_run_add_sync_returns_result_immediately(client):
    resp = client.get("/run_add_sync/")

    expected_result = {'x': 1, 'y': 2, 'sum': 3}
    assert resp.json() == expected_result

def test_launch_add_task_result_returns_result_url(client):
    launch_resp = client.get("/launch_add_task/")

    assert launch_resp.status_code == 200
    result_url = launch_resp.json()["result_url"]
    parsed_url = urlparse(result_url)
    assert parsed_url.netloc == "testserver"

    result_path = parsed_url.path

    time.sleep(1)  # Wait for the background task to complete
    result_resp = client.get(result_path)

    assert result_resp.status_code == 200
    expected_result = {'x': 1, 'y': 2, 'sum': 3}
    assert result_resp.json() == expected_result

def test_launch_add_task_result_returns_204_if_task_is_processing(client):
    launch_resp = client.get("/launch_add_task/?sleep=1")

    assert launch_resp.status_code == 200
    result_url = launch_resp.json()["result_url"]
    parsed_url = urlparse(result_url)
    assert parsed_url.netloc == "testserver"

    result_path = parsed_url.path

    result_resp = client.get(result_path)

    assert result_resp.status_code == 204

def test_launch_add_task_result_only_returns_result_to_launching_user_by_default(client, django_user_model):
    user1 = django_user_model.objects.create_user(username="user1", password="password")
    user2 = django_user_model.objects.create_user(username="user2", password="password")

    # launch task as user1
    client.force_login(user1)
    launch_resp = client.get("/launch_add_task/")

    assert launch_resp.status_code == 200
    result_url = launch_resp.json()["result_url"]
    parsed_url = urlparse(result_url)
    assert parsed_url.netloc == "testserver"

    result_path = parsed_url.path

    time.sleep(1)  # Wait for the background task to complete

    # try to get result as user2
    client.force_login(user2)
    user2_result_resp = client.get(result_path)
    assert user2_result_resp.status_code == 404

    # try and get result as anonymous user
    client.logout()
    anon_result_resp = client.get(result_path)
    assert anon_result_resp.status_code == 404

    # get result as user1
    client.force_login(user1)
    user1_result_resp = client.get(result_path)

    assert user1_result_resp.status_code == 200
    expected_result = {'x': 1, 'y': 2, 'sum': 3}
    assert user1_result_resp.json() == expected_result


def test_launch_add_task_result_can_be_made_public(client, django_user_model):
    user1 = django_user_model.objects.create_user(username="user1", password="password")
    user2 = django_user_model.objects.create_user(username="user2", password="password")

    # launch task as user1
    client.force_login(user1)
    launch_resp = client.get("/launch_add_task/?public=true")

    assert launch_resp.status_code == 200
    result_url = launch_resp.json()["result_url"]
    parsed_url = urlparse(result_url)
    assert parsed_url.netloc == "testserver"

    result_path = parsed_url.path

    time.sleep(1)  # Wait for the background task to complete

    # get result as user2
    client.force_login(user2)
    user2_result_resp = client.get(result_path)
    assert user2_result_resp.status_code == 200
    expected_result = {'x': 1, 'y': 2, 'sum': 3}
    assert user2_result_resp.json() == expected_result
