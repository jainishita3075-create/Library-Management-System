from datetime import datetime, timedelta
import uuid
from src.service.file_handler import load_users, load_books, _save_users, _save_books
from config import BOOKS_FILE, USERS_FILE, ADMIN_FILE

def _check_duplicate(username: str, target_book: dict, users: list) -> bool:
    user_record = next((u for u in users if u.get("username") == username), None)
    if not user_record or not user_record.get("history"):
        return False

    target_isbn = str(target_book.get("isbn", "")).strip().lower()
    for record in user_record.get("history", []):
        if str(record.get("isbn", "")).strip().lower() == target_isbn:
            return True
    return False

def _generate_invoice_data(action: str, book: dict, price: float, user_id: str = "N/A", shipping_address: str = None) -> dict:
    invoice = {
        "invoice_id": f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:4]}",
        "date_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_id": user_id,
        "action": action,
        "book_id": book.get("book_id", "N/A"),
        "book_title": book.get("book_title", "N/A"),
        "isbn": book.get("isbn"),
        "price": price
    }
    if shipping_address:
        invoice["shipping_address"] = shipping_address
    return invoice

def execute_purchase(username: str, isbn: str, shipping_address: str = None) -> dict:
    books = load_books(BOOKS_FILE)
    users = load_users(USERS_FILE)
    
    target_book = next((b for b in books if b.get("isbn") == isbn), None)
    if not target_book:
        return {"success": False, "error": "Book not found."}
        
    if target_book.get("quantity", 0) <= 0:
        return {"success": False, "error": "Book is currently out of stock."}
        
    if _check_duplicate(username, target_book, users):
        return {"success": False, "error": "User already has this book in history."}
        
    target_user = next((u for u in users if u.get("username") == username), None)
    final_shipping = shipping_address if shipping_address else (target_user.get("address", "N/A") if target_user else "N/A")

    target_book["quantity"] -= 1
    price = target_book.get('price', 0.0)
    receipt = _generate_invoice_data("BUY", target_book, price, user_id=target_user.get("user_id", "N/A") if target_user else username, shipping_address=final_shipping)
    
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