from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.core.security import decode_token
from src.core.settings import settings
from src.db.database import get_db
from src.services.auth_service import get_teacher_by_id


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_teacher(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Nao autenticado.")

    try:
        payload = decode_token(credentials.credentials, settings.AUTH_SECRET_KEY)
        teacher_id = int(payload["sub"])
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido.") from exc

    teacher = get_teacher_by_id(db, teacher_id)
    if not teacher:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Professor nao encontrado.")
    if not teacher["is_active"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Conta inativa.")
    return teacher
