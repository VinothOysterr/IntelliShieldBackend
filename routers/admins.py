from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from datetime import date, timedelta
from jose import JWTError, jwt
import logging

import models
import schemas
from dependencies import get_db
from utils import create_access_token, blacklist_token, is_token_blacklisted

logger = logging.getLogger(__name__)

oauth2_scheme_admin = OAuth2PasswordBearer(tokenUrl="/admins/login")

router = APIRouter()

@router.post("/login", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    admin = authenticate_admin(db, form_data.username, form_data.password)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": admin.username, "lic": admin.number_of_licenses}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "admin_id": admin.id, "location": admin.location}

def authenticate_admin(db: Session, username: str, password: str):
    admin = db.query(models.Admin).filter(models.Admin.username == username).first()
    if not admin:
        logger.info(f"Admin not found for username: {username}")
        return False
    if not admin.check_password(password):
        logger.info(f"Password mismatch for username: {username}")
        return False
    return admin

@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme_admin)):
    if is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token already blacklisted",
        )
    blacklist_token(token)
    return {"msg": "Logged out successfully"}

@router.post("/", response_model=schemas.AdminResponse)
async def create_admin(admin: schemas.AdminCreate, db: Session = Depends(get_db)):
    db_admin = db.query(models.Admin).filter(models.Admin.username == admin.username).first()
    if db_admin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    new_admin = models.Admin(
        username=admin.username,
        email=admin.email,
        full_name=admin.full_name,
        location=admin.location,
        is_active=True,
        number_of_licenses=admin.number_of_licenses,
        created_at=date.today(),
        updated_at=date.today()
    )
    new_admin.set_password(admin.password)
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    return new_admin

@router.get("/", response_model=List[schemas.AdminResponse])
async def read_admins(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    admins = db.query(models.Admin).offset(skip).limit(limit).all()
    return admins

@router.get("/admin_list", response_model=List[schemas.AdminListResponse])
async def read_admins(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    admins = db.query(models.Admin).offset(skip).limit(limit).all()
    admin_lists = [
        {
            "username": admin.username,
            "location": admin.location,
            "license_count": admin.number_of_licenses
        }
        for admin in admins
    ]
    return admin_lists

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
