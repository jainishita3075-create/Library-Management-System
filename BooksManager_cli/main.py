import questionary
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from services.file_handler import (
    load_books,
    load_users,
    view_books,
    search_books,
    filter_books,
    filter_by_range,
    add_book,
    update_book,
    delete_book,
    _save_books,
    _save_users
)
from Utility.input_validator import (
    prompt_string_only,
    prompt_non_empty_string,
    prompt_isbn,
    prompt_date
)
from Utility.numeric_validator import (
    prompt_float,
    prompt_int
)
from Utility.loggers import get_logger

# Initialize logger and rich console
logger = get_logger(__name__)
console = Console()

BOOKS_FILE = "MOCK_DATA.json"
USERS_FILE = "USERS.json"


# ==========================================
# 1. CUSTOMER PORTAL & AUTHENTICATION
# ==========================================

def browse_library(books_file: str):
    """
    Shows all books currently available in the library.

    Example:
        >>> browse_library("MOCK_DATA.json")
        # Displays the books stored in MOCK_DATA.json.

    Args:
        books_file: Path to the JSON file that stores the book catalog.

    Example:
        >>> browse_library("MOCK_DATA.json")
        # Prints an informational banner, then renders the full book
        # catalog table via view_books().
    """
    print("\n--- BROWSE LIBRARY ---")
    print("[INFO] Here you can view all available books in our catalog.")
    print("[INFO] Take note of the 'ISBN' if you wish to Buy or Issue a book.")
    print("-" * 40)

    view_books(books_file)


def check_duplicate_transaction(target_book: dict, users_file: str) -> bool:
    """
    Checks whether the selected book is already in the customer's history.

    Args:
        target_book: Book being bought or borrowed.
        users_file: JSON file where customer history is stored.

    Returns:
        True if the book is already in the history; otherwise False.

    Example:
        >>> check_duplicate_transaction({"isbn": "123", "book_title": "1984"}, "USERS.json")
        False
    """
    users = load_users(users_file)
    user_record = users[0] if users else None

    if not user_record or not user_record.get("history"):
        return False

    target_isbn = str(target_book.get("isbn", "")).strip().lower()
    target_title = str(target_book.get("book_title", "")).strip().lower()

    for record in user_record.get("history", []):
        rec_isbn = str(record.get("isbn", "")).strip().lower()
        rec_title = str(record.get("book", "")).strip().lower()

        # If either the ISBN or Title matches perfectly, they already have it
        if (target_isbn == rec_isbn and target_isbn != "") or (target_title == rec_title and target_title != ""):
            return True

    return False


def generate_invoice(action: str, book: dict, price: float) -> dict:
    """
    Creates a receipt for a book transaction and displays it on screen.

    Example:
        >>> generate_invoice("BUY", {"book_title": "1984", "isbn": "123"}, 15.99)
        # Shows a receipt and returns its details as a dictionary.

    Args:
        action: "BUY" or "ISSUE".
        book: The book dict involved in the transaction.
        price: The amount charged (0.0 for issued/borrowed books).

    Returns:
        A dict describing the transaction (invoice_id, date, action, book,
        isbn, price) suitable for appending to a user's history list.

    Example:
        >>> receipt = generate_invoice(
        ...     "Alice", "BUY", {"book_title": "1984", "isbn": "123", "author": "Orwell"}, 15.99
        ... )
        # Prints a receipt panel to the terminal and returns the receipt dict.
    """
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    invoice_id = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    receipt_content = (
        f"[bold]Invoice ID:[/bold] {invoice_id}\n"
        f"[bold]Date:[/bold] {date_now}\n"
        f"[bold]Customer:[/bold] Customer\n"
        f"----------------------------------------\n"
        f"[bold]Action:[/bold] {action.upper()}\n"
        f"[bold]Item:[/bold] {book.get('book_title')} by {book.get('author')}\n"
        f"[bold]ISBN:[/bold] {book.get('isbn')}\n"
        f"----------------------------------------\n"
        f"TOTAL PAID: ${price}"
    )

    console.print(Panel(receipt_content, title="TRANSACTION RECEIPT", border_style="green", expand=False))

    return {
        "invoice_id": invoice_id,
        "date": date_now,
        "action": action,
        "book": book.get('book_title'),
        "isbn": book.get('isbn'),
        "price": price
    }


def return_book(books_file: str, users_file: str):
    """
    Lets a logged-in user return a book they currently have issued,
    calculates any overdue fine, restores stock, and updates history.

    Args:
        books_file: Path to the JSON file that stores the book catalog.
        users_file: Path to the JSON file that stores user records.

    Example:
        >>> return_book("MOCK_DATA.json", "USERS.json")
        # Prompts the user to pick an issued book, computes any late fine,
        # then updates both the book stock and the user's history.
    """
    print("\n--- RETURN A BOOK ---")
    users = load_users(users_file)
    books = load_books(books_file)

    # Use the first customer record because login is no longer required.
    user_record = users[0] if users else None
    if not user_record or not user_record.get("history"):
        print("\nYou have no transaction history.")
        return

    # Filter for books that are currently issued and not yet returned
    issued_books = [record for record in user_record["history"] if record.get("action") == "ISSUE"]

    if not issued_books:
        print("\nYou have no currently issued books to return.")
        return

    # Build selection menu for issued books
    choices = []
    for i, record in enumerate(issued_books):
        title = record.get("book")
        due_date = record.get("due_date", "N/A")
        choices.append(questionary.Choice(f"{title} (Due: {due_date})", i))

    choices.append(questionary.Choice("Cancel", -1))

    selection_idx = questionary.select(
        "Select the book you want to return:",
        choices=choices
    ).ask()

    if selection_idx == -1 or selection_idx is None:
        print("Return process cancelled.")
        return

    selected_record = issued_books[selection_idx]

    # Calculate fine
    due_date_obj = datetime.strptime(selected_record["due_date"], "%Y-%m-%d").date()
    now_date = datetime.now().date()

    fine = 0.0
    overdue_days = 0
    if now_date > due_date_obj:
        overdue_days = (now_date - due_date_obj).days
        fine = overdue_days * 1.50  # $1.50 fine per overdue day

    if fine > 0:
        console.print(f"\n[bold red]This book is overdue by {overdue_days} day(s).[/bold red]")
        console.print(f"[bold red]You owe a late fine of ${fine:.2f}.[/bold red]")
        confirm = questionary.confirm("Do you want to pay the fine and return the book now?").ask()

        if not confirm:
            print("Return cancelled. You must pay the fine to complete the return.")
            return

        console.print(f"[bold green]Fine of ${fine:.2f} paid successfully.[/bold green]")
    else:
        confirm = questionary.confirm(f"Return '{selected_record.get('book')}'?").ask()
        if not confirm:
            return

    # 1. Update the book stock (+1)
    target_isbn = selected_record.get("isbn")
    for b in books:
        if b.get("isbn") == target_isbn:
            b["quantity"] += 1
            break

    # 2. Update the user's history record
    selected_record["action"] = "RETURNED"
    selected_record["return_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    selected_record["fine_paid"] = fine

    # Save updates
    _save_books(books_file, books)
    _save_users(users_file, users)

    console.print(f"\n[bold green]Successfully returned '{selected_record.get('book')}'. Thank you![/bold green]")
    logger.info(f"Customer returned book ISBN {target_isbn}. Fine paid: ${fine}")


def view_user_history(users_file: str):
    """
    Displays a table of a user's complete transaction history, showing
    context-appropriate details for BUY, ISSUE, and RETURNED records.

    Args:
        users_file: Path to the JSON file that stores user records.

    Example:
        >>> view_user_history("USERS.json")
        # Renders a rich table: Date | Action | Book Title | Details,
        # or prints a message if the user has no history yet.
    """
    print("\n--- YOUR TRANSACTION HISTORY ---")
    print("[INFO] This lists all your previous purchases, borrowed books, and returns.")
    print("-" * 40)

    users = load_users(users_file)
    user_data = users[0] if users else None

    if not user_data or not user_data.get("history"):
        print("\nYou have no transaction history yet.")
        return

    table = Table(title="Customer Transaction History", show_header=True, header_style="bold cyan")
    table.add_column("Date", style="dim")
    table.add_column("Action", style="bold")
    table.add_column("Book Title")
    table.add_column("Details", style="yellow")

    for record in user_data["history"]:
        # Dynamically handle formatting based on the action type
        if record.get('action') == "BUY":
            extra = f"Price: ${record.get('price', 0.0)}"
        elif record.get('action') == "RETURNED":
            ret_date = record.get('return_date', '').split()[0] if record.get('return_date') else "N/A"
            extra = f"Returned: {ret_date} (Fine: ${record.get('fine_paid', 0.0):.2f})"
        else:
            extra = f"Due: {record.get('due_date', 'N/A')}"

        table.add_row(record.get("date", "N/A"), record.get("action", "N/A"), record.get("book", "N/A"), extra)

    console.print(table)


def buy_book(books_file: str, users_file: str):
    """
    Sub-menu allowing a logged-in user to browse, search by Title/ISBN,
    and purchase a book, or check their purchase history.

    Args:
        books_file: Path to the JSON file that stores the book catalog.
        users_file: Path to the JSON file that stores user records.

    Example:
        >>> buy_book("MOCK_DATA.json", "USERS.json")
        # Opens an interactive menu; on "Enter ISBN or Title to Buy",
        # searches the catalog, confirms price, then records the sale.
    """
    while True:
        print("\n")
        action = questionary.select(
            "========== BUY A BOOK ==========\nWhat would you like to do?",
            choices=[
                questionary.Choice("1. Enter ISBN or Title to Buy", "buy"),
                questionary.Choice("2. Browse Available Books First", "browse"),
                questionary.Choice("3. View My Purchase History", "history"),
                questionary.Choice("4. Go Back", "back")
            ]
        ).ask()

        if action == "back" or action is None:
            break
        elif action == "browse":
            view_books(books_file)
        elif action == "history":
            view_user_history( users_file)
        elif action == "buy":
            books = load_books(books_file)
            users = load_users(users_file)
            if not users:
                users.append({"username": "customer", "history": []})

            while True:
                print("\n[REQUIREMENTS] You can search using the exact ISBN or Book Title.")
                query = input("Enter ISBN or Title (or type '0' to cancel): ").strip()

                if query == "0" or query == "000-0":
                    break
                if not query:
                    print("[!] Input cannot be empty.")
                    continue

                # Search by exact ISBN or partial Title match
                q_lower = query.lower()
                matches = [
                    b for b in books
                    if b.get("isbn") == query or q_lower in str(b.get("book_title", "")).lower()
                ]

                if not matches:
                    print("\n[!] Error: Book not found in the library catalog.")
                    retry = questionary.confirm("Do you want to try again?").ask()
                    if retry:
                        continue
                    else:
                        break

                target_book = None
                # If only one match, select it automatically
                if len(matches) == 1:
                    target_book = matches[0]
                else:
                    # If multiple matches, let the user choose from a list
                    choices = [
                        questionary.Choice(f"{b.get('book_title')} (ISBN: {b.get('isbn')}) - ${b.get('price', 0.0)}", b)
                        for b in matches
                    ]
                    choices.append(questionary.Choice("Cancel", None))

                    target_book = questionary.select(
                        "Multiple books found. Please select the correct one:",
                        choices=choices
                    ).ask()

                    if not target_book:
                        continue  # User chose to cancel selection

                if target_book.get("quantity", 0) <= 0:
                    print("\n[!] Error: Sorry, this book is currently out of stock.")
                    retry = questionary.confirm("Do you want to try a different book?").ask()
                    if retry:
                        continue
                    else:
                        break

                # DUPLICATE CHECK
                if check_duplicate_transaction(target_book, users_file):
                    console.print(f"\nNOTICE: You already have '{target_book.get('book_title')}' in your transaction history!")
                    proceed_anyway = questionary.confirm("Are you absolutely sure you want to BUY another copy?").ask()
                    if not proceed_anyway:
                        print("Transaction cancelled.")
                        break

                price = target_book.get('price', 0.0)
                confirm = questionary.confirm(f"The price for '{target_book.get('book_title')}' is ${price}. Proceed with purchase?").ask()

                if not confirm:
                    print("Transaction cancelled.")
                    break

                # Process transaction
                target_book["quantity"] -= 1
                _save_books(books_file, books)
                receipt = generate_invoice("BUY", target_book, price)

                for user in users:
                    if users and user is users[0]:
                        user.setdefault("history", []).append(receipt)
                        break

                _save_users(users_file, users)
                logger.info(f"Customer bought book ISBN {target_book.get('isbn')}")
                break


def issue_book(books_file: str, users_file: str):
    """
    Sub-menu allowing a logged-in user to browse, search by Title/ISBN,
    and issue (borrow) a book for 14 days, or check their issue history.

    Args:
        books_file: Path to the JSON file that stores the book catalog.
        users_file: Path to the JSON file that stores user records.

    Example:
        >>> issue_book("MOCK_DATA.json", "USERS.json")
        # Opens an interactive menu; on "Enter ISBN or Title to Issue",
        # searches the catalog, sets a 14-day due date, and records it.
    """
    while True:
        print("\n")
        action = questionary.select(
            "========== ISSUE A BOOK ==========\nWhat would you like to do?",
            choices=[
                questionary.Choice("1. Enter ISBN or Title to Issue", "issue"),
                questionary.Choice("2. Browse Available Books First", "browse"),
                questionary.Choice("3. View My Issue History", "history"),
                questionary.Choice("4. Go Back", "back")
            ]
        ).ask()

        if action == "back" or action is None:
            break
        elif action == "browse":
            view_books(books_file)
        elif action == "history":
            view_user_history( users_file)
        elif action == "issue":
            books = load_books(books_file)
            users = load_users(users_file)
            if not users:
                users.append({"username": "customer", "history": []})

            while True:
                print("\n[REQUIREMENTS] 1. You can search using the exact ISBN or Book Title.")
                print("[REQUIREMENTS] 2. Issued books are completely free of charge ($0.00).")
                print("[REQUIREMENTS] 3. You MUST return the book within exactly 14 days.")
                query = input("Enter ISBN or Title (or type '0' to cancel): ").strip()

                if query == "0" or query == "000-0":
                    break
                if not query:
                    print("[!] Input cannot be empty.")
                    continue

                q_lower = query.lower()
                matches = [
                    b for b in books
                    if b.get("isbn") == query or q_lower in str(b.get("book_title", "")).lower()
                ]

                if not matches:
                    print("\n[!] Error: Book not found in the library catalog.")
                    retry = questionary.confirm("Do you want to try again?").ask()
                    if retry:
                        continue
                    else:
                        break

                target_book = None
                if len(matches) == 1:
                    target_book = matches[0]
                else:
                    choices = [
                        questionary.Choice(f"{b.get('book_title')} (ISBN: {b.get('isbn')})", b)
                        for b in matches
                    ]
                    choices.append(questionary.Choice("Cancel", None))

                    target_book = questionary.select(
                        "Multiple books found. Please select the correct one:",
                        choices=choices
                    ).ask()

                    if not target_book:
                        continue

                if target_book.get("quantity", 0) <= 0:
                    print("\n[!] Error: Sorry, this book is currently out of stock.")
                    retry = questionary.confirm("Do you want to try a different book?").ask()
                    if retry:
                        continue
                    else:
                        break

                # DUPLICATE CHECK
                if check_duplicate_transaction(target_book, users_file):
                    console.print(f"\nNOTICE: You already have '{target_book.get('book_title')}' in your transaction history!")
                    proceed_anyway = questionary.confirm("Are you absolutely sure you want to ISSUE another copy?").ask()
                    if not proceed_anyway:
                        print("Transaction cancelled.")
                        break

                due_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
                confirm = questionary.confirm(f"Issue '{target_book.get('book_title')}' for 14 days? (Due Date: {due_date})").ask()

                if not confirm:
                    print("Transaction cancelled.")
                    break

                # Process Transaction
                target_book["quantity"] -= 1
                _save_books(books_file, books)
                receipt = generate_invoice("ISSUE", target_book, 0.0)
                receipt["due_date"] = due_date

                for user in users:
                    if users and user is users[0]:
                        user.setdefault("history", []).append(receipt)
                        break

                _save_users(users_file, users)
                logger.info(f"Customer issued book ISBN {target_book.get('isbn')}")
                break


def customer_dashboard():
    """
    Shows the customer menu for browsing and managing books.

    No login or registration is required.

    Example:
        >>> customer_dashboard()
        # Shows options to browse, buy, borrow, return, or view history.
    """
    while True:
        print("\n")
        choice = questionary.select(
            "========== CUSTOMER PORTAL ==========\nSelect a task:",
            choices=[
                questionary.Choice("1. Browse Library", "browse"),
                questionary.Choice("2. Buy a Book", "buy"),
                questionary.Choice("3. Issue (Borrow) a Book", "issue"),
                questionary.Choice("4. Return an Issued Book", "return"),
                questionary.Choice("5. View Complete History", "history"),
                questionary.Choice("6. Go Back", "back")
            ]
        ).ask()

        if choice == "browse":
            browse_library(BOOKS_FILE)
        elif choice == "buy":
            buy_book(BOOKS_FILE, USERS_FILE)
        elif choice == "issue":
            issue_book(BOOKS_FILE, USERS_FILE)
        elif choice == "return":
            return_book(BOOKS_FILE, USERS_FILE)
        elif choice == "history":
            view_user_history(USERS_FILE)
        elif choice == "back" or choice is None:
            print("Returning to Main Menu...")
            break


# ==========================================
# 2. BOOK MANAGER (ADMIN)
# ==========================================

def find_book_by_isbn_or_title(books_file: str, action_label: str = "book"):
    """
    Finds a book using its ISBN or part of its title.

    If more than one book matches, the admin can choose the correct one.

    Example:
        >>> find_book_by_isbn_or_title("MOCK_DATA.json", "update")
        # Finds the book that should be updated.

    find_book_by_isbn_or_title("MOCK_DATA.json", "update")
        "Enter ISBN or Book Title...", accepts "1984" or an
        ISBN, and returns the matching book dict (or None).
    """
    books = load_books(books_file)
    query = input(f"Enter ISBN or Book Title of the book to {action_label} (partial title is OK): ").strip()

    if not query:
        print("[!] Input cannot be empty.")
        return None

    q_lower = query.lower()
    matches = [
        b for b in books
        if str(b.get("isbn", "")) == query or q_lower in str(b.get("book_title", "")).lower()
    ]

    if not matches:
        print(f"\n[!] Error: No book found matching '{query}'.")
        return None

    if len(matches) == 1:
        return matches[0]

    choices = [
        questionary.Choice(f"{b.get('book_title')} (ISBN: {b.get('isbn')}) - ${b.get('price', 0.0)}", b)
        for b in matches
    ]
    choices.append(questionary.Choice("Cancel", None))

    selected = questionary.select(
        f"Multiple books matched '{query}'. Please select the correct one to {action_label}:",
        choices=choices
    ).ask()

    return selected


def book_manager_menu():
    """
    Shows the admin menu for managing books.

    The admin can view, search, filter, add, update, or delete books.

    Example:
        >>> book_manager_menu()
        # Opens the Book Manager menu.

    Example:
        >>> book_manager_menu()
        # Loops an interactive menu until "Return to Main Menu" is chosen.
    """
    while True:
        print("\n")
        choice = questionary.select(
            "========== ADMIN: BOOK MANAGER ==========\nSelect a task:",
            choices=[
                questionary.Choice("1. Load/Count Books", "1"),
                questionary.Choice("2. View Books", "2"),
                questionary.Choice("3. Search Books (Partial match on Title/Author)", "3"),
                questionary.Choice("4. Filter Books (Exact match or Range)", "4"),
                questionary.Choice("5. Add Book", "5"),
                questionary.Choice("6. Update Book", "6"),
                questionary.Choice("7. Delete Book", "7"),
                questionary.Choice("8. Return to Main Menu", "8")
            ]
        ).ask()

        if choice == "1":
            books = load_books(BOOKS_FILE)
            print("Books loaded successfully.")
            print("Total books:", len(books))

        elif choice == "2":
            view_books(BOOKS_FILE)

        elif choice == "3":
            query = input("Enter partial title or author to search (letters, numbers, or both): ").strip()
            if not query:
                print("[!] Input cannot be empty.")
                continue
            search_books(BOOKS_FILE, query)

        elif choice == "4":
            print("\n")
            sub_choice = questionary.select(
                "--- Filter Options ---",
                choices=[
                    questionary.Choice("1. Filter by Exact Genre", "1"),
                    questionary.Choice("2. Filter by Price Range", "2"),
                    questionary.Choice("3. Go Back", "3")
                ]
            ).ask()

            if sub_choice == "1":
                genre = prompt_string_only("Enter genre to filter by (letters only): ")
                filter_books(BOOKS_FILE, "genre", genre)
            elif sub_choice == "2":
                min_p = prompt_float("Enter minimum price: $", min_val=0.0)
                max_p = prompt_float(f"Enter maximum price (must be >= {min_p}): $", min_val=min_p)
                filter_by_range(BOOKS_FILE, "price", min_p, max_p)

        elif choice == "5":
            print("\n--- Enter Book Details ---")
            book = {
                "book_title": prompt_non_empty_string("Enter book title: "),
                "author": prompt_string_only("Enter author (letters only): "),
                "genre": prompt_string_only("Enter genre (letters only): "),
                "publication_date": prompt_date("Enter publication date (YYYY-MM-DD): "),
                "isbn": prompt_isbn("Enter ISBN: "),
                "price": prompt_float("Enter price: $", min_val=0.0),
                "quantity": prompt_int("Enter quantity: ", min_val=0),
                "language": prompt_string_only("Enter language (letters only): ")
            }
            add_book(BOOKS_FILE, book)

        elif choice == "6":
            # Look up the book by exact ISBN or by (partial) title, so an
            # admin who doesn't know the ISBN can still find the book.
            target_book = find_book_by_isbn_or_title(BOOKS_FILE, "update")

            if not target_book:
                continue

            isbn = target_book.get("isbn")

            print("\nEnter new details:")
            updated_data = {
                "book_title": prompt_non_empty_string("Enter book title: "),
                "author": prompt_string_only("Enter author (letters only): "),
                "genre": prompt_string_only("Enter genre (letters only): "),
                "publication_date": prompt_date("Enter publication date (YYYY-MM-DD): "),
                "price": prompt_float("Enter price: $", min_val=0.0),
                "quantity": prompt_int("Enter quantity: ", min_val=0),
                "language": prompt_string_only("Enter language (letters only): ")
            }

            # COMPARISON TABLE
            print("\n")
            table = Table(title="Please Review Your Changes", show_header=True, header_style="bold magenta")
            table.add_column("Field", style="cyan", justify="right")
            table.add_column("Previous Data", style="red")
            table.add_column("New Data", style="green")

            table.add_row("Title", str(target_book.get("book_title")), str(updated_data.get("book_title")))
            table.add_row("Author", str(target_book.get("author")), str(updated_data.get("author")))
            table.add_row("Genre", str(target_book.get("genre")), str(updated_data.get("genre")))
            table.add_row("Pub Date", str(target_book.get("publication_date")), str(updated_data.get("publication_date")))
            table.add_row("Price", f"${target_book.get('price', 0.0)}", f"${updated_data.get('price', 0.0)}")
            table.add_row("Quantity", str(target_book.get("quantity")), str(updated_data.get("quantity")))
            table.add_row("Language", str(target_book.get("language")), str(updated_data.get("language")))

            console.print(table)
            print("\n")

            # CONFIRMATION
            confirm = questionary.confirm("Do you want to apply these changes?").ask()

            if confirm:
                update_book(BOOKS_FILE, isbn, updated_data)
                console.print(f"[bold green]'{updated_data.get('book_title')}' (ISBN: {isbn}) updated successfully.[/bold green]")
                logger.info(f"Admin updated book ISBN {isbn}.")
            else:
                logger.info("User cancelled book update.")
                print("Update cancelled. Previous data was retained.")

        elif choice == "7":
            # Look up the book by exact ISBN or by (partial) title, so an
            # admin who doesn't know the ISBN can still find the book.
            target_book = find_book_by_isbn_or_title(BOOKS_FILE, "delete")

            if not target_book:
                continue

            isbn = target_book.get("isbn")

            # DISPLAY BOOK DETAILS TO BE DELETED
            print("\n")
            table = Table(title="Book Scheduled for Deletion", show_header=False)
            table.add_column("Field", style="cyan", justify="right")
            table.add_column("Value", style="red")

            table.add_row("Title:", str(target_book.get("book_title")))
            table.add_row("Author:", str(target_book.get("author")))
            table.add_row("Genre:", str(target_book.get("genre")))
            table.add_row("Price:", f"${target_book.get('price', 0.0)}")
            table.add_row("ISBN:", str(target_book.get("isbn")))

            console.print(table)
            print("\n")

            # CONFIRMATION
            confirm = questionary.confirm("Are you sure you want to PERMANENTLY delete this book?").ask()

            if confirm:
                delete_book(BOOKS_FILE, isbn)
                console.print(f"[bold green]'{target_book.get('book_title')}' (ISBN: {isbn}) was deleted successfully.[/bold green]")
                logger.info(f"Admin deleted book ISBN {isbn}.")
            else:
                logger.info("User cancelled book deletion.")
                print("Deletion cancelled. The book was retained.")

        elif choice == "8" or choice is None:
            print("Returning to Main Menu...")
            break


# ==========================================
# MASTER ENTRY
# ==========================================

def main():
    """
    Starts the Library & Bookstore application.

    The main menu lets you choose the customer area, admin book manager,
    or exit the program.

    Example:
        >>> main()
        # Displays the main menu and keeps running until Exit is selected.
    """
    logger.info("Application started.")

    while True:
        print("\n")
        choice = questionary.select(
            "========== LIBRARY & BOOKSTORE SYSTEM ==========\nSelect a Portal:",
            choices=[
                questionary.Choice("1. Customer Portal (Buy/Issue/Return)", "1"),
                questionary.Choice("2. Admin Portal (Book Manager)", "2"),
                questionary.Choice("3. Exit Application", "3")
            ]
        ).ask()

        if choice == "1":
            customer_dashboard()
        elif choice == "2":
            book_manager_menu()
        elif choice == "3" or choice is None:
            print("Exiting application. Goodbye!")
            logger.info("Application exited cleanly by user.")
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Application terminated abruptly via KeyboardInterrupt (Ctrl+C).")
        print("\nExiting application. Goodbye!")