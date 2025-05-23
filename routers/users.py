from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from datetime import date, timedelta
import logging

import models
import schemas
from dependencies import get_db
from utils import create_access_token, blacklist_token, is_token_blacklisted

logger = logging.getLogger(__name__)

router = APIRouter()

# OAuth2PasswordBearer for user login
oauth2_scheme_user = OAuth2PasswordBearer(tokenUrl="/users/login")

@router.post("/login", response_model=schemas.UserToken)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "username": user.username}

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        logger.info(f"User not found for username: {username}")
        return False
    if not user.check_password(password):
        logger.info(f"Password mismatch for username: {username}")
        return False
    return user

@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme_user)):
    if is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token already blacklisted",
        )
    blacklist_token(token)
    return {"msg": "Logged out successfully"}

@router.post("/", response_model=schemas.UserResponse)
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    
    new_user = models.User(
        username=user.username, 
        name=user.name, 
        mobile=user.mobile, 
        doj = user.doj,
        role=user.role if user.role else "Unknown",
        created_at=date.today(),
        updated_at=date.today()
    )
    new_user.set_password(user.password)
    new_user.encrypt_aadhaar(user.aadhaar)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.get("/", response_model=List[schemas.UserResponse])
async def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

@router.get("/protected")
async def protected_route(request: Request, db: Session = Depends(get_db)):
    token = request.headers.get("Authorization")
    if token and token.startswith("Bearer "):
        token = token[len("Bearer "):]
    if not token or is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is blacklisted or missing",
        )
    # Your endpoint logic here
    return {"message": "This is a protected route"}