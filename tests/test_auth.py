def test_register_success(client):
    response = client.post("/auth/register", json={
        "email": "newuser@example.com",
        "password": "ValidPass123!"
    })
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data


def test_register_duplicate_email(client):
    user_data = {
        "email": "duplicate@example.com",
        "password": "ValidPass123!"
    }
    
    client.post("/auth/register", json=user_data)
    response = client.post("/auth/register", json=user_data)
    
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_register_weak_password(client):
    response = client.post("/auth/register", json={
        "email": "weak@example.com",
        "password": "weak"
    })
    
    assert response.status_code == 422


def test_register_password_no_uppercase(client):
    response = client.post("/auth/register", json={
        "email": "nouppercase@example.com",
        "password": "lowercase123!"
    })
    
    assert response.status_code == 422


def test_register_password_no_special_char(client):
    response = client.post("/auth/register", json={
        "email": "nospecial@example.com",
        "password": "NoSpecial123"
    })
    
    assert response.status_code == 422


def test_login_success(client):
    user_data = {
        "email": "logintest@example.com",
        "password": "ValidPass123!"
    }
    
    client.post("/auth/register", json=user_data)
    response = client.post("/auth/login", json=user_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    user_data = {
        "email": "wrongpass@example.com",
        "password": "ValidPass123!"
    }
    
    client.post("/auth/register", json=user_data)
    
    response = client.post("/auth/login", json={
        "email": "wrongpass@example.com",
        "password": "WrongPass123!"
    })
    
    assert response.status_code == 401


def test_login_nonexistent_user(client):
    response = client.post("/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "ValidPass123!"
    })
    
    assert response.status_code == 401
