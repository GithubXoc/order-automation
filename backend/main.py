from contextlib import asynccontextmanager
from pathlib import Path

from database.database import create_db_and_tables

from routers import messages, webhook

from fastapi import FastAPI
from fastapi.responses import FileResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(messages.router)
app.include_router(webhook.router)

def main():
    print("Hello from backend!")


if __name__ == "__main__":
    main()

@app.get("/privacy")
def privacy_policy():
    return FileResponse(Path(__file__).parent / "privacy-policy.html")

@app.get("/")
def hello():
    return {"message": "Hello from backend!"}

