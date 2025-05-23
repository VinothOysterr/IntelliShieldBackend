from fastapi import FastAPI, Depends, HTTPException, status, APIRouter, Request, Body
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
import logging


class LogoutRequest(BaseModel):
    session_id: int
    
# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# User Database (for demonstration purposes)
users = {}

# In-memory session storage (for demonstration purposes)
sessions = {}

# Create an instance of FastAPI
app = FastAPI()

# CORS middleware
origins = [
    "http://localhost:3000",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()

security = HTTPBasic()

def authenticate_user(credentials: HTTPBasicCredentials = Depends(security)):
    logger.debug(f"Authenticating user: {credentials.username}")
    user = users.get(credentials.username)
    if user is None or user["password"] != credentials.password:
        logger.debug(f"Authentication failed for user: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    logger.debug(f"Authenticated user: {credentials.username}")
    return user

def create_session(user_id: int):
    session_id = len(sessions) + random.randint(0, 1000000)
    sessions[session_id] = user_id
    logger.debug(f"Created session {session_id} for user_id {user_id}")
    return session_id

# Custom middleware for session-based authentication
def get_authenticated_user_from_session_id(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id is None or int(session_id) not in sessions:
        logger.debug(f"Invalid session ID: {session_id}")
        raise HTTPException(
            status_code=401,
            detail="Invalid session ID",
        )
    user = get_user_from_session(int(session_id))
    return user

# Use the valid session id to get the corresponding user from the users dictionary
def get_user_from_session(session_id: int):
    user = None
    for user_data in users.values():
        if user_data['user_id'] == sessions.get(session_id):
            user = user_data
            break
    return user

# Create a new dependency to get the session ID from cookies
def get_session_id(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id is None or int(session_id) not in sessions:
        logger.debug(f"Invalid session ID: {session_id}")
        raise HTTPException(status_code=401, detail="Invalid session ID")
    return int(session_id)

@app.post("/signup")
def sign_up(username: str = Body(...), password: str = Body(...)):
    logger.debug(f"Signing up user: {username}")
    user = users.get(username)
    if user:
        logger.debug(f"Username already exists: {username}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )
    new_user_id = len(users) + 1
    new_user = {
        "username": username,
        "password": password,
        "user_id": new_user_id
    }
    users[username] = new_user
    logger.debug(f"User registered successfully: {username}")
    return {"message": "User registered successfully"}

# Login endpoint - Creates a new session
@router.post("/login")
def login(user: dict = Depends(authenticate_user)):
    logger.debug(f"Logging in user: {user['username']}")
    session_id = create_session(user["user_id"])
    return {"message": "Logged in successfully", "session_id": session_id}

# Get current user endpoint - Returns the user corresponding to the session ID
@router.get("/getusers/me")
def read_current_user(user: dict = Depends(get_authenticated_user_from_session_id)):
    return user

# Protected endpoint - Requires authentication
@router.get("/protected")
def protected_endpoint(user: dict = Depends(get_authenticated_user_from_session_id)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authenticated")
    return {"message": "This user can connect to a protected endpoint after successfully authenticated", "user": user}

# Logout endpoint - Removes the session
@router.post("/logout")
def logout(request: LogoutRequest):
    session_id = request.session_id
    if session_id not in sessions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    sessions.pop(session_id)
    return {"message": "Logged out successfully", "session_id": session_id}

# Include the router in the app
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6547)
