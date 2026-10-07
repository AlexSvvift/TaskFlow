from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.config import Settings, get_settings
from app.database import create_database, initialize_database

BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / "web"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    engine, session_factory = create_database(settings.database_url)
    initialize_database(engine)

    application = FastAPI(
        title=settings.app_name,
        description="CRM для клиентов и заказов.",
        version="1.0.0",
    )
    application.state.settings = settings
    application.state.engine = engine
    application.state.session_factory = session_factory
    origins = settings.cors_origin_list()
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=origins != ["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(router)
    application.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

    @application.get("/", include_in_schema=False)
    def web_panel():
        return FileResponse(WEB_DIR / "index.html")

    return application


app = create_app()
