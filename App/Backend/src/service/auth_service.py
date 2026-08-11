from src.service.file_handler import _save_users, load_users
from src.utility.input_validator import valid_username, valid_password
from config import USERS_FILE

def register_new_user(username: str, password: str) -> dict:
    """
    Creates a brand new user account if the details check out.
    
    It makes sure the username is unique and meets our length/character 
    requirements, checks the password strength, and then saves the new 
    profile to the database.

    Example:
        >>> register_new_user("ishita123", "securePass12")
        {"success": True, "message": "Account created successfully."}
    """
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
    """
    Checks if a user's login details are correct.
    
    It searches the database for a matching username and password combo. 
    If it finds a match, it lets them in!

    Example:
        >>> authenticate_user("ishita123", "securePass12")
        {"success": True, "username": "ishita123"}
    """
    users = load_users(USERS_FILE)
    user = next((u for u in users if u.get("username") == username and u.get("password") == password), None)
    
    if user:
        return {"success": True, "username": username}
    return {"success": False, "error": "Invalid username or password."}

def fetch_user_history(username: str) -> dict:
    """
    Grabs the complete transaction history for a specific user.
    
    It looks up the user's profile and hands back the list of every 
    book they have ever bought or borrowed.

    Example:
        >>> fetch_user_history("ishita123")
        {"success": True, "history": [{"action": "BUY", "book": "1984"}]}
    """
    users = load_users(USERS_FILE)
    user = next((u for u in users if u.get("username") == username), None)
    
    if not user:
        return {"success": False, "error": "User not found."}
        
    return {"success": True, "history": user.get("history", [])}