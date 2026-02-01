import os
import sqlite3
import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_PATH"] = "test.db"

from app.main import app
from app.database import DATABASE_PATH


def setup_test_tables():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS folders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            parent_folder_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (parent_folder_id) REFERENCES folders(id) ON DELETE CASCADE
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            content TEXT NOT NULL,
            size INTEGER NOT NULL,
            mime_type TEXT,
            user_id INTEGER NOT NULL,
            parent_folder_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (parent_folder_id) REFERENCES folders(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    conn.close()


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    if os.path.exists(DATABASE_PATH):
        os.remove(DATABASE_PATH)
    
    setup_test_tables()
    
    yield
    
    if os.path.exists(DATABASE_PATH):
        os.remove(DATABASE_PATH)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    user_data = {
        "email": "test@example.com",
        "password": "TestPass123!"
    }
    
    client.post("/auth/register", json=user_data)
    
    response = client.post("/auth/login", json=user_data)
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}
