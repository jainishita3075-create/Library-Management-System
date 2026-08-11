from datetime import datetime, timedelta
from src.service.file_handler import load_users,load_books,_save_users,_save_books
from config import BOOKS_FILE, USERS_FILE

def _check_duplicate(username: str, target_book: dict, users: list) -> bool:
    """Internal helper to check if a user already owns or has issued a book."""
    user_record = next((u for u in users if u.get("username") == username), None)
    if not user_record or not user_record.get("history"):
        return False

    target_isbn = str(target_book.get("isbn", "")).strip().lower()
    for record in user_record.get("history", []):
        if str(record.get("isbn", "")).strip().lower() == target_isbn:
            return True
    return False

def _generate_invoice_data(action: str, book: dict, price: float) -> dict:
    """Internal helper to create receipt metadata."""
    return {
        "invoice_id": f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "book": book.get('book_title'),
        "isbn": book.get('isbn'),
        "price": price
    }

def execute_purchase(username: str, isbn: str) -> dict:
    books = load_books(BOOKS_FILE)
    users = load_users(USERS_FILE) 
from src.service.file_handler import load_users, load_books, _save_users, _save_books
from config import BOOKS_FILE, USERS_FILE

def _check_duplicate(username: str, target_book: dict, users: list) -> bool:
    """Internal helper to check if a user already owns or has issued a specific book."""
    user_record = next((u for u in users if u.get("username") == username), None)
    if not user_record or not user_record.get("history"):
        return False

    target_isbn = str(target_book.get("isbn", "")).strip().lower()
    for record in user_record.get("history", []):
        if str(record.get("isbn", "")).strip().lower() == target_isbn:
            return True
    return False

def _generate_invoice_data(action: str, book: dict, price: float) -> dict:
    """Internal helper to automatically generate a receipt for any transaction."""
    return {
        "invoice_id": f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "book": book.get('book_title'),
        "isbn": book.get('isbn'),
        "price": price
    }

def execute_purchase(username: str, isbn: str) -> dict:
    """
    Processes a book purchase for a user.
    
    It checks if the book exists, ensures it is in stock, and makes sure 
    the user hasn't already bought it. If everything is good, it takes one 
    copy off the shelf, writes a receipt, and saves it to the user's history.

    Example:
        >>> execute_purchase("ishita", "12345678-X")
        {"success": True, "receipt": {"invoice_id": "INV-...", "price": 20.0}}
    """
    books = load_books(BOOKS_FILE)
    users = load_users(USERS_FILE)
    
    target_book = next((b for b in books if b.get("isbn") == isbn), None)
    if not target_book:
        return {"success": False, "error": "Book not found."}
        
    if target_book.get("quantity", 0) <= 0:
        return {"success": False, "error": "Book is currently out of stock."}
        
    if _check_duplicate(username, target_book, users):
        return {"success": False, "error": "User already has this book in history."}
        
    target_book["quantity"] -= 1
    price = target_book.get('price', 0.0)
    receipt = _generate_invoice_data("BUY", target_book, price)
    
    for user in users:
        if user.get("username") == username:
            user.setdefault("history", []).append(receipt)
            break
            
    _save_books(BOOKS_FILE, books)
    _save_users(USERS_FILE, users)
    
    return {"success": True, "receipt": receipt}

def execute_issue(username: str, isbn: str) -> dict:
    """
    Lets a user borrow a book for 14 days.
    
    Similar to buying, it checks stock and prevents duplicates. Instead of 
    charging money, it sets the price to 0.0 and calculates a return date 
    exactly two weeks from today.

    Example:
        >>> execute_issue("ishita", "12345678-X")
        {"success": True, "receipt": {"due_date": "2026-08-25", "price": 0.0}}
    """
    books = load_books(BOOKS_FILE)
    users = load_users(USERS_FILE)
    
    target_book = next((b for b in books if b.get("isbn") == isbn), None)
    if not target_book:
        return {"success": False, "error": "Book not found."}
        
    if target_book.get("quantity", 0) <= 0:
        return {"success": False, "error": "Book is currently out of stock."}
        
    if _check_duplicate(username, target_book, users):
        return {"success": False, "error": "User already has this book in history."}
        
    target_book["quantity"] -= 1
    due_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    receipt = _generate_invoice_data("ISSUE", target_book, 0.0)
    receipt["due_date"] = due_date
    
    for user in users:
        if user.get("username") == username:
            user.setdefault("history", []).append(receipt)
            break
            
    _save_books(BOOKS_FILE, books)
    _save_users(USERS_FILE, users)
    
    return {"success": True, "receipt": receipt}

def execute_return(username: str, isbn: str) -> dict:
    """
    Processes a borrowed book being returned to the library.
    
    It finds the exact issue record in the user's history, calculates if 
    they owe any late fines ($1.50 per day), puts the book back on the 
    library shelf, and updates the user's history to show it was returned.

    Example:
        >>> execute_return("ishita", "12345678-X")
        {"success": True, "fine_paid": 0.0, "record": {...}}
    """
    books = load_books(BOOKS_FILE)
    users = load_users(USERS_FILE)
    
    user_record = next((u for u in users if u.get("username") == username), None)
    if not user_record:
        return {"success": False, "error": "User not found."}
        
    issued_record = next((r for r in user_record.get("history", []) if r.get("isbn") == isbn and r.get("action") == "ISSUE"), None)
    
    if not issued_record:
        return {"success": False, "error": "No active issue record found for this book."}
        
    due_date_obj = datetime.strptime(issued_record["due_date"], "%Y-%m-%d").date()
    now_date = datetime.now().date()
    
    fine = 0.0
    if now_date > due_date_obj:
        overdue_days = (now_date - due_date_obj).days
        fine = overdue_days * 1.50
        
    for b in books:
        if b.get("isbn") == isbn:
            b["quantity"] += 1
            break
            
    issued_record["action"] = "RETURNED"
    issued_record["return_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    issued_record["fine_paid"] = fine
    
    _save_books(BOOKS_FILE, books)
    _save_users(USERS_FILE, users)
    
    return {"success": True, "fine_paid": fine, "record": issued_record}
    
    target_book = next((b for b in books if b.get("isbn") == isbn), None)
    if not target_book:
        return {"success": False, "error": "Book not found."}
        
    if target_book.get("quantity", 0) <= 0:
        return {"success": False, "error": "Book is currently out of stock."}
        
    if _check_duplicate(username, target_book, users):
        return {"success": False, "error": "User already has this book in history."}
        
    target_book["quantity"] -= 1
    price = target_book.get('price', 0.0)
    receipt = _generate_invoice_data("BUY", target_book, price)
    
    for user in users:
        if user.get("username") == username:
            user.setdefault("history", []).append(receipt)
            break
            
    _save_books(BOOKS_FILE, books)
    _save_users(USERS_FILE, users)
    
    return {"success": True, "receipt": receipt}

def execute_issue(username: str, isbn: str) -> dict:
    books = load_books(BOOKS_FILE)
    users = load_users(USERS_FILE)
    
    target_book = next((b for b in books if b.get("isbn") == isbn), None)
    if not target_book:
        return {"success": False, "error": "Book not found."}
        
    if target_book.get("quantity", 0) <= 0:
        return {"success": False, "error": "Book is currently out of stock."}
        
    if _check_duplicate(username, target_book, users):
        return {"success": False, "error": "User already has this book in history."}
        
    target_book["quantity"] -= 1
    due_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    receipt = _generate_invoice_data("ISSUE", target_book, 0.0)
    receipt["due_date"] = due_date
    
    for user in users:
        if user.get("username") == username:
            user.setdefault("history", []).append(receipt)
            break
            
    _save_books(BOOKS_FILE, books)
    _save_users(USERS_FILE, users)
    
    return {"success": True, "receipt": receipt}

def execute_return(username: str, isbn: str) -> dict:
    books = load_books(BOOKS_FILE)
    users = load_users(USERS_FILE)
    
    user_record = next((u for u in users if u.get("username") == username), None)
    if not user_record:
        return {"success": False, "error": "User not found."}
        
    issued_record = next((r for r in user_record.get("history", []) if r.get("isbn") == isbn and r.get("action") == "ISSUE"), None)
    
    if not issued_record:
        return {"success": False, "error": "No active issue record found for this book."}
        
    due_date_obj = datetime.strptime(issued_record["due_date"], "%Y-%m-%d").date()
    now_date = datetime.now().date()
    
    fine = 0.0
    if now_date > due_date_obj:
        overdue_days = (now_date - due_date_obj).days
        fine = overdue_days * 1.50
        
    for b in books:
        if b.get("isbn") == isbn:
            b["quantity"] += 1
            break
            
    issued_record["action"] = "RETURNED"
    issued_record["return_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    issued_record["fine_paid"] = fine
    
    _save_books(BOOKS_FILE, books)
    _save_users(USERS_FILE, users)
    
    return {"success": True, "fine_paid": fine, "record": issued_record}