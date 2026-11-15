from fastapi import APIRouter
from database.database import SessionDep

from database.db_handlers import get_all_messages
router = APIRouter(prefix="/messages")

@router.get("/")
def get_messages_(session: SessionDep):
    try:
        return get_all_messages(session)
    except Exception:
        raise

@router.get("/pending")
def read_pending_messages(session: SessionDep):
    try:
        return get_all_messages(session)
    except Exception:
        raise

