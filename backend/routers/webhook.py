import os
import logging

from typing import Annotated

from database.database import SessionDep
from database.db_handlers import create_message
from utils.webhook_parser import parse_events
from core.config import Settings, get_settings
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import PlainTextResponse
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(prefix="/webhook")
logger = logging.getLogger(__name__)

SettingsDep = Annotated[Settings, Depends(get_settings)]

@router.get("/")
def verify_webhook(
    settings: SettingsDep,
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_verify_token: str = Query(..., alias="hub.verify_token"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
) -> PlainTextResponse:
    try:
        if hub_mode != "subscribe" or hub_verify_token != settings.verify_token:
            raise HTTPException(status_code=403, detail="Verification failed")
        return PlainTextResponse(hub_challenge)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Verification failed") from exc

@router.post("/")
async def handle_webhook(request: Request, session: SessionDep) -> PlainTextResponse:
    try:
        body = await request.json()
        for parsed_event in parse_events(body):
            await run_in_threadpool(create_message, session, parsed_event)
        
        return PlainTextResponse("Webhook received")

    except SQLAlchemyError as exc:
        logger.exception("Failed to save webhook messages")
        raise HTTPException(status_code=500, detail="Failed to save webhook messages") from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON") from exc

async def inspect_request(request: Request):
    # Read raw bytes or parse JSON safely
    raw_body = await request.body()
    try:
        json_body = await request.json()
    except Exception:
        json_body = None

    return {
        "method": request.method,
        "url": str(request.url),
        "base_url": str(request.base_url),
        "path_params": request.path_params,
        "query_params": dict(request.query_params),
        "headers": dict(request.headers),
        "cookies": request.cookies,
        "client": request.client,  # (host, port)
        "state": request.state._state,
        "body_raw": raw_body.decode("utf-8", errors="ignore"),
        "body_json": json_body,
    }

@router.get("/check")
def check_webhook(settings: SettingsDep,) -> PlainTextResponse:
    return PlainTextResponse("Webhook is working")