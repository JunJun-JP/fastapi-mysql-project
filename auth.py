import hashlib
import hmac

from fastapi import Cookie, HTTPException, status

from config import ADMIN_USERNAME, SESSION_SECRET


def make_token(username: str) -> str:
    return hmac.new(SESSION_SECRET.encode(), username.encode(), hashlib.sha256).hexdigest()


def verify_session(session: str | None) -> bool:
    if not session:
        return False
    return hmac.compare_digest(session, make_token(ADMIN_USERNAME))


def require_session(session: str | None = Cookie(default=None)) -> None:
    """FastAPI Depends 用。セッション Cookie がなければ 401 を返す。"""
    if not verify_session(session):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ログインが必要です",
        )
