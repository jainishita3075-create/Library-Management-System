from fastapi import APIRouter, HTTPException, Query, status # type: ignore
from pydantic import BaseModel, Field
from typing import List, Optional

# Only import the service layers, remove direct file_handler imports
from src.service import book_service
from src.service.auth_service import (
    execute_purchase, 
    execute_issue, 
    execute_return, 
    fetch_book_history
)

router = APIRouter()

# ==========================================
# PYDANTIC MODELS (Validation & Schema)
# ==========================================
class Book(BaseModel):
    book_id: Optional[str] = None  
    isbn: str = Field(..., min_length=10, max_length=13)
    book_title: str = Field(..., min_length=1)  # Changed from 'title'
    author: str
    genre: str
    publication_date: str
    price: float = Field(..., gt=0)
    quantity: int = Field(..., ge=0)
    language: str

class BookUpdate(BaseModel):
    book_title: Optional[str] = None  # Changed from 'title'
    author: Optional[str] = None
    genre: Optional[str] = None
    publication_date: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, ge=0)
    language: Optional[str] = None

class TransactionRequest(BaseModel):
    user_id: str = Field(..., description="The ID of the user performing the action")
    isbn: str = Field(..., description="The ISBN of the book")

class BuyRequest(BaseModel):
    isbn: str

# ==========================================
# PUBLIC ENDPOINTS
# ==========================================
@router.get("/", response_model=List[Book])
def get_all_books():
    return book_service.get_all_books()

@router.get("/search", response_model=List[Book])
def search_books(
    book_title: Optional[str] = None, 
    isbn: Optional[str] = None, 
    language: Optional[str] = None
):
    results = book_service.search_books(book_title=book_title, isbn=isbn, language=language)
    if not results:
        raise HTTPException(status_code=404, detail="No books match your search.")
    return results

@router.get("/filter", response_model=List[Book])
def filter_books(
    min_price: Optional[float] = None, 
    max_price: Optional[float] = None,
    language: Optional[str] = None
):
    # Safeguard: Block the request if all three are empty
    if min_price is None and max_price is None and language is None:
        raise HTTPException(
            status_code=400, 
            detail="You must provide at least one filter (price or language)."
        )

    results = book_service.filter_books(min_price, max_price, language)
    if not results:
        raise HTTPException(status_code=404, detail="No books match those filters.")
    return results

# ==========================================
# USER TRANSACTION ENDPOINTS
# ==========================================
@router.post("/buy")
def api_buy_book(request: TransactionRequest):
    result = execute_purchase(request.user_id, request.isbn)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"message": "Purchase successful!", "receipt": result["receipt"]}

@router.post("/issue")
def api_issue_book(request: TransactionRequest):
    result = execute_issue(request.user_id, request.isbn)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"message": "Book issued successfully! Please note the due date.", "receipt": result["receipt"]}

@router.post("/return")
def api_return_book(request: TransactionRequest):
    result = execute_return(request.user_id, request.isbn)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
        
    response = {"message": "Book returned successfully!"}
    if result.get("fine_paid", 0) > 0:
        response["message"] += f" A late fine of ${result['fine_paid']} was charged."
        
    response["record"] = result["record"]
    return response

# ==========================================
# ADMIN ENDPOINTS (Manage Books)
# ==========================================
@router.post("/admin/add", response_model=Book, status_code=status.HTTP_201_CREATED)
def admin_add_book(book: Book):
    result = book_service.add_new_book(book.dict())
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result["book"]


# 1. Removed response_model=Book
# 2. Changed /{isbn} to /{identifier} to match the function variable
@router.put("/admin/{identifier}")
def admin_update_book(
    identifier: str, 
    updates: BookUpdate, 
    by: str = Query("book_id", regex="^(book_id|isbn)$"),
    # 3. Added the confirm toggle for the Yes/No logic
    confirm: bool = Query(False, description="Set to True to save changes. False to just preview.")
):
    update_data = updates.dict(exclude_unset=True)
    
    # 4. Point it to the new preview function in your service layer
    result = book_service.update_book_preview(identifier, update_data, by, confirm)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))
        
    return result

# 1. Changed /{isbn} to /{identifier} to match the function variable
@router.delete("/admin/{identifier}")
def admin_delete_book(
    identifier: str, 
    # 2. Removed 'title' from regex since you only want ID or ISBN
    by: str = Query("book_id", regex="^(book_id|isbn)$"),
    # 3. Added the confirm toggle for the Yes/No logic
    confirm: bool = Query(False, description="Set to True to actually delete. False to preview book details.")
):
    # 4. Point it to the preview function we created in your service layer
    result = book_service.delete_book_preview(identifier, by, confirm)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Book not found."))
        
    # 5. Return the result directly (it handles both the preview data and the success message)
    return result

@router.get("/admin/history/{isbn}")
def admin_get_book_history(
    identifier: str, 
    by: str = Query("book_id", regex="^(book_id|isbn|title)$")
):
    result = fetch_book_history(identifier, by)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return {"history": result["history"]}