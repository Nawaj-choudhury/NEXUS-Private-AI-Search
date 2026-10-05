import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.auth import router as auth_router
from .api.routes import router
from .api.search import router as search_router
from .api.indexing import router as indexing_router
from .api.research import router as research_router
from .api.crawl import router as crawl_router
from .api.graph import router as graph_router
from .core.config import settings

app = FastAPI(title=settings.app_name)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"error": {"code": "VALIDATION_ERROR", "message": "Request validation failed."}})


@app.exception_handler(Exception)
async def safe_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logging.getLogger(__name__).error("Unhandled API error type=%s", type(exc).__name__)
    return JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_ERROR", "message": "The server could not complete the request."}})

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'"
    return response

app.include_router(auth_router)
app.include_router(router)
app.include_router(search_router)
app.include_router(indexing_router)
app.include_router(research_router)
app.include_router(crawl_router)
app.include_router(graph_router)