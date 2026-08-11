from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import json
import os

router = APIRouter()

# Pointing exactly to where your JSON file lives in the "file" folder
BOOKS_FILE = os.path.join("file", "MOCK_DATA.json")

# Define what a Book looks like
class Book(BaseModel):
    book_title: str
    author: str
    genre: str
    publication_date: str
    isbn: str
    price: float
    quantity: int
    language: str

# Define what information we need when someone buys a book
class BuyRequest(BaseModel):
    isbn: str

# --- Helper Functions ---
def load_books():
    """Silently opens the JSON file in the background and hands over the list of books."""
    if not os.path.exists(BOOKS_FILE):
        return []
    with open(BOOKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_books(books):
    """Silently takes your updated list of books and saves them back into the JSON file."""
    with open(BOOKS_FILE, "w", encoding="utf-8") as f:
        json.dump(books, f, indent=4)

# --- API Endpoints ---

@router.get("/", response_model=List[Book])
def get_all_books():
    """
    Look at all the books in the library.
    
    This command grabs every single book saved in your database and gives you the full list to read through.

    Example:
        >>> GET /books/
        [{"book_title": "The Great Gatsby", "author": "Pris Coulson", ...}]
    """
    return load_books()

@router.get("/filter", response_model=List[Book])
def filter_books(
    genre: Optional[str] = None, 
    min_price: Optional[float] = None, 
    max_price: Optional[float] = None
):
    """
    Search for books that match specific criteria.
    
    You can narrow down your library by asking for a specific genre, a minimum price, a maximum price, or all three combined! It sifts through the database and hands you back only the books that match.

    Example:
        >>> GET /books/filter?genre=sci-fi&min_price=12&max_price=120
        [{"book_title": "Dune", "genre": "sci-fi", "price": 25.00, ...}]
    """
    books = load_books()
    filtered_books = []

    for book in books:
        # Check if the book matches the requested genre (if one was provided)
        match_genre = True
        if genre and book.get("genre", "").lower() != genre.lower():
            match_genre = False
            
        # Check if the book is above the minimum price
        match_min = True
        if min_price is not None and book.get("price", 0) < min_price:
            match_min = False
            
        # Check if the book is below the maximum price
        match_max = True
        if max_price is not None and book.get("price", 0) > max_price:
            match_max = False

        if match_genre and match_min and match_max:
            filtered_books.append(book)

    if not filtered_books:
        raise HTTPException(status_code=404, detail="No books match those exact filters.")
        
    return filtered_books

@router.get("/{isbn}", response_model=Book)
def get_book_by_isbn(isbn: str):
    """
    Find one specific book using its ISBN.
    
    Just hand over the unique ISBN barcode number, and this will search the shelves and hand you back the exact book details.

    Example:
        >>> GET /books/12345678-X
        {"book_title": "money heist", "isbn": "12345678-X", ...}
    """
    books = load_books()
    for book in books:
        if book.get("isbn") == isbn:
            return book
    
    raise HTTPException(status_code=404, detail="Sorry, we couldn't find a book with that ISBN.")

@router.post("/buy")
def buy_book(request: BuyRequest):
    """
    Purchase a copy of a book.
    
    Send the ISBN of the book someone wants to buy. This function will find the book, make sure it is in stock, and then permanently reduce the library's quantity by 1.

    Example:
        >>> POST /books/buy
        Body: {"isbn": "12345678-X"}
        Response: {"message": "Success! You bought 'money heist'. 121 copies remaining."}
    """
    books = load_books()
    for book in books:
        if book.get("isbn") == request.isbn:
            if book.get("quantity", 0) <= 0:
                raise HTTPException(status_code=400, detail="Sorry, this book is completely out of stock!")
                
            book["quantity"] -= 1
            save_books(books)
            return {
                "message": f"Success! You bought '{book['book_title']}'. {book['quantity']} copies remaining."
            }
            
    raise HTTPException(status_code=404, detail="We couldn't find a book with that ISBN to buy.")

@router.post("/", response_model=Book)
def add_new_book(book: Book):
    """
    Put a brand new book onto the library shelf.
    
    Fill out the details for a new book (title, author, price, etc.) and this will save it into your collection. It prevents duplicate ISBNs automatically.

    Example:
        >>> POST /books/
        Body: {"book_title": "My Awesome Book", "isbn": "999-000", ...}
    """
    books = load_books()
    
    for existing_book in books:
        if existing_book.get("isbn") == book.isbn:
            raise HTTPException(status_code=400, detail="A book with this ISBN already exists!")

    books.append(book.dict())
    save_books(books)
    return book

@router.put("/{isbn}", response_model=Book)
def update_book(isbn: str, updated_book: Book):
    """
    Fix or change the details of a book you already have.
    
    Give it the ISBN of the book you want to change, plus the new corrected details. It swaps the old info for the new info.

    Example:
        >>> PUT /books/12345678-X
        Body: {"book_title": "Corrected Title", "price": 15.00, ...}
    """
    books = load_books()
    for index, book in enumerate(books):
        if book.get("isbn") == isbn:
            books[index] = updated_book.dict()
            save_books(books)
            return updated_book
            
    raise HTTPException(status_code=404, detail="Sorry, we couldn't find that book to update.")

@router.delete("/{isbn}")
def delete_book(isbn: str):
    """
    Throw a book in the trash.
    
    Tell it which ISBN you want to get rid of, and it will permanently delete that book from your collection.

    Example:
        >>> DELETE /books/12345678-X
        {"message": "The book was successfully deleted!"}
    """
    books = load_books()
    for index, book in enumerate(books):
        if book.get("isbn") == isbn:
            books.pop(index)
            save_books(books)
            return {"message": "The book was successfully deleted!"}
            
    raise HTTPException(status_code=404, detail="Sorry, we couldn't find that book to delete.")