from fastapi import Depends, HTTPException, status
from database import SessionLocal
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from models import Admin
from schemas import TokenData
from config import settings


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# def get_current_admin(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     try:
#         payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
#         print(f"Decoded payload: {payload}")
#         username: str = payload.get("sub")
#         if username is None:
#             print("Username not found in token payload")
#             raise credentials_exception
#         token_data = TokenData(username=username)
#     except JWTError as e:
#         print(f"JWTError: {str(e)}")
#         raise credentials_exception
#     admin = db.query(Admin).filter(Admin.username == token_data.username).first()
#     if admin is None:
#         print(f"Admin not found for username: {token_data.username}")
#         raise credentials_exception
#     return admin

def get_current_admin(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        print(f"Decoded payload: {payload}")
        username: str = payload.get("sub")
        license_limit: int = payload.get("lic", 0)
        if username is None:
            print("Username not found in token payload")
            raise credentials_exception
        token_data = TokenData(username=username, lic=license_limit)
    except JWTError as e:
        print(f"JWTError: {str(e)}")
        raise credentials_exception
    admin = db.query(Admin).filter(Admin.username == token_data.username).first()
    if admin is None:
        print(f"Admin not found for username: {token_data.username}")
        raise credentials_exception
    admin.license_limit = token_data.lic  # Attach license limit to the admin object
    return admin
