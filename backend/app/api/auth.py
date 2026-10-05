from fastapi import APIRouter, HTTPException, Request, Response

from backend.app.auth.dependencies import get_current_user
from backend.app.auth.service import AuthService
from backend.app.schemas.auth import AuthResponse, LoginRequest, MeResponse, RegisterRequest
from backend.app.core.config import settings

router = APIRouter(prefix="/api/auth")


def get_auth_service() -> AuthService:
    return AuthService(settings.database_path)


@router.post("/register", response_model=AuthResponse)
def register(payload: RegisterRequest, response: Response) -> AuthResponse:
    service = get_auth_service()
    user = service.register(payload.email, payload.password, response)
    return AuthResponse(authenticated=True, user={"user_id": user.user_id, "email": user.email})


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, response: Response) -> AuthResponse:
    service = get_auth_service()
    user = service.login(payload.email, payload.password, response)
    return AuthResponse(authenticated=True, user={"user_id": user.user_id, "email": user.email})


@router.post("/logout")
def logout(response: Response, request: Request) -> dict[str, bool]:
    service = get_auth_service()
    service.logout(request, response)
    return {"logged_out": True}


@router.get("/me", response_model=MeResponse)
def current_user(request: Request) -> MeResponse:
    user = get_current_user(request)
    return MeResponse(user_id=user.user_id, email=user.email, is_active=user.is_active)
