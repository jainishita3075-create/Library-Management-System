from fastapi import APIRouter, HTTPException, status
from typing import Optional

from src.service.transaction_service import (
    execute_purchase,
    execute_issue,
    execute_return,
)

from src.service.file_handler import (
    load_books,
    add_book,
    update_book,
    delete_book,
)

from config import BOOKS_FILE


router = APIRouter()


# ============================================================
# GET ALL BOOKS
# ============================================================

@router.get("/")
def api_get_all_books():
    """Retrieve the entire catalog."""

    books = load_books(BOOKS_FILE)

    return books


# ============================================================
# SEARCH BOOKS
# ============================================================

@router.get("/search")
def api_search_books(query: str):
    """Search for books by exact ISBN or partial title match."""

    books = load_books(BOOKS_FILE)

    q_lower = query.lower()

    matches = [
        book
        for book in books
        if (
            str(book.get("isbn", "")) == query
            or q_lower in str(book.get("book_title", "")).lower()
        )
    ]

    if not matches:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No books found matching '{query}'."
        )

    return {
        "results": matches
    }


# ============================================================
# FILTER BOOKS
# ============================================================

@router.get("/filter")
def api_filter_books(
    genre: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
):
    """Filter books by genre or price range."""

    books = load_books(BOOKS_FILE)

    results = books

    # Filter by genre
    if genre:
        results = [
            book
            for book in results
            if str(book.get("genre", "")).lower() == genre.lower()
        ]

    # Filter by minimum price
    if min_price is not None:
        results = [
            book
            for book in results
            if float(book.get("price", 0.0)) >= min_price
        ]

    # Filter by maximum price
    if max_price is not None:
        results = [
            book
            for book in results
            if float(book.get("price", 0.0)) <= max_price
        ]

    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No books match the specified filters."
        )

    return {
        "results": results
    }


# ============================================================
# BUY BOOK
# ============================================================

@router.post("/buy")
def api_buy_book(request: dict):
    """Execute a book purchase for a user."""

    username = request.get("username")
    isbn = request.get("isbn")

    if not username or not isbn:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="username and isbn are required."
        )

    result = execute_purchase(
        username,
        isbn
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )

    return {
        "message": "Purchase successful",
        "receipt": result["receipt"],
    }


# ============================================================
# ISSUE BOOK
# ============================================================

@router.post("/issue")
def api_issue_book(request: dict):
    """Execute a 14-day book issue for a user."""

    username = request.get("username")
    isbn = request.get("isbn")

    if not username or not isbn:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="username and isbn are required."
        )

    result = execute_issue(
        username,
        isbn
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )

    return {
        "message": "Book issued successfully",
        "receipt": result["receipt"],
    }


# ============================================================
# RETURN BOOK
# ============================================================

@router.post("/return")
def api_return_book(request: dict):
    """Return a previously issued book and calculate late fines."""

    username = request.get("username")
    isbn = request.get("isbn")

    if not username or not isbn:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="username and isbn are required."
        )

    result = execute_return(
        username,
        isbn
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )

    return {
        "message": "Book returned successfully",
        "fine_paid": result["fine_paid"],
        "record": result["record"],
    }


# ============================================================
# ADMIN - ADD BOOK
# ============================================================

@router.post(
    "/admin/add",
    status_code=status.HTTP_201_CREATED
)
def api_add_book(book: dict):
    """Add a completely new book to the catalog."""

    isbn = book.get("isbn")

    if not isbn:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ISBN is required."
        )

    books = load_books(BOOKS_FILE)

    # Check duplicate ISBN
    if any(
        str(existing_book.get("isbn")) == str(isbn)
        for existing_book in books
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A book with this ISBN already exists."
        )

    add_book(
        BOOKS_FILE,
        book
    )

    return {
        "message": "Book added successfully",
        "book": book,
    }


# ============================================================
# ADMIN - UPDATE BOOK
# ============================================================

@router.put("/admin/update/{isbn}")
def api_update_book(
    isbn: str,
    book_data: dict
):
    """Update an existing book by its ISBN."""

    books = load_books(BOOKS_FILE)

    target_book = next(
        (
            book
            for book in books
            if str(book.get("isbn")) == str(isbn)
        ),
        None
    )

    if not target_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found."
        )

    update_book(
        BOOKS_FILE,
        isbn,
        book_data
    )

    return {
        "message": f"Book with ISBN {isbn} updated successfully.",
        "updated_data": book_data,
    }


# ============================================================
# ADMIN - DELETE BOOK
# ============================================================

@router.delete("/admin/delete/{isbn}")
def api_delete_book(isbn: str):
    """Permanently delete a book by its ISBN."""

    books = load_books(BOOKS_FILE)

    target_book = next(
        (
            book
            for book in books
            if str(book.get("isbn")) == str(isbn)
        ),
        None
    )

    if not target_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found."
        )

    delete_book(
        BOOKS_FILE,
        isbn
    )

    return {
        "message": f"Book with ISBN {isbn} was deleted successfully."
    }