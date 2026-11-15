from fastapi import APIRouter

# from database.database import get_messages, post_message
# from request.messages import MessageCreate
router = APIRouter(prefix="/messages")


# @router.post("/")
# async def create_message(body: MessageCreate, session: SessionDep):
#     try:
#         return post_message(session, body.message)
#     except Exception:
#         raise

# @router.get("/")
# def get_messages_(session: SessionDep):
#     try:
#         return get_messages(session)
#     except Exception:
#         raise

# @router.get("/pending")
# def read_pending_messages(session: SessionDep):
#     try:
#         return get_messages(session)
#     except Exception:
#         raise

