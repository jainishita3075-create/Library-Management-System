from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status # type: ignore
from src.router.users import UserCredentials
from src.service import auth_service
from src.router.books import Book, BookCreate, BookUpdate
from src.service import book_service

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/login")
def api_admin_login(credentials: UserCredentials):
    result = auth_service.authenticate_admin(credentials.username, credentials.password)
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["error"])
    return {"message": "Admin login successful."}

@router.get("/all")
def api_get_all_users():
    return auth_service.get_all_users_safe()

@router.get("/users/{user_id}/history")
def api_admin_get_user_history(user_id: str):
    result = auth_service.fetch_user_history(user_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return {"history": result["history"]}

@router.post("/add", response_model=Book, status_code=status.HTTP_201_CREATED)
def admin_add_book(book: BookCreate):
    payload = book.model_dump() if hasattr(book, "model_dump") else book.dict()
    result = book_service.add_new_book(payload)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result["book"]

@router.put("/books/{identifier}")
def admin_update_book(
    identifier: str, 
    updates: BookUpdate, 
    by: Optional[str] = Query(None, description="Search by 'book_id', 'isbn', or 'book_title'. If omitted, auto-detected."),
    confirm: bool = Query(False, description="Set to True to save changes. False to just preview.")
):
    update_data = updates.model_dump(exclude_unset=True) if hasattr(updates, "model_dump") else updates.dict(exclude_unset=True)
    result = book_service.update_book(identifier, update_data, by, confirm)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Book not found."))
        
    return result

@router.delete("/books/{identifier}")
def admin_delete_book(
    identifier: str, 
    by: Optional[str] = Query(None, description="Search by 'book_id', 'isbn', or 'book_title'. If omitted, auto-detected."),
    confirm: bool = Query(False, description="Set to True to actually delete. False to preview book details.")
):
    result = book_service.delete_book(identifier, by, confirm)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Book not found."))
        
    return result

@router.get("/history/{identifier}")
def admin_get_history(
    identifier: str, 
    by: Optional[str] = Query(None, description="Search by 'book_id', 'isbn', 'book_title', or 'user_id'. If omitted, auto-detected.")
):
    result = book_service.fetch_history(identifier, by)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "No history found."))
    return result

@router.get("/history/{identifier}")
def admin_get_book_history(
    identifier: str, 
    by: Optional[str] = Query(None, description="Search by 'book_id', 'isbn', 'book_title', or 'user_id'. If omitted, auto-detected.")
):
    result = book_service.fetch_history(identifier, by)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "No history found."))
    return result