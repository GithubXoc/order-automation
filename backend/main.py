from pathlib import Path

from routers import messages, webhook

from fastapi import FastAPI
from fastapi.responses import FileResponse

app = FastAPI()
app.include_router(messages.router)
app.include_router(webhook.router)

@app.get("/privacy")
def privacy_policy():
    return FileResponse(Path(__file__).parent / "privacy-policy.html")

@app.get("/")
def hello():
    return {"message": "Hello from backend!"}

def main():
    print("Hello from backend!")

if __name__ == "__main__":
    main()