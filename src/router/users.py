from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from src.service import auth_service

router = APIRouter()

# Define exactly what information we expect from the user
class UserCredentials(BaseModel):
    username: str
    password: str

# ============================================================
# REGISTER
# ============================================================

@router.post("/register", status_code=status.HTTP_201_CREATED)
def api_register_user(credentials: UserCredentials):
    """
    Create a brand new user account.

    Hand over a username and a password, and this will set up a fresh profile so the user can start borrowing and buying books.

    Example:
        >>> POST /users/register
        Body: {"username": "ishita", "password": "securepassword123"}
    """
    if not credentials.username or not credentials.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="We need both a username and a password to sign you up."
        )

    result = auth_service.register_new_user(
        credentials.username,
        credentials.password
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )

    return {"message": result["message"]}


# ============================================================
# LOGIN
# ============================================================

@router.post("/login")
def api_login_user(credentials: UserCredentials):
    """
    Log into an existing account.

    Provide your registered username and password. If they match our records, you'll be granted access to your library profile.

    Example:
        >>> POST /users/login
        Body: {"username": "ishita", "password": "securepassword123"}
    """
    if not credentials.username or not credentials.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide both your username and password to log in."
        )

    result = auth_service.authenticate_user(
        credentials.username,
        credentials.password
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["error"]
        )

    return {
        "message": "Login successful. Welcome back!",
        "username": result["username"]
    }


# ============================================================
# USER HISTORY
# ============================================================

@router.get("/{username}/history")
def api_get_history(username: str):
    """
    Look up a user's past activity.

    Give us a username, and we will hand back a complete receipt history of every book they have ever bought or borrowed.

    Example:
        >>> GET /users/ishita/history
        {"history": [{"action": "BUY", "book": "1984", ...}]}
    """
    result = auth_service.fetch_user_history(username)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )

    return {"history": result["history"]}