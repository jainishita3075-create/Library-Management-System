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
    isbn: str = Field(..., min_length=10, max_length=20)
    book_title: str = Field(..., min_length=1)
    author: str
    genre: str
    publication_date: str
    price: float = Field(..., gt=0)
    quantity: int = Field(..., ge=0)
    language: str

class BookCreate(BaseModel):
    isbn: str = Field(..., min_length=10, max_length=20, description="ISBN (10-20 characters)")
    book_title: str = Field(..., min_length=1, description="Book Title")
    author: str = Field(..., description="Author")
    genre: str = Field(..., description="Genre/Category")
    publication_date: str = Field(..., description="Publication Date (e.g. YYYY-MM-DD)")
    price: float = Field(..., gt=0, description="Book Price")
    quantity: int = Field(..., ge=0, description="Stock Quantity")
    language: str = Field(..., description="Language")

class BookUpdate(BaseModel):
    book_title: Optional[str] = None
    author: Optional[str] = None
    genre: Optional[str] = None
    publication_date: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, ge=0)
    language: Optional[str] = None

class TransactionRequest(BaseModel):
    user_id: str = Field(..., description="The ID of the user performing the action")
    isbn: str = Field(..., description="The ISBN of the book")

class BuyBookRequest(BaseModel):
    user_id: str = Field(..., description="The ID of the user performing the purchase")
    isbn: str = Field(..., description="The ISBN of the book to buy")
    shipping_address: Optional[str] = Field(None, description="Custom shipping address. If omitted, user's registered address is used.")

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
def api_buy_book(request: BuyBookRequest):
    result = execute_purchase(request.user_id, request.isbn, shipping_address=request.shipping_address)
    if not result["success"]:
        err_msg = result["error"]
        status_code = status.HTTP_404_NOT_FOUND if "not found" in err_msg.lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=err_msg)
    return {"message": "Purchase successful!", "receipt": result["receipt"]}

@router.post("/issue")
def api_issue_book(request: TransactionRequest):
    result = execute_issue(request.user_id, request.isbn)
    if not result["success"]:
        err_msg = result["error"]
        status_code = status.HTTP_404_NOT_FOUND if "not found" in err_msg.lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=err_msg)
    return {"message": "Book issued successfully! Please note the due date.", "receipt": result["receipt"]}

@router.post("/return")
def api_return_book(request: TransactionRequest):
    result = execute_return(request.user_id, request.isbn)
    if not result["success"]:
        err_msg = result["error"]
        status_code = status.HTTP_404_NOT_FOUND if "not found" in err_msg.lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=err_msg)
        
    response = {"message": "Book returned successfully!"}
    if result.get("fine_paid", 0) > 0:
        response["message"] += f" A late fine of ${result['fine_paid']} was charged."
        
    response["record"] = result["record"]
    return response

# ==========================================
# ADMIN ENDPOINTS (Manage Books)
# ==========================================
@router.post("/admin/add", response_model=Book, status_code=status.HTTP_201_CREATED)
def admin_add_book(book: BookCreate):
    payload = book.model_dump() if hasattr(book, "model_dump") else book.dict()
    result = book_service.add_new_book(payload)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result["book"]


@router.put("/admin/{identifier}")
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

@router.delete("/admin/{identifier}")
def admin_delete_book(
    identifier: str, 
    by: Optional[str] = Query(None, description="Search by 'book_id', 'isbn', or 'book_title'. If omitted, auto-detected."),
    confirm: bool = Query(False, description="Set to True to actually delete. False to preview book details.")
):
    result = book_service.delete_book(identifier, by, confirm)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Book not found."))
        
    return result

@router.get("/admin/history/{identifier}")
def admin_get_book_history(
    identifier: str, 
    by: Optional[str] = Query(None, description="Search by 'book_id', 'isbn', 'book_title', or 'user_id'. If omitted, auto-detected.")
):
    result = book_service.fetch_history(identifier, by)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "No history found."))
    return result