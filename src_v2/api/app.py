from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src_v2.api.routes import router
from src_v2.config.settings import settings

def create_app() -> FastAPI:
    app = FastAPI(
        title="WhisperEngine Chat API",
        version="2.0.0",
        description="API for interacting with WhisperEngine characters"
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for now
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routes
    app.include_router(router)

    return app

app = create_app()
