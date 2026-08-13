from typing import List, Dict, Any, Optional
from src.service.file_handler import load_books, _save_books, load_users
from config import BOOKS_FILE, ADMIN_FILE, USERS_FILE
import uuid # Assuming you use this for add_new_book
import copy

def get_all_books() -> List[Dict[str, Any]]:
    return load_books(BOOKS_FILE)

def search_books(book_title: Optional[str] = None, isbn: Optional[str] = None, language: Optional[str] = None) -> List[Dict[str, Any]]:
    books = load_books(BOOKS_FILE)
    
    # If the user didn't type any search terms, return nothing (or all books, your choice!)
    if not book_title and not isbn and not language:
        return books 

    results = []
    for b in books:
        # Check if ANY of the conditions match
        match_title = book_title and book_title.lower() in b.get("book_title", "").lower()
        match_isbn = isbn and b.get("isbn") == isbn
        match_language = language and language.lower() == b.get("language", "").lower()
        
        if match_title or match_isbn or match_language:
            results.append(b)

    return results

def filter_books(min_price: Optional[float] = None, max_price: Optional[float] = None, language: Optional[str] = None) -> List[Dict[str, Any]]:
    books = load_books(BOOKS_FILE)
    filtered = []

    for book in books:
        if min_price is not None and book.get("price", 0) < min_price:
            continue
        if max_price is not None and book.get("price", 0) > max_price:
            continue
        if language and book.get("language", "").lower() != language.lower():
            continue
        filtered.append(book)

    return filtered

def update_book(identifier: str, update_data: Dict[str, Any], by: str, confirm: bool) -> Dict[str, Any]:
    books = load_books(BOOKS_FILE)
    
    for index, book in enumerate(books):
        if (by == "book_title" and book.get("book_title", "").lower() == identifier.lower()) or \
           (by != "book_title" and book.get(by) == identifier):
            
            # Create a copy of the old book for the "Before" view
            old_book = copy.deepcopy(book)
            
            # Create the "After" view
            new_book = copy.deepcopy(book)
            new_book.update(update_data)
            
            # If the admin hasn't confirmed yet, just return the preview
            if not confirm:
                return {
                    "success": True, 
                    "message": "PREVIEW MODE: Changes not saved yet. Send confirm=True to save.",
                    "before_update": old_book,
                    "after_update": new_book
                }
            
            # If confirm=True, actually save it
            books[index] = new_book
            _save_books(BOOKS_FILE, books)
            return {
                "success": True, 
                "message": "Book successfully updated.",
                "book": new_book
            }
            
    return {"success": False, "error": "Book not found."}

def delete_book(identifier: str, by: str, confirm: bool) -> Dict[str, Any]:
    books = load_books(BOOKS_FILE)
    
    for index, book in enumerate(books):
        if book.get(by) == identifier:
            
            # If not confirmed, just show the admin what they are about to delete
            if not confirm:
                return {
                    "success": True,
                    "message": "PREVIEW MODE: Book not deleted yet. Send confirm=True to permanently delete.",
                    "book_to_delete": book
                }
            
            # If confirm=True, delete it
            deleted_book = books.pop(index)
            _save_books(BOOKS_FILE, books)
            return {
                "success": True, 
                "message": f"Successfully deleted '{deleted_book.get('book_title', 'Unknown')}'."
            }
            
    return {"success": False, "error": "Book not found."}


# Assuming you already have this function, it should look something like this:
def add_new_book(book_data: Dict[str, Any]) -> Dict[str, Any]:
    books = load_books(BOOKS_FILE)
    
    # Example logic to prevent duplicate ISBNs
    if any(b.get("isbn") == book_data["isbn"] for b in books):
        return {"success": False, "error": "Book with this ISBN already exists."}
        
    if not book_data.get("book_id"):
        book_data["book_id"] = str(uuid.uuid4())
        
    books.append(book_data)
    _save_books(BOOKS_FILE, books)
    
    return {"success": True, "book": book_data}

def fetch_book_history_with_users(identifier: str, by: str) -> Dict[str, Any]:
    books = load_books(BOOKS_FILE)
    users = load_users(USERS_FILE) 
    
    # 1. Get the book details first
    target_book = next((b for b in books if b.get(by) == identifier), None)
    if not target_book:
         return {"success": False, "error": "Book not found in library."}
    
    # 2. Look through all users to find who has interacted with this book
    history_records = []
    
    for user in users:
        for record in user.get("history", []):
            
            if (by == "book_id" and record.get("book_id") == identifier) or \
               (by == "isbn" and record.get("isbn") == identifier):
                
                # Combine the transaction data with the user's details
                enriched_record = {
                    "action": record.get("action"),
                    "date_time": record.get("date_time", record.get("date", "Unknown")),
                    "user_details": {
                        "user_id": user.get("user_id"),
                        "username": user.get("username"),
                        "email": user.get("email")
                    }
                }
                
                if record.get("due_date"):
                    enriched_record["due_date"] = record.get("due_date")
                    
                history_records.append(enriched_record)

    # Sort history newest first
    history_records.sort(key=lambda x: x.get("date_time", ""), reverse=True)

    return {
        "success": True, 
        "book_details": target_book,
        "transaction_history": history_records if history_records else "No transactions found for this book."
    }