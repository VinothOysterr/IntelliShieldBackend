from fastapi import APIRouter, HTTPException, Depends, status, Request
from utils import create_access_token, blacklist_token, is_token_blacklisted
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from dependencies import get_db
import models
import schemas
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

oauth2_scheme_admin = OAuth2PasswordBearer(tokenUrl="/gomode/login")

router = APIRouter()

@router.post("/", response_model=schemas.SuperAdminResponse)
def create_super_admin(super_admin_create: schemas.SuperAdminCreate, db: Session = Depends(get_db)):
    # Check if the super admin already exists
    db_super_admin = db.query(models.SuperAdmin).filter(models.SuperAdmin.username == super_admin_create.username).first()
    if db_super_admin:
        raise HTTPException(status_code=400, detail="Username already taken")

    # Create the super admin instance
    new_super_admin = models.SuperAdmin(username=super_admin_create.username)
    new_super_admin.set_password(super_admin_create.password)

    db.add(new_super_admin)
    db.commit()
    db.refresh(new_super_admin)

    # Return a Pydantic model (SuperAdminResponse) that FastAPI can use for serialization
    return schemas.SuperAdminResponse(id=new_super_admin.id, username=new_super_admin.username)

@router.post("/login", response_model=schemas.SuperAdminToken)
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
        data={"sub": admin.username}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "admin_id": admin.id,
        "username": admin.username  # Include the username in the response
    }

def authenticate_admin(db: Session, username: str, password: str):
    admin = db.query(models.SuperAdmin).filter(models.SuperAdmin.username == username).first()
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