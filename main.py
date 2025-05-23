from fastapi import FastAPI
import models
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from database import engine
from routers import users, admins, fire_extinguishers, monthly_activity, super_admin

app = FastAPI()

# List of allowed origins (you can add more origins as needed)
origins = [
    "http://localhost:3000",  # React frontend
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=engine)

app.include_router(super_admin.router, prefix="/godmode", tags=["Super User"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(admins.router, prefix="/admins", tags=["Admins"])
app.include_router(fire_extinguishers.router, prefix="/fireextinguishers", tags=["Fire Extinguishers"])
app.include_router(monthly_activity.router, prefix="/monthlyactivity", tags=["Monthlyactivity"])
app.include_router(admins.router, prefix="/token", tags=["token"], include_in_schema=False)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="IntelliShield API",
        version="1.0.0",
        description="This was the custom API made by DB Productions",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearerUser": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/users/login"
                }
            }
        },
        "OAuth2PasswordBearerAdmin": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/admins/login"
                }
            }
        },
    }
    openapi_schema["security"] = [
        {"OAuth2PasswordBearerUser": []},
        {"OAuth2PasswordBearerAdmin": []},
    ]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=6547, reload=True)
