import base64
import mimetypes
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel

from app.database import get_db
from app.auth.dependencies import get_current_user, get_user_file

router = APIRouter(prefix="/files", tags=["files"])


class FileCreate(BaseModel):
    name: str
    content: str
    parent_folder_id: Optional[int] = None


class FileUpdate(BaseModel):
    name: str


class FileResponse(BaseModel):
    id: int
    name: str
    size: int
    mime_type: Optional[str]
    parent_folder_id: Optional[int]
    created_at: str


@router.post("", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
def create_file(
    file: FileCreate,
    current_user: dict = Depends(get_current_user),
):
    try:
        decoded_content = base64.b64decode(file.content)
        size = len(decoded_content)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid base64 content",
        )
    
    mime_type, _ = mimetypes.guess_type(file.name)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        if file.parent_folder_id is not None:
            cursor.execute(
                "SELECT id FROM folders WHERE id = ? AND user_id = ?",
                (file.parent_folder_id, current_user["id"]),
            )
            if cursor.fetchone() is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent folder not found",
                )
        
        cursor.execute(
            "INSERT INTO files (name, content, size, mime_type, user_id, parent_folder_id) VALUES (?, ?, ?, ?, ?, ?)",
            (file.name, file.content, size, mime_type, current_user["id"], file.parent_folder_id),
        )
        file_id = cursor.lastrowid
        
        cursor.execute(
            "SELECT id, name, size, mime_type, parent_folder_id, created_at FROM files WHERE id = ?",
            (file_id,),
        )
        row = cursor.fetchone()
        
        return {
            "id": row["id"],
            "name": row["name"],
            "size": row["size"],
            "mime_type": row["mime_type"],
            "parent_folder_id": row["parent_folder_id"],
            "created_at": row["created_at"],
        }


@router.get("/{file_id}", response_model=FileResponse)
def get_file(file: dict = Depends(get_user_file)):
    return file


@router.get("/{file_id}/download")
def download_file(
    file_id: int,
    current_user: dict = Depends(get_current_user),
):
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT name, content, mime_type FROM files WHERE id = ? AND user_id = ?",
            (file_id, current_user["id"]),
        )
        row = cursor.fetchone()
        
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )
        
        try:
            decoded_content = base64.b64decode(row["content"])
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to decode file content",
            )
        
        return Response(
            content=decoded_content,
            media_type=row["mime_type"] or "application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{row["name"]}"'
            },
        )


@router.patch("/{file_id}", response_model=FileResponse)
def update_file(
    file_update: FileUpdate,
    file: dict = Depends(get_user_file),
):
    mime_type, _ = mimetypes.guess_type(file_update.name)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE files SET name = ?, mime_type = ? WHERE id = ?",
            (file_update.name, mime_type, file["id"]),
        )
        
        cursor.execute(
            "SELECT id, name, size, mime_type, parent_folder_id, created_at FROM files WHERE id = ?",
            (file["id"],),
        )
        row = cursor.fetchone()
        
        return {
            "id": row["id"],
            "name": row["name"],
            "size": row["size"],
            "mime_type": row["mime_type"],
            "parent_folder_id": row["parent_folder_id"],
            "created_at": row["created_at"],
        }


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(file: dict = Depends(get_user_file)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM files WHERE id = ?", (file["id"],))
        return None
