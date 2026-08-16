from contextlib import asynccontextmanager
import time
from fastapi import FastAPI, Request #type: ignore
from src.router import books, users, admin
from src.utility.loggers import loggers

@asynccontextmanager
async def lifespan(app: FastAPI):
    loggers.info("Application is starting up!")
    yield
    loggers.info("Application is shutting down!")

app = FastAPI(
    title="Books Manager API",
    description="A simple and easy-to-use API for managing your book collection.",
    version="1.0.0",
    lifespan=lifespan
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = round((time.time() - start_time) * 1000, 2)
    loggers.info(f"{request.method} {request.url.path} - Status: {response.status_code} ({duration}ms)")
    return response

app.include_router(books.router, prefix="/books", tags=["Books"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(admin.router)

@app.get("/")
def root():
    return {"message": "Books Manager API is running"}