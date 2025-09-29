# app/services/security.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.schemas import TokenData

# Secret key for JWT tokens
SECRET_KEY = "your-secret-key-here"  # In production, environment variable will be used
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Enhanced user database with roles
fake_users_db = {
    "doctor1": {
        "username": "doctor1",
        "full_name": "Dr. Sharma",
        "email": "dr.sharma@hospital.com",
        "abha_number": "1234-5678-9012",
        "hashed_password": pwd_context.hash("doctorpass"),
        "disabled": False,
        "role": "user",
        "permissions": ["read:terminology", "write:problem_list"]
    },
    "admin": {
        "username": "admin",
        "full_name": "System Administrator",
        "email": "admin@hospital.com",
        "abha_number": "0000-0000-0000",
        "hashed_password": pwd_context.hash("doctorpass"),
        "disabled": False,
        "role": "admin",
        "permissions": ["read:terminology", "write:problem_list", "admin:system", "sync:who_api"]
    },
    "doctor2": {
        "username": "doctor2",
        "full_name": "Dr. Patel",
        "email": "dr.patel@clinic.com",
        "abha_number": "9876-5432-1098",
        "hashed_password": pwd_context.hash("doctorpass"),
        "disabled": False,
        "role": "user",
        "permissions": ["read:terminology", "write:problem_list"]
    }
}

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_user(username: str):
    if username in fake_users_db:
        user_dict = fake_users_db[username]
        return user_dict
    return None

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        
        # Get user data from database
        user = get_user(username=username)
        if user is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    return user

async def get_current_active_user(current_user: dict = Depends(get_current_user)):
    if current_user.get("disabled"):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# ISO 22600 Compliance - Access Control
async def require_permission(permission: str, current_user: dict = Depends(get_current_active_user)):
    """Check if user has required permission (ISO 22600 compliance)"""
    user_permissions = current_user.get("permissions", [])
    if permission not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission '{permission}' required"
        )
    return current_user

# Specific permission checkers
async def require_admin_permission(current_user: dict = Depends(get_current_active_user)):
    return await require_permission("admin:system", current_user)

async def require_sync_permission(current_user: dict = Depends(get_current_active_user)):
    return await require_permission("sync:who_api", current_user)