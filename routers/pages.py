"""認証付き HTML ページのルーター（/docs, /dashboard, ログイン/ログアウト）。"""

from pathlib import Path

from fastapi import APIRouter, Cookie, Form, Request
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from auth import make_token, verify_session
from config import ADMIN_USERNAME, ADMIN_PASSWORD, SESSION_MAX_AGE

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")


# ── /docs ────────────────────────────────────────────────────────────────────

@router.get("/docs", response_class=HTMLResponse, include_in_schema=False)
async def docs_page(request: Request, session: str | None = Cookie(default=None)):
    if not verify_session(session):
        return templates.TemplateResponse(
            request, "login.html",
            {"error": False, "login_action": "/docs/login"},
        )
    return templates.TemplateResponse(request, "docs.html")


@router.post("/docs/login", response_class=HTMLResponse, include_in_schema=False)
async def docs_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        response = RedirectResponse(url="/docs", status_code=303)
        response.set_cookie(
            key="session",
            value=make_token(ADMIN_USERNAME),
            httponly=True,
            samesite="lax",
            max_age=SESSION_MAX_AGE,
        )
        return response
    return templates.TemplateResponse(
        request, "login.html",
        {"error": True, "login_action": "/docs/login"},
        status_code=401,
    )


@router.get("/docs/logout", include_in_schema=False)
async def docs_logout():
    response = RedirectResponse(url="/docs", status_code=303)
    response.delete_cookie("session")
    return response


@router.get("/dashboard/logout", include_in_schema=False)
async def dashboard_logout():
    response = RedirectResponse(url="/dashboard/login", status_code=303)
    response.delete_cookie("session")
    return response


@router.get("/openapi.json", include_in_schema=False)
async def openapi_schema(request: Request, session: str | None = Cookie(default=None)):
    if not verify_session(session):
        return HTMLResponse("Unauthorized", status_code=401)
    # 循環インポートを避けるため遅延インポート
    import main as _main
    return get_openapi(title=_main.app.title, version=_main.app.version, routes=_main.app.routes)


# ── /dashboard ───────────────────────────────────────────────────────────────

@router.get("/dashboard/login", response_class=HTMLResponse, include_in_schema=False)
async def dashboard_login_page(request: Request):
    return templates.TemplateResponse(
        request, "login.html",
        {"error": False, "login_action": "/dashboard/login"},
    )


@router.post("/dashboard/login", response_class=HTMLResponse, include_in_schema=False)
async def dashboard_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        response = RedirectResponse(url="/dashboard", status_code=303)
        response.set_cookie(
            key="session",
            value=make_token(ADMIN_USERNAME),
            httponly=True,
            samesite="lax",
            max_age=SESSION_MAX_AGE,
        )
        return response
    return templates.TemplateResponse(
        request, "login.html",
        {"error": True, "login_action": "/dashboard/login"},
        status_code=401,
    )


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, session: str | None = Cookie(default=None)):
    if not verify_session(session):
        return RedirectResponse(url="/dashboard/login", status_code=303)
    return templates.TemplateResponse(request, "dashboard.html")
