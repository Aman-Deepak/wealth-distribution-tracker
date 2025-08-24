from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.openapi.utils import get_openapi

from app.api.v1.auth import router as auth_router
from app.api.v1.income import router as income_router
from app.api.v1.expense import router as expense_router
from app.api.v1.invest import router as invest_router
from app.api.v1.upload import router as upload_router
from app.api.v1.summary import router as summary_router
from app.api.v1.report import router as report_router
from app.api.v1.config import router as config_router

app = FastAPI(title="Wealth Tracker API")

# CORS if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(income_router)
app.include_router(expense_router)
app.include_router(invest_router)
app.include_router(upload_router)
app.include_router(summary_router)
app.include_router(report_router)
app.include_router(config_router)

# Optional: Customize OpenAPI to show Bearer token properly
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Wealth Tracker API",
        version="1.0.0",
        description="Manage your wealth efficiently",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            if method in ["get", "post", "put", "delete"]:
                openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
