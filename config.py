# config.py
import os

# Define file paths centrally
BOOKS_FILE = os.getenv("BOOKS_FILE", "MOCK_DATA.json")
USERS_FILE = os.getenv("USERS_FILE", "USERS.json")