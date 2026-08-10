# schemas/models.py
from pydantic import BaseModel
from typing import Optional

class BookModel(BaseModel):
    book_title: str
    author: str
    genre: str
    publication_date: str
    isbn: str
    price: float
    quantity: int
    language: str

class UserCredentials(BaseModel):
    username: str
    password: str

class TransactionRequest(BaseModel):
    username: str
    isbn: str