import base64
import pytest


@pytest.fixture
def file_user_headers(client):
    user_data = {
        "email": "fileuser@example.com",
        "password": "FilePass123!"
    }
    
    client.post("/auth/register", json=user_data)
    response = client.post("/auth/login", json=user_data)
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}


def test_upload_file(client, file_user_headers):
    content = base64.b64encode(b"Hello, World!").decode()
    
    response = client.post(
        "/files",
        json={
            "name": "hello.txt",
            "content": content
        },
        headers=file_user_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "hello.txt"
    assert data["size"] == 13
    assert data["mime_type"] == "text/plain"


def test_upload_file_to_folder(client, file_user_headers):
    folder_response = client.post(
        "/folders",
        json={"name": "FileFolder"},
        headers=file_user_headers
    )
    folder_id = folder_response.json()["id"]
    
    content = base64.b64encode(b"File content").decode()
    
    response = client.post(
        "/files",
        json={
            "name": "document.txt",
            "content": content,
            "parent_folder_id": folder_id
        },
        headers=file_user_headers
    )
    
    assert response.status_code == 201
    assert response.json()["parent_folder_id"] == folder_id


def test_get_file_metadata(client, file_user_headers):
    content = base64.b64encode(b"Test content").decode()
    
    create_response = client.post(
        "/files",
        json={"name": "metadata.txt", "content": content},
        headers=file_user_headers
    )
    file_id = create_response.json()["id"]
    
    response = client.get(
        f"/files/{file_id}",
        headers=file_user_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "metadata.txt"
    assert data["size"] == 12


def test_download_file(client, file_user_headers):
    original_content = b"Download test content"
    content = base64.b64encode(original_content).decode()
    
    create_response = client.post(
        "/files",
        json={"name": "download.txt", "content": content},
        headers=file_user_headers
    )
    file_id = create_response.json()["id"]
    
    response = client.get(
        f"/files/{file_id}/download",
        headers=file_user_headers
    )
    
    assert response.status_code == 200
    assert response.content == original_content


def test_rename_file(client, file_user_headers):
    content = base64.b64encode(b"Rename test").decode()
    
    create_response = client.post(
        "/files",
        json={"name": "oldname.txt", "content": content},
        headers=file_user_headers
    )
    file_id = create_response.json()["id"]
    
    response = client.patch(
        f"/files/{file_id}",
        json={"name": "newname.pdf"},
        headers=file_user_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "newname.pdf"
    assert data["mime_type"] == "application/pdf"


def test_delete_file(client, file_user_headers):
    content = base64.b64encode(b"Delete test").decode()
    
    create_response = client.post(
        "/files",
        json={"name": "todelete.txt", "content": content},
        headers=file_user_headers
    )
    file_id = create_response.json()["id"]
    
    response = client.delete(
        f"/files/{file_id}",
        headers=file_user_headers
    )
    
    assert response.status_code == 204
    
    get_response = client.get(
        f"/files/{file_id}",
        headers=file_user_headers
    )
    assert get_response.status_code == 404


def test_invalid_base64_content(client, file_user_headers):
    response = client.post(
        "/files",
        json={
            "name": "invalid.txt",
            "content": "not-valid-base64!!!"
        },
        headers=file_user_headers
    )
    
    assert response.status_code == 400
    assert "Invalid base64" in response.json()["detail"]


def test_file_not_found(client, file_user_headers):
    response = client.get(
        "/files/99999",
        headers=file_user_headers
    )
    
    assert response.status_code == 404


def test_file_unauthorized(client):
    response = client.get("/files/1")
    
    assert response.status_code == 403
