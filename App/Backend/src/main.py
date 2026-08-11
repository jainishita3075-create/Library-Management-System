from fastapi import FastAPI

from src.router.books import router as books_router
from src.router.users import router as users_router


app = FastAPI()

app.include_router(
    books_router,
    prefix="/books",
    tags=["Books"]
)

app.include_router(
    users_router,
    prefix="/users",
    tags=["Users"]
)


@app.get("/")
def home():
    return {
        "message": "BooksManager API is running"
    }
