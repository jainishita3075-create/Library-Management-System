from Utility.file_handler import load_users, _save_users
from Utility.input_validator import valid_username, valid_password
from config import USERS_FILE

def register_new_user(username: str, password: str) -> dict:
    """Validates and registers a new user."""
    users = load_users(USERS_FILE)
    
    if not valid_username(username):
        return {"success": False, "error": "Username must be at least 8 chars, 5 letters, and 2 digits."}
        
    if any(u.get("username") == username for u in users):
        return {"success": False, "error": "Username already exists."}
        
    if not valid_password(password):
        return {"success": False, "error": "Invalid password format."}
        
    users.append({"username": username, "password": password, "history": []})
    
    if _save_users(USERS_FILE, users):
        return {"success": True, "message": "Account created successfully."}
    
    return {"success": False, "error": "Failed to save user data."}

def authenticate_user(username: str, password: str) -> dict:
    """Authenticates a user's credentials."""
    users = load_users(USERS_FILE)
    user = next((u for u in users if u.get("username") == username and u.get("password") == password), None)
    
    if user:
        return {"success": True, "username": username}
    return {"success": False, "error": "Invalid username or password."}

def fetch_user_history(username: str) -> dict:
    """Retrieves the transaction history for a specific user."""
    users = load_users(USERS_FILE)
    user = next((u for u in users if u.get("username") == username), None)
    
    if not user:
        return {"success": False, "error": "User not found."}
        
    return {"success": True, "history": user.get("history", [])}