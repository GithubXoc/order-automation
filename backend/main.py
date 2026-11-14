from fastapi import FastAPI

app = FastAPI()

def main():
    print("Hello from backend!")


if __name__ == "__main__":
    main()

@app.get("/")
def hello():
    return {"message": "Hello from backend!"}

