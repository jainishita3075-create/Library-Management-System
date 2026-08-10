from fastapi import APIRouter, HTTPException, status
from typing import Optional
from api.schemas.models import BookModel, TransactionRequest
from api.services.transaction_service import (
    execute_purchase,
    execute_issue,
    execute_return,
)
from Utility.file_handler import (
    load_books,
    add_book,
    update_book,
    delete_book,
)
from config import BOOKS_FILE


router = APIRouter()


@router.get("/")
def api_get_all_books():
    """Retrieve the entire catalog."""
    books = load_books(BOOKS_FILE)
    return books


@router.get("/search")
def api_search_books(query: str):
    """Search for books by exact ISBN or partial title match."""
    books = load_books(BOOKS_FILE)

    q_lower = query.lower()

    matches = [
        b
        for b in books
        if str(b.get("isbn", "")) == query
        or q_lower in str(b.get("book_title", "")).lower()
    ]

    if not matches:
        raise HTTPException(
            status_code=404,
            detail=f"No books found matching '{query}'."
        )

    return {"results": matches}


@router.get("/filter")
def api_filter_books(
    genre: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
):
    """Filter books by genre or price range."""

    books = load_books(BOOKS_FILE)
    results = books

    if genre:
        results = [
            b
            for b in results
            if str(b.get("genre", "")).lower() == genre.lower()
        ]

    if min_price is not None:
        results = [
            b
            for b in results
            if float(b.get("price", 0.0)) >= min_price
        ]

    if max_price is not None:
        results = [
            b
            for b in results
            if float(b.get("price", 0.0)) <= max_price
        ]

    if not results:
        raise HTTPException(
            status_code=404,
            detail="No books match the specified filters."
        )

    return {"results": results}


@router.post("/buy")
def api_buy_book(request: TransactionRequest):
    """Execute a book purchase for a user."""

    result = transaction_service.execute_purchase(
        request.username,
        request.isbn
    )

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result["error"]
        )

    return {
        "message": "Purchase successful",
        "receipt": result["receipt"],
    }


@router.post("/issue")
def api_issue_book(request: TransactionRequest):
    """Execute a 14-day book issue for a user."""

    result = transaction_service.execute_issue(
        request.username,
        request.isbn
    )

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result["error"]
        )

    return {
        "message": "Book issued successfully",
        "receipt": result["receipt"],
    }


@router.post("/return")
def api_return_book(request: TransactionRequest):
    """Return a previously issued book and calculate late fines."""

    result = transaction_service.execute_return(
        request.username,
        request.isbn
    )

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result["error"]
        )

    return {
        "message": "Book returned successfully",
        "fine_paid": result["fine_paid"],
        "record": result["record"],
    }


@router.post(
    "/admin/add",
    status_code=status.HTTP_201_CREATED
)
def api_add_book(book: BookModel):
    """Add a completely new book to the catalog."""

    books = load_books(BOOKS_FILE)

    if any(b.get("isbn") == book.isbn for b in books):
        raise HTTPException(
            status_code=400,
            detail="A book with this ISBN already exists."
        )

    book_dict = book.model_dump()

    add_book(BOOKS_FILE, book_dict)

    return {
        "message": "Book added successfully",
        "book": book_dict,
    }


@router.put("/admin/update/{isbn}")
def api_update_book(
    isbn: str,
    book_data: BookModel
):
    """Update an existing book by its ISBN."""

    books = load_books(BOOKS_FILE)

    target_book = next(
        (b for b in books if str(b.get("isbn")) == isbn),
        None
    )

    if not target_book:
        raise HTTPException(
            status_code=404,
            detail="Book not found."
        )

    updated_data = book_data.model_dump()

    update_book(
        BOOKS_FILE,
        isbn,
        updated_data
    )

    return {
        "message": f"Book with ISBN {isbn} updated successfully.",
        "updated_data": updated_data,
    }


@router.delete("/admin/delete/{isbn}")
def api_delete_book(isbn: str):
    """Permanently delete a book by its ISBN."""

    books = load_books(BOOKS_FILE)

    target_book = next(
        (b for b in books if str(b.get("isbn")) == isbn),
        None
    )

    if not target_book:
        raise HTTPException(
            status_code=404,
            detail="Book not found."
        )

    delete_book(BOOKS_FILE, isbn)

    return {
        "message": f"Book with ISBN {isbn} was deleted successfully."
    }