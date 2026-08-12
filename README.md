# 📚 Library Management System

A Python-based Library Management System that includes both a **CLI application** and a **FastAPI REST API**.

The system manages books, purchases, borrowing, returns, searching, filtering, and transaction history.

---

## ✨ Features

### 🖥️ CLI Application

The CLI provides two portals.

#### 👤 Customer Portal

- Browse Library
- Buy a Book
- Issue a Book
- Return an Issued Book
- View Complete History

#### 🛠️ Admin Portal

- Load / Count Books
- View Books
- Search Books by Title / Author
- Filter Books
- Add Book
- Update Book
- Delete Book

---

## 🌐 FastAPI 

The FastAPI backend provides REST APIs for book management.

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Root |
| GET | `/books/` | Get all books |
| POST | `/books/` | Add a book |
| GET | `/books/filter` | Filter books |
| GET | `/books/{isbn}` | Get book by ISBN |
| PUT | `/books/{isbn}` | Update a book |
| DELETE | `/books/{isbn}` | Delete a book |
| POST | `/books/buy` | Buy a book |

---

## ▶️ Run FastAPI and CLI

Go to the backend folder:

```bash

## ▶️ Run FastAPI

cd App/Backend

## Install dependencies: 

pip install -r requirement.txt

## Start the server: 

uvicorn src.main:app --reload

Open Swagger API documentation:

http://127.0.0.1:8000/docs

## ▶️ Run CLI 

Go to the CLI folder:

cd BooksManager_cli

Run:

python main.py
