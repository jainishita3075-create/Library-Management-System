from fastapi import FastAPI #type: ignore
from src.router import books, users
from src.utility.loggers import loggers

app = FastAPI(
    title="Books Manager API",
    description="A simple and easy-to-use API for managing your book collection.",
    version="1.0.0"
)

app.include_router(books.router, prefix="/books", tags=["Books"])
app.include_router(users.router, prefix="/users", tags=["Users"])

@app.get("/")
def root():
    return {"message": "Books Manager API is running"}