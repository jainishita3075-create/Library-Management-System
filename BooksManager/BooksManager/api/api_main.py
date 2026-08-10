# from fastapi import FastAPI
# from api.routes import books, users
# from Utility.loggers import get_logger

# # Initialize logger
# logger = get_logger(__name__)

# # Create the FastAPI instance
# app = FastAPI(
#     title="BooksManager API",
#     description="A modular REST API for managing books and users.",
#     version="1.0.0"
# )

# # Attach modules to the main router
# app.include_router(books.router, prefix="/books", tags=["Books"])
# app.include_router(users.router, prefix="/users", tags=["Users"])

# @app.get("/")
# def read_root():
#     """Health check route to verify the server is running."""
#     logger.info("Health check endpoint accessed.")
#     return {"status": "success", "message": "Welcome to the BooksManager API"}


from fastapi import FastAPI
from api.routes import books, users

app = FastAPI()

app.include_router(books.router)
app.include_router(users.router)


@app.get("/")
def root():
    return {
        "message": "Books Manager API is running"
    }