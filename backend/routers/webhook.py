import os

from typing import Annotated

from config import Config, get_settings
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

router = APIRouter(prefix="/webhook")

SettingsDep = Annotated[Config, Depends(get_settings)]

@router.get("/")
def verify_webhook(
    settings: SettingsDep,
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_verify_token: str = Query(..., alias="hub.verify_token"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
) -> PlainTextResponse:
    try:
        print("expected:", repr(settings.verify_token), "got:", repr(hub_verify_token))
        if hub_mode != "subscribe" or hub_verify_token != settings.verify_token:
            raise HTTPException(status_code=403, detail="Verification failed")
        return PlainTextResponse(hub_challenge)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Verification failed") from exc

@router.post("/")
async def handle_webhook(request: Request) -> PlainTextResponse:
    try:
        body = await request.json()
        data = await inspect_request(request)
        print("request data", data)
        print("request body", body)
        print("Webhook message received")
        
        return PlainTextResponse("Webhook received")

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
    print(settings)
    return PlainTextResponse("Webhook is working")