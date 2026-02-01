from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.database import get_db
from app.auth.dependencies import get_current_user, get_user_folder

router = APIRouter(prefix="/folders", tags=["folders"])


class FolderCreate(BaseModel):
    name: str
    parent_folder_id: Optional[int] = None


class FolderUpdate(BaseModel):
    name: str


class FolderResponse(BaseModel):
    id: int
    name: str
    parent_folder_id: Optional[int]
    created_at: str


class FolderContentsResponse(BaseModel):
    id: int
    name: str
    parent_folder_id: Optional[int]
    created_at: str
    subfolders: List[dict]
    files: List[dict]


class RootContentsResponse(BaseModel):
    folders: List[dict]
    files: List[dict]


@router.get("/root", response_model=RootContentsResponse)
def get_root_contents(current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, name, parent_folder_id, created_at FROM folders WHERE parent_folder_id IS NULL AND user_id = ?",
            (current_user["id"],),
        )
        folders = [
            {
                "id": row["id"],
                "name": row["name"],
                "parent_folder_id": row["parent_folder_id"],
                "created_at": row["created_at"],
            }
            for row in cursor.fetchall()
        ]
        
        cursor.execute(
            "SELECT id, name, size, mime_type, parent_folder_id, created_at FROM files WHERE parent_folder_id IS NULL AND user_id = ?",
            (current_user["id"],),
        )
        files = [
            {
                "id": row["id"],
                "name": row["name"],
                "size": row["size"],
                "mime_type": row["mime_type"],
                "parent_folder_id": row["parent_folder_id"],
                "created_at": row["created_at"],
            }
            for row in cursor.fetchall()
        ]
        
        return {"folders": folders, "files": files}


@router.post("", response_model=FolderResponse, status_code=status.HTTP_201_CREATED)
def create_folder(
    folder: FolderCreate,
    current_user: dict = Depends(get_current_user),
):
    with get_db() as conn:
        cursor = conn.cursor()
        
        if folder.parent_folder_id is not None:
            cursor.execute(
                "SELECT id FROM folders WHERE id = ? AND user_id = ?",
                (folder.parent_folder_id, current_user["id"]),
            )
            if cursor.fetchone() is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent folder not found",
                )
        
        cursor.execute(
            "INSERT INTO folders (name, user_id, parent_folder_id) VALUES (?, ?, ?)",
            (folder.name, current_user["id"], folder.parent_folder_id),
        )
        folder_id = cursor.lastrowid
        
        cursor.execute(
            "SELECT id, name, parent_folder_id, created_at FROM folders WHERE id = ?",
            (folder_id,),
        )
        row = cursor.fetchone()
        
        return {
            "id": row["id"],
            "name": row["name"],
            "parent_folder_id": row["parent_folder_id"],
            "created_at": row["created_at"],
        }


@router.get("/{folder_id}", response_model=FolderContentsResponse)
def get_folder(
    folder: dict = Depends(get_user_folder),
    current_user: dict = Depends(get_current_user),
):
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, name, parent_folder_id, created_at FROM folders WHERE parent_folder_id = ? AND user_id = ?",
            (folder["id"], current_user["id"]),
        )
        subfolders = [
            {
                "id": row["id"],
                "name": row["name"],
                "parent_folder_id": row["parent_folder_id"],
                "created_at": row["created_at"],
            }
            for row in cursor.fetchall()
        ]
        
        cursor.execute(
            "SELECT id, name, size, mime_type, parent_folder_id, created_at FROM files WHERE parent_folder_id = ? AND user_id = ?",
            (folder["id"], current_user["id"]),
        )
        files = [
            {
                "id": row["id"],
                "name": row["name"],
                "size": row["size"],
                "mime_type": row["mime_type"],
                "parent_folder_id": row["parent_folder_id"],
                "created_at": row["created_at"],
            }
            for row in cursor.fetchall()
        ]
        
        return {
            "id": folder["id"],
            "name": folder["name"],
            "parent_folder_id": folder["parent_folder_id"],
            "created_at": folder["created_at"],
            "subfolders": subfolders,
            "files": files,
        }


@router.patch("/{folder_id}", response_model=FolderResponse)
def update_folder(
    folder_update: FolderUpdate,
    folder: dict = Depends(get_user_folder),
):
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE folders SET name = ? WHERE id = ?",
            (folder_update.name, folder["id"]),
        )
        
        cursor.execute(
            "SELECT id, name, parent_folder_id, created_at FROM folders WHERE id = ?",
            (folder["id"],),
        )
        row = cursor.fetchone()
        
        return {
            "id": row["id"],
            "name": row["name"],
            "parent_folder_id": row["parent_folder_id"],
            "created_at": row["created_at"],
        }


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_folder(
    folder: dict = Depends(get_user_folder),
    current_user: dict = Depends(get_current_user),
):
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT COUNT(*) as count FROM folders WHERE parent_folder_id = ?",
            (folder["id"],),
        )
        if cursor.fetchone()["count"] > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Folder is not empty. Delete subfolders first.",
            )
        
        cursor.execute(
            "SELECT COUNT(*) as count FROM files WHERE parent_folder_id = ?",
            (folder["id"],),
        )
        if cursor.fetchone()["count"] > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Folder is not empty. Delete files first.",
            )
        
        cursor.execute("DELETE FROM folders WHERE id = ?", (folder["id"],))
        
        return None
