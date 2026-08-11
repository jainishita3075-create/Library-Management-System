from fastapi import APIRouter, HTTPException, status
from src.service import auth_service


router = APIRouter()


# ============================================================
# REGISTER
# ============================================================

@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED
)
def api_register_user(credentials: dict):
    """
    Register a new user.

    Expected JSON:

    {
        "username": "ishita",
        "password": "12345"
    }
    """

    username = credentials.get("username")
    password = credentials.get("password")

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password are required."
        )

    result = auth_service.register_new_user(
        username,
        password
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )

    return {
        "message": result["message"]
    }


# ============================================================
# LOGIN
# ============================================================

@router.post("/login")
def api_login_user(credentials: dict):
    """
    Login an existing user.

    Expected JSON:

    {
        "username": "ishita",
        "password": "12345"
    }
    """

    username = credentials.get("username")
    password = credentials.get("password")

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password are required."
        )

    result = auth_service.authenticate_user(
        username,
        password
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["error"]
        )

    return {
        "message": "Login successful",
        "username": result["username"]
    }


# ============================================================
# USER HISTORY
# ============================================================

@router.get("/{username}/history")
def api_get_history(username: str):
    """
    Get the purchase/issue history of a user.
    """

    result = auth_service.fetch_user_history(username)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )

    return {
        "history": result["history"]
    }