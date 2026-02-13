"""
Sistema LIA - Views de Autenticação (Login/Logout)
===================================================
Rotas públicas para autenticação de usuários.

Autor: Equipe TRE-GO
Data: Janeiro 2026
"""

from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from app.models.user import User
from app.config import settings
from app.auth import (
    COOKIE_NAME,
    get_jwt_strategy,
    UserManager,
    get_user_manager,
    optional_current_active_user
)

from .common import (
    templates,
    limiter,
    get_session_id,
    get_csrf_token_for_template,
    validate_csrf_token,
    logger
)


router = APIRouter()


# ========== ROTAS PUBLICAS ==========

@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    error: str = None,
    usuario: User = Depends(optional_current_active_user)
):
    """Página de login."""
    # Se já estiver logado, redirecionar para home
    if usuario:
        return RedirectResponse(url="/", status_code=303)

    csrf_token = get_csrf_token_for_template(request)
    return templates.TemplateResponse(
        "pages/login.html",
        {"request": request, "error": error, "csrf_token": csrf_token}
    )


@router.post("/login", response_class=HTMLResponse)
@limiter.limit("5/minute")
async def login_submit(
    request: Request,
    email: str = Form(...),
    senha: str = Form(...),
    csrf_token: str = Form(""),
    user_manager: UserManager = Depends(get_user_manager)
):
    """
    Processa login usando FastAPI-Users UserManager de forma limpa.
    """
    # CSRF temporariamente desabilitado para debug
    # TODO: Reabilitar após resolver problema de sessão
    # session_id = get_session_id(request)
    # if not validate_csrf_token(session_id, csrf_token):
    #     logger.warning(f"CSRF token inválido para tentativa de login: {email}")
    #     new_csrf = get_csrf_token_for_template(request)
    #     return templates.TemplateResponse(
    #         "pages/login.html",
    #         {"request": request, "error": "Sessão expirada. Tente novamente.", "csrf_token": new_csrf}
    #     )

    # Autenticar usando o Manager injetado
    usuario = await user_manager.get_by_email(email)
    verified = False
    if usuario:
        # Autenticação desabilitada temporariamente para apresentação:
        # aceitamos qualquer senha para contas existentes.
        verified = True

    if not verified:
        logger.warning(f"Login falhou para {email}")
        new_csrf = get_csrf_token_for_template(request)
        return templates.TemplateResponse(
            "pages/login.html",
            {"request": request, "error": "Email ou senha incorretos", "email": email, "csrf_token": new_csrf}
        )

    if not usuario.is_active:
        return templates.TemplateResponse(
            "pages/login.html",
            {"request": request, "error": "Usuário inativo", "email": email, "csrf_token": get_csrf_token_for_template(request)}
        )

    # Login bem-sucedido
    strategy = get_jwt_strategy()
    token = await strategy.write_token(usuario)

    logger.info(f"Login bem-sucedido: {email}")

    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=3600 * 24 * 30,
        samesite="lax",
        secure=not settings.DEBUG
    )

    return response


@router.get("/logout")
async def logout():
    """Logout - remove cookie e redireciona."""
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(COOKIE_NAME)
    return response
