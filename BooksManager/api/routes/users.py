from fastapi import APIRouter, HTTPException, status

from api.schemas.models import UserCredentials
from api.services import auth_service


router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
def api_register_user(credentials: UserCredentials):
    result = auth_service.register_new_user(
        credentials.username,
        credentials.password
    )

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result["error"]
        )

    return {
        "message": result["message"]
    }


@router.post("/login")
def api_login_user(credentials: UserCredentials):
    result = auth_service.authenticate_user(
        credentials.username,
        credentials.password
    )

    if not result["success"]:
        raise HTTPException(
            status_code=401,
            detail=result["error"]
        )

    return {
        "message": "Login successful",
        "username": result["username"]
    }


@router.get("/{username}/history")
def api_get_history(username: str):
    result = auth_service.fetch_user_history(username)

    if not result["success"]:
        raise HTTPException(
            status_code=404,
            detail=result["error"]
        )

    return {
        "history": result["history"]
    }