📚 Bookstore & Library Manager
Welcome to the Bookstore & Library Manager. I built this application to serve as a complete, all-in-one book management system. It securely handles everything required to run daily operations—from processing customer purchases and 14-day book loans to helping admins keep their inventory perfectly synced.

The best part? It is built to be highly flexible. You can manage everything right in your terminal with a beautiful, interactive menu, or run it as a modern Web API ready to connect to a web browser or frontend application!

✨ What Can It Do?
🖥️ The Interactive Terminal App
If you like using the command line, you will love this. I used some cool tools to make the terminal look great and easy to navigate without needing a mouse[cite: 3].

For Customers: You can log in, browse the catalog, buy a book to keep, or "issue" a book to borrow it for exactly 14 days[cite: 3].

For Admins: You get a special menu to easily add new books, update prices, or remove old books from the shelf[cite: 3].

🌐 The Web API (FastAPI)
Behind the scenes, the project has a powerful engine that can talk to web browsers or other apps.

Smart Math: It automatically deducts books from the inventory when someone buys them, stops people from buying the same book twice, and even calculates a $1.50 late fine for every day a borrowed book is overdue!

Easy Searching: You can filter the catalog to find exactly what you want—like searching for "sci-fi books between $10 and $20."

Built-in Documentation: It automatically creates a web page where you can test all these features with the click of a button.

🗄️ Simple, Headache-Free Storage
You don't need to install a massive, complicated database to run this.

All the books and user profiles are safely saved in simple text files (MOCK_DATA.json and USERS.json)[cite: 2].

It plays it safe! Before you delete anything, it automatically creates a .bak backup file just in case you make a mistake[cite: 1].

It keeps a diary (app.log) of everything that happens, so you can always see who bought what[cite: 1].

🛠️ What I Used to Build This (Tech Stack)
Python: The core programming language.

FastAPI & Uvicorn: The magic ingredients that turn my Python code into a working web server.

Rich & Questionary: The tools that make the terminal menus colorful, interactive, and easy to navigate[cite: 3].

JSON: How the data is safely stored and read[cite: 2, 4, 6].

🚀 How to Run It on Your Computer
Prerequisites
Before you begin, make sure you have the following installed on your computer:

Git

Python 3.8 or higher

Installation Steps
1. Grab the code and go to the right folder:

Bash
git clone https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPOSITORY_NAME.git
cd YOUR_REPOSITORY_NAME/APP/Backend
(Note: Don't forget to replace the link above with your actual GitHub repository URL once you upload it!)

2. Create a safe workspace (Virtual Environment):
This keeps the project from messing with other Python stuff on your computer.

Bash
python -m venv venv

# If you are on Windows, run this to turn it on:
venv\Scripts\activate
# If you are on Linux/Mac, run this:
source venv/bin/activate
3. Install the tools:

Bash
pip install fastapi uvicorn pydantic rich questionary
💻 Turning It On!
Option A: I want to use the Web API
To turn on the web server, make sure you are in the Backend folder and run this command:

Bash
uvicorn src.main:app --reload
🎉 It's alive! Open your web browser and go to [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs). You will see a gorgeous dashboard where you can click around and test buying or borrowing books!

Option B: I want to use the Terminal Menu
(If you have set up your main.py to run the terminal loop, just run this!)

Bash
python src/main.py
📡 What the API Can Do (The Endpoints)
If you are a developer looking at the API, here is a quick menu of the available commands:

Managing Books (/books)

GET /books/: See every book we have.

GET /books/filter: Find specific books (by genre or price).

GET /books/{isbn}: Look up one specific book by its barcode (ISBN).

POST /books/: Admin only! Put a new book on the shelf.

PUT /books/{isbn}: Admin only! Fix a typo or change a price.

DELETE /books/{isbn}: Admin only! Remove a book permanently.

POST /books/buy: Buy a book (this lowers the stock).

POST /books/issue: Borrow a book for 14 days (this also lowers stock).

POST /books/return: Bring a book back and see if you owe a late fee.

Managing Users (/users)

POST /users/register: Sign up for a new account.

POST /users/login: Log into your account.

GET /users/{username}/history: See a receipt of every book you have ever bought, borrowed, or returned.

🔗 Production REST API Examples
To give you an idea of how the routing is structured in a production environment (like a live Library Management System website), here are 5 real-world examples of how these endpoints would look when hosted:

[https://lms.com/v1/books](https://lms.com/v1/books)

[https://lms.com/api/v1/order/](https://lms.com/api/v1/order/){id}

[http://lms.com/api/issuer?version=v1](http://lms.com/api/issuer?version=v1)

[https://lms.com/api/v1/transactionshistory](https://lms.com/api/v1/transactionshistory)

[https://lms.com/api/v1/issuer](https://lms.com/api/v1/issuer)
