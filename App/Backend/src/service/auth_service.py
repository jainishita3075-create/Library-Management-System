from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import uuid
from src.service.file_handler import load_users, load_books, _save_users, _save_books
from config import BOOKS_FILE, USERS_FILE, ADMIN_FILE
from src.utility.input_validator import valid_username, valid_password, is_valid_email
from src.utility.loggers import get_logger

logger = get_logger(__name__)

def register_new_user(user_data: dict) -> dict:
    users = load_users(USERS_FILE)
    
    if not valid_username(user_data["username"]):
        logger.warning(f"User registration failed: Invalid username format '{user_data.get('username')}'")
        return {"success": False, "error": "Username must be at least 8 chars, 5 letters, and 2 digits."}
        
    if not is_valid_email(user_data.get("email", "")):
        logger.warning(f"User registration failed: Invalid email format '{user_data.get('email')}'")
        return {"success": False, "error": "Invalid email address format."}

    if any(u.get("username") == user_data["username"] for u in users):
        logger.warning(f"User registration failed: Duplicate username '{user_data.get('username')}'")
        return {"success": False, "error": "Username already exists."}
        
    if any(u.get("email") == user_data["email"] for u in users):
        logger.warning(f"User registration failed: Duplicate email '{user_data.get('email')}'")
        return {"success": False, "error": "Email is already registered."}
        
    if not valid_password(user_data["password"]):
        logger.warning(f"User registration failed: Invalid password format for user '{user_data.get('username')}'")
        return {"success": False, "error": "Invalid password format."}
        
# ==========================================
#  AUTO-INCREMENT USER ID
# ==========================================
    if not users:
        next_num = 101 # Starting number
    else:
        existing_nums = []
        for u in users:
            id_val = str(u.get("user_id", ""))
            # Only process IDs that match our format to prevent crashes from bad data
            if id_val.startswith("USR-"):
                try:
                    # Strip the prefix and convert the number part to an integer
                    num_part = int(id_val.replace("USR-", ""))
                    existing_nums.append(num_part)
                except ValueError:
                    pass
                    
        next_num = max(existing_nums) + 1 if existing_nums else 101
        
    # Generate the final prefixed ID (e.g., "USR-105")
    new_user_id = f"USR-{next_num}"
        
    new_user = {
        "user_id": new_user_id, 
        "username": user_data["username"],
        "password": user_data["password"],
        "email": user_data["email"],
        "phone_number": user_data["phone_number"],
        "address": user_data["address"],
        "history": []
    }
    
    users.append(new_user)
    
    if _save_users(USERS_FILE, users):
        logger.info(f"User account created successfully: {new_user['username']} ({new_user['user_id']})")
        return {"success": True, "message": "Account created successfully.", "user_id": new_user["user_id"]}
    
    logger.error("Failed to save user data during registration.")
    return {"success": False, "error": "Failed to save user data."}


def authenticate_user(username: str, password: str) -> dict:
    # Looks ONLY in USERS.json
    users = load_users(USERS_FILE) 
    
    for u in users:
        if u.get("username") == username and u.get("password") == password:
            logger.info(f"User authenticated successfully: {username} ({u.get('user_id')})")
            return {"success": True, "user_id": u.get("user_id")}
            
    logger.warning(f"User authentication failed for username: {username}")
    return {"success": False, "error": "Invalid user credentials."}

def fetch_user_history(user_id: str) -> dict:
    users = load_users(USERS_FILE)
    user = next((u for u in users if u.get("user_id") == user_id), None)
    
    if not user:
        logger.warning(f"User history fetch failed: User {user_id} not found.")
        return {"success": False, "error": "User not found."}
        
    return {"success": True, "history": user.get("history", [])}

def _check_duplicate(user_id: str, target_book: dict, users: list) -> bool:
    user_record = next((u for u in users if u.get("user_id") == user_id), None)
    if not user_record or not user_record.get("history"):
        return False

    target_isbn = str(target_book.get("isbn", "")).strip().lower()
    for record in user_record.get("history", []):
        if str(record.get("isbn", "")).strip().lower() == target_isbn and record.get("action") in ["BUY", "ISSUE"]:
            return True
    return False

def _generate_invoice_data(action: str, book: dict, price: float, user_id: str, shipping_address: Optional[str] = None) -> dict:
    invoice = {
        "invoice_id": f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:4]}",
        "date_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_id": user_id,
        "action": action,
        "book_id": book.get('book_id', 'N/A'),
        "book_title": book.get('book_title') or book.get('title', 'N/A'),
        "isbn": book.get('isbn'),
        "price": price
    }
    if shipping_address:
        invoice["shipping_address"] = shipping_address
    return invoice

def execute_purchase(user_id: str, isbn: str, shipping_address: Optional[str] = None) -> dict:
    books = load_books(BOOKS_FILE)
    users = load_users(USERS_FILE)
    
    user_record = next((u for u in users if u.get("user_id") == user_id), None)
    if not user_record:
        logger.warning(f"Purchase failed: User {user_id} not found.")
        return {"success": False, "error": "User not found. Please check the User ID."}

    target_book = next((b for b in books if b.get("isbn") == isbn), None)
    if not target_book:
        logger.warning(f"Purchase failed: Book with ISBN {isbn} not found.")
        return {"success": False, "error": "Book not found."}
        
    if target_book.get("quantity", 0) <= 0:
        logger.warning(f"Purchase failed: Book {isbn} is out of stock.")
        return {"success": False, "error": "Book is currently out of stock."}

    if _check_duplicate(user_id, target_book, users):
        logger.warning(f"Purchase failed: User {user_id} already has book {isbn} in history.")
        return {"success": False, "error": "User already owns or has issued this book."}
    
    # Determine shipping address (custom or registered address)
    final_shipping_address = shipping_address.strip() if (shipping_address and isinstance(shipping_address, str) and shipping_address.strip()) else user_record.get("address", "N/A")

    target_book["quantity"] -= 1
    price = target_book.get('price', 0.0)
    receipt = _generate_invoice_data("BUY", target_book, price, user_id, shipping_address=final_shipping_address)
    
    user_record.setdefault("history", []).append(receipt)
            
    _save_books(BOOKS_FILE, books)
    _save_users(USERS_FILE, users)
    
    logger.info(f"Purchase completed: User {user_id} bought ISBN {isbn} (${price}) - Shipping: '{final_shipping_address}'")
    return {"success": True, "receipt": receipt}

def execute_issue(user_id: str, isbn: str) -> dict:
    books = load_books(BOOKS_FILE)
    users = load_users(USERS_FILE)
    
    # 1. FIX: Check if user exists BEFORE doing anything else!
    user_record = next((u for u in users if u.get("user_id") == user_id), None)
    if not user_record:
        logger.warning(f"Issue failed: User {user_id} not found.")
        return {"success": False, "error": "User not found. Please check the User ID."}
    
    # 2. Check book stock
    target_book = next((b for b in books if b.get("isbn") == isbn), None)
    if not target_book:
        logger.warning(f"Issue failed: Book with ISBN {isbn} not found.")
        return {"success": False, "error": "Book not found."}
        
    if target_book.get("quantity", 0) <= 0:
        logger.warning(f"Issue failed: Book {isbn} is out of stock.")
        return {"success": False, "error": "Book is currently out of stock."}
        
    if _check_duplicate(user_id, target_book, users):
        logger.warning(f"Issue failed: User {user_id} already owns or has issued book {isbn}.")
        return {"success": False, "error": "User already owns or has issued this book."}
        
    # 3. Process the transaction
    target_book["quantity"] -= 1
    due_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    
    receipt = _generate_invoice_data("ISSUE", target_book, 0.0, user_id)
    receipt["due_date"] = due_date
    
    # 4. We already know user_record exists, so we just append to it directly!
    user_record.setdefault("history", []).append(receipt)
            
    _save_books(BOOKS_FILE, books)
    _save_users(USERS_FILE, users)
    
    logger.info(f"Book issued successfully: User {user_id} issued ISBN {isbn} (Due: {due_date})")
    return {"success": True, "receipt": receipt}

def execute_return(user_id: str, isbn: str) -> dict:
    books = load_books(BOOKS_FILE)
    users = load_users(USERS_FILE)
    
    user_record = next((u for u in users if u.get("user_id") == user_id), None)
    if not user_record:
        logger.warning(f"Return failed: User {user_id} not found.")
        return {"success": False, "error": "User not found."}
        
    issued_record = next(
        (r for r in user_record.get("history", []) 
         if r.get("isbn") == isbn and r.get("action") == "ISSUE"), 
        None
    )
    
    if not issued_record:
        logger.warning(f"Return failed: No active issue record for user {user_id}, ISBN {isbn}.")
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
    
    logger.info(f"Book returned: User {user_id} returned ISBN {isbn} (Fine Paid: ${fine})")
    return {"success": True, "fine_paid": fine, "record": issued_record}

def fetch_book_history(identifier: str, search_by: str) -> dict:
    users = load_users(USERS_FILE)
    book_history = []
    ident_str = str(identifier).strip().lower()

    for user in users:
        for record in user.get("history", []):
            match = False
            # Check based on the admin's chosen search criteria
            if search_by == "book_id" and str(record.get("book_id", "")).strip() == str(identifier).strip():
                match = True
            elif search_by == "isbn" and str(record.get("isbn", "")).strip().lower() == ident_str:
                match = True
            elif search_by in ["title", "book_title"] and str(record.get("book_title") or "").strip().lower() == ident_str:
                match = True
            elif search_by == "user_id" and (str(user.get("user_id", "")).strip().lower() == ident_str or str(record.get("user_id", "")).strip().lower() == ident_str):
                match = True
            
            if match:
                # Attach the username to the record so the admin knows WHO did the action
                enriched_record = record.copy()
                enriched_record["username"] = user.get("username")
                book_history.append(enriched_record)

    if not book_history:
        return {"success": False, "error": "No transaction history found."}
    
    # Sort the history by date (newest first)
    book_history.sort(key=lambda x: x.get("date_time", ""), reverse=True)
    return {"success": True, "history": book_history}


# Add this to your existing auth_service.py

def authenticate_admin(username: str, password: str) -> dict:
    # Looks ONLY in ADMIN.json
    admins = load_users(ADMIN_FILE) 
    
    for a in admins:
        if a.get("username") == username and a.get("password") == password:
            return {"success": True, "admin_id": a.get("admin_id")}
            
    return {"success": False, "error": "Invalid admin credentials."}

def get_all_users_safe() -> list:
    """
    Retrieves all users but strips out sensitive data like passwords 
    before sending them to the client.
    """
    users = load_users(USERS_FILE)
    
    # Create a copy or strip passwords safely
    safe_users = []
    for user in users:
        safe_user = user.copy()
        safe_user.pop("password", None)  # Remove the password field
        safe_users.append(safe_user)
        
    return safe_users