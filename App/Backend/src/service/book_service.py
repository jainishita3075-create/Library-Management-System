from typing import List, Dict, Any, Optional
from src.service.file_handler import load_books, _save_books, load_users
from config import BOOKS_FILE, ADMIN_FILE, USERS_FILE
from src.utility.loggers import get_logger
import uuid # Assuming you use this for add_new_book
import copy

logger = get_logger(__name__)

def get_all_books() -> List[Dict[str, Any]]:
    return load_books(BOOKS_FILE)

def search_books(book_title: Optional[str] = None, isbn: Optional[str] = None, language: Optional[str] = None) -> List[Dict[str, Any]]:
    books = load_books(BOOKS_FILE)
    logger.info(f"Book search requested: title='{book_title}', isbn='{isbn}', language='{language}'")
    
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

def _matches_book(book: dict, identifier: str, by: Optional[str] = None) -> bool:
    ident_str = str(identifier).strip().lower()
    
    # 1. Check primary specified field if given
    if by in ["book_title", "title"]:
        if str(book.get("book_title", "")).strip().lower() == ident_str:
            return True
    elif by == "book_id":
        if str(book.get("book_id", "")).strip() == str(identifier).strip():
            return True
    elif by == "isbn":
        if str(book.get("isbn", "")).strip().lower() == ident_str:
            return True
    elif by and by not in ["auto", "None"]:
        if str(book.get(by, "")).strip().lower() == ident_str:
            return True

    # 2. Smart auto-detect fallback across all book identifier fields
    if str(book.get("book_title", "")).strip().lower() == ident_str:
        return True
    if str(book.get("isbn", "")).strip().lower() == ident_str:
        return True
    if str(book.get("book_id", "")).strip() == str(identifier).strip():
        return True

    return False


def update_book(identifier: str, update_data: Dict[str, Any], by: Optional[str] = None, confirm: bool = False) -> Dict[str, Any]:
    books = load_books(BOOKS_FILE)
    
    for index, book in enumerate(books):
        if _matches_book(book, identifier, by):
            # Create a copy of the old book for the "Before" view
            old_book = copy.deepcopy(book)
            
            # Create the "After" view
            new_book = copy.deepcopy(book)
            new_book.update(update_data)
            
            # Preserve original book_id if not explicitly provided
            if "book_id" not in update_data and "book_id" in old_book:
                new_book["book_id"] = old_book["book_id"]
            
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
            logger.info(f"Book updated successfully: identifier='{identifier}' (by {by or 'auto'})")
            return {
                "success": True, 
                "message": "Book successfully updated.",
                "book": new_book
            }
            
    logger.warning(f"Book update failed: Book not found for identifier='{identifier}' (by {by or 'auto'})")
    return {"success": False, "error": "Book not found."}

def delete_book(identifier: str, by: Optional[str] = None, confirm: bool = False) -> Dict[str, Any]:
    books = load_books(BOOKS_FILE)
    
    for index, book in enumerate(books):
        if _matches_book(book, identifier, by):
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
            logger.info(f"Book deleted: '{deleted_book.get('book_title')}' (identifier='{identifier}', by {by or 'auto'})")
            return {
                "success": True, 
                "message": f"Successfully deleted '{deleted_book.get('book_title', 'Unknown')}'."
            }
            
    logger.warning(f"Book deletion failed: Book not found for identifier='{identifier}' (by {by or 'auto'})")
    return {"success": False, "error": "Book not found."}


def add_new_book(book_data: Dict[str, Any]) -> Dict[str, Any]:
    books = load_books(BOOKS_FILE)
    
    # Prevent duplicate ISBNs
    if any(b.get("isbn") == book_data["isbn"] for b in books):
        logger.warning(f"Add book failed: ISBN {book_data.get('isbn')} already exists.")
        return {"success": False, "error": "Book with this ISBN already exists."}
        
    # Auto-increment book_id from the latest/highest existing numeric ID
    existing_nums = []
    for b in books:
        b_id = str(b.get("book_id", "")).strip()
        if b_id.isdigit():
            existing_nums.append(int(b_id))
            
    next_num = max(existing_nums) + 1 if existing_nums else 101
    book_data["book_id"] = str(next_num)
        
    books.append(book_data)
    _save_books(BOOKS_FILE, books)
    logger.info(f"New book added: '{book_data.get('book_title')}' (ID: {book_data.get('book_id')}, ISBN: {book_data.get('isbn')})")
    
    return {"success": True, "book": book_data}

def fetch_history(identifier: str, by: Optional[str] = None) -> dict:
    users = load_users(USERS_FILE)
    books = load_books(BOOKS_FILE)
    ident_str = str(identifier).strip().lower()
    
    # Check if this is a user search
    if by == "user_id" or (not by and any(str(u.get("user_id", "")).strip().lower() == ident_str for u in users)):
        target_user = next((u for u in users if str(u.get("user_id", "")).strip().lower() == ident_str), None)
        if target_user:
            return {
                "success": True,
                "search_type": "User History",
                "user_info": {
                    "user_id": target_user.get("user_id"),
                    "username": target_user.get("username"),
                    "email": target_user.get("email")
                },
                "history": target_user.get("history", [])
            }
        elif by == "user_id":
            return {"success": False, "error": f"No user found with ID '{identifier}'."}

    # Find target book using smart matcher
    target_book = next((b for b in books if _matches_book(b, identifier, by)), None)
    
    # Search all users to see who interacted with this book
    history_records = []
    for user in users:
        for record in user.get("history", []):
            match = False
            if by == "book_id" and str(record.get("book_id", "")).strip() == str(identifier).strip():
                match = True
            elif by == "isbn" and str(record.get("isbn", "")).strip().lower() == ident_str:
                match = True
            elif by in ["title", "book_title"] and str(record.get("book_title") or "").strip().lower() == ident_str:
                match = True
            elif not by or by == "auto":
                if str(record.get("book_id", "")).strip() == str(identifier).strip() or \
                   str(record.get("isbn", "")).strip().lower() == ident_str or \
                   str(record.get("book_title") or "").strip().lower() == ident_str:
                    match = True
                
            if match:
                enriched_record = {
                    "action": record.get("action"),
                    "date_time": record.get("date_time", record.get("date", "Unknown")),
                    "isbn": record.get("isbn"),
                    "book_title": record.get("book_title"),
                    "price": record.get("price"),
                    "shipping_address": record.get("shipping_address"),
                    "user_details": {
                        "user_id": user.get("user_id"),
                        "username": user.get("username"),
                        "email": user.get("email")
                    }
                }
                history_records.append(enriched_record)

    if not target_book and not history_records:
        return {"success": False, "error": f"No book found with {by or 'identifier'} '{identifier}'."}

    # Sort newest transactions first
    history_records.sort(key=lambda x: x.get("date_time", ""), reverse=True)

    return {
        "success": True, 
        "search_type": "Book History",
        "book_details": target_book,
        "history": history_records
    }