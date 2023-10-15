from fastapi import FastAPI
from .api_routes import api_router

def create_app():

    app = FastAPI(
        description="Restaurant Status Monitoring System",
        root_path="/api/v1"
    )

    app.include_router(api_router)

    return app