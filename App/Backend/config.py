# config.py
import os

# Define file paths centrally
BOOKS_FILE = os.getenv("BOOKS_FILE", "file/MOCK_DATA.json")
USERS_FILE = os.getenv("USERS_FILE", "file/USERS.json")
ADMIN_FILE = os.getenv("ADMIN_FILE", "file/ADMIN.json")
LOG_FILE = os.getenv("LOG_FILE", "App.log")