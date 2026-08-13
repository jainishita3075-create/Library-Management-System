from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any

# Only import the service layer
from src.service import auth_service

router = APIRouter()

# ==========================================
# PYDANTIC MODELS (Validation & Schema)
# ==========================================
class UserRegistration(BaseModel):
    username: str = Field(..., min_length=5)
    password: str = Field(..., min_length=8)
    email: str # Use EmailStr if you install pydantic[email]
    phone_number: str = Field(..., min_length=10, max_length=15)
    address: str

class UserCredentials(BaseModel):
    username: str
    password: str

# ==========================================
# USER ENDPOINTS
# ==========================================
@router.post("/register", status_code=status.HTTP_201_CREATED)
def api_register_user(data: UserRegistration):
    result = auth_service.register_new_user(data.dict())
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"message": result["message"], "user_id": result.get("user_id")}

@router.post("/login")
def api_login_user(credentials: UserCredentials):
    result = auth_service.authenticate_user(credentials.username, credentials.password)
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["error"])
    return {"message": "Login successful.", "user_id": result["user_id"]}

@router.get("/{user_id}/history")
def api_get_history(user_id: str):
    result = auth_service.fetch_user_history(user_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return {"history": result["history"]}

# ==========================================
# ADMIN ENDPOINTS (Manage Users)
# ==========================================
@router.post("/admin/login")
def api_admin_login(credentials: UserCredentials):
    result = auth_service.authenticate_admin(credentials.username, credentials.password)
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["error"])
    return {"message": "Admin login successful."}

@router.get("/admin/all")
def api_get_all_users():
    return auth_service.get_all_users_safe()

@router.get("/admin/{user_id}/history")
def api_admin_get_user_history(user_id: str):
    result = auth_service.fetch_user_history(user_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return {"history": result["history"]}