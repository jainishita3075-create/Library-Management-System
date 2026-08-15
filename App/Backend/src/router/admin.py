from fastapi import APIRouter, HTTPException, Query, status # type: ignore
from Backend.src.router.books import Book, BookUpdate
from src.service import book_service

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.put("/books/{isbn}")
def update_book(
    identifier: str, 
    updates: BookUpdate,
    # 2. Changed 'title' to 'book_title' to match your database
    by: str = Query("book_id", regex="^(book_id|isbn|book_title)$"),
    # 3. Added the confirm toggle
    confirm: bool = Query(False, description="Set to True to save changes. False to just preview.")
):
    # This endpoint assumes you have already verified the user is an admin
    update_data = updates.dict(exclude_unset=True)
    
    # Pass 'confirm' to the service layer
    result = book_service.update_book_preview(identifier, update_data, by, confirm)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Book not found."))
        
    return result
                        

@router.delete("/books/{isbn}")
def delete_book(
    identifier: str, 
    # Removed title as an option for delete, as requested earlier
    by: str = Query("book_id", regex="^(book_id|isbn)$"),
    # Added the confirm toggle
    confirm: bool = Query(False, description="Set to True to actually delete. False to preview book.")
):
    # Pass 'confirm' to the service layer
    result = book_service.delete_book_preview(identifier, by, confirm)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Book not found."))
        
    return result


# Don't forget to add your new history route!
# Fixed /{isbn} to /{identifier}
@router.get("/history/{identifier}")
def admin_get_history(
    identifier: str, 
    # Added user_id to the allowed regex options
    by: str = Query("book_id", regex="^(book_id|isbn|user_id)$")
):
    # Point this to a new, unified function in book_service
    result = book_service.fetch_history(identifier, by)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))
        
    return result