import pytest


@pytest.fixture
def folder_user_headers(client):
    user_data = {
        "email": "folderuser@example.com",
        "password": "FolderPass123!"
    }
    
    client.post("/auth/register", json=user_data)
    response = client.post("/auth/login", json=user_data)
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}


def test_create_folder(client, folder_user_headers):
    response = client.post(
        "/folders",
        json={"name": "Documents"},
        headers=folder_user_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Documents"
    assert data["parent_folder_id"] is None


def test_create_nested_folder(client, folder_user_headers):
    parent_response = client.post(
        "/folders",
        json={"name": "Parent"},
        headers=folder_user_headers
    )
    parent_id = parent_response.json()["id"]
    
    response = client.post(
        "/folders",
        json={"name": "Child", "parent_folder_id": parent_id},
        headers=folder_user_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Child"
    assert data["parent_folder_id"] == parent_id


def test_get_folder_contents(client, folder_user_headers):
    folder_response = client.post(
        "/folders",
        json={"name": "TestFolder"},
        headers=folder_user_headers
    )
    folder_id = folder_response.json()["id"]
    
    response = client.get(
        f"/folders/{folder_id}",
        headers=folder_user_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "TestFolder"
    assert "subfolders" in data
    assert "files" in data


def test_rename_folder(client, folder_user_headers):
    folder_response = client.post(
        "/folders",
        json={"name": "OldName"},
        headers=folder_user_headers
    )
    folder_id = folder_response.json()["id"]
    
    response = client.patch(
        f"/folders/{folder_id}",
        json={"name": "NewName"},
        headers=folder_user_headers
    )
    
    assert response.status_code == 200
    assert response.json()["name"] == "NewName"


def test_delete_empty_folder(client, folder_user_headers):
    folder_response = client.post(
        "/folders",
        json={"name": "ToDelete"},
        headers=folder_user_headers
    )
    folder_id = folder_response.json()["id"]
    
    response = client.delete(
        f"/folders/{folder_id}",
        headers=folder_user_headers
    )
    
    assert response.status_code == 204


def test_delete_non_empty_folder(client, folder_user_headers):
    parent_response = client.post(
        "/folders",
        json={"name": "ParentToDelete"},
        headers=folder_user_headers
    )
    parent_id = parent_response.json()["id"]
    
    client.post(
        "/folders",
        json={"name": "ChildFolder", "parent_folder_id": parent_id},
        headers=folder_user_headers
    )
    
    response = client.delete(
        f"/folders/{parent_id}",
        headers=folder_user_headers
    )
    
    assert response.status_code == 400
    assert "not empty" in response.json()["detail"]


def test_folder_not_found(client, folder_user_headers):
    response = client.get(
        "/folders/99999",
        headers=folder_user_headers
    )
    
    assert response.status_code == 404


def test_folder_unauthorized(client):
    response = client.get("/folders/1")
    
    assert response.status_code == 403
