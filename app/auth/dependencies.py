from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.auth.jwt import decode_access_token
from app.database import get_db

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    token = credentials.credentials
    user_id = decode_access_token(token)
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, email FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        
        return {"id": row["id"], "email": row["email"]}


def get_user_folder(
    folder_id: int,
    current_user: dict = Depends(get_current_user),
) -> dict:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, parent_folder_id, created_at FROM folders WHERE id = ? AND user_id = ?",
            (folder_id, current_user["id"]),
        )
        row = cursor.fetchone()
        
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Folder not found",
            )
        
        return {
            "id": row["id"],
            "name": row["name"],
            "parent_folder_id": row["parent_folder_id"],
            "created_at": row["created_at"],
        }


def get_user_file(
    file_id: int,
    current_user: dict = Depends(get_current_user),
) -> dict:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, size, mime_type, parent_folder_id, created_at FROM files WHERE id = ? AND user_id = ?",
            (file_id, current_user["id"]),
        )
        row = cursor.fetchone()
        
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )
        
        return {
            "id": row["id"],
            "name": row["name"],
            "size": row["size"],
            "mime_type": row["mime_type"],
            "parent_folder_id": row["parent_folder_id"],
            "created_at": row["created_at"],
        }
