from fastapi import FastAPI
from src.router import books

app = FastAPI(
    title="Books Manager API",
    description="A simple and easy-to-use API for managing your book collection.",
    version="1.0.0"
)

app.include_router(books.router, prefix="/books", tags=["Books"])

@app.get("/")
def root():
    """
    Check if the API is awake and running.
    
    Think of this as knocking on the API's door to see if anyone is home. 
    It just replies with a friendly message so you know everything is working.

    Example:
        >>> GET /
        {"message": "Books Manager API is running"}
    """
    return {"message": "Books Manager API is running"}