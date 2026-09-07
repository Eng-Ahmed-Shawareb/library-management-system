# 📚 Library Management System

A complete desktop Library Management System built with **Python**,
**SQLite**, and a modern GUI powered by **CustomTkinter**.

## Features

- **Login screen** with hashed-password authentication (default admin account).
- **Dashboard** — live stats: distinct titles, total copies, available copies,
  members, active loans, overdue loans.
- **Books** — add / edit / delete / search catalogue entries.
- **Members** — add / edit / delete / search / suspend / reactivate members.
- **Loans** — issue and return loans with automatic due-date and fine calculation.
- **Reports** — overdue-loan report and CSV export for books and loans.
- **SQLite database** (`library.db`, created automatically on first run) with
  foreign-key constraints protecting data integrity (e.g. you can't delete a
  book or member that still has loan history).

## Validation rules built in

**Books**
- Title, author, category required; author limited to letter-based names.
- ISBN must be a real ISBN-10 or ISBN-13 (checksum digit is verified, not
  just length).
- Publish year must be between 1450 and the current year.
- Total copies must be a positive whole number (max 1000); ISBN must be unique.
- Total copies can't be lowered below the number of copies currently on loan.
- A book with any loan history (active or past) can't be deleted, to preserve
  records — set its status/copies to 0 instead.

**Members**
- Full name: letters/spaces/hyphens only, 2–100 characters.
- Email must match a valid address format and be unique.
- Phone must be 7–15 digits (optionally starting with `+`).
- Membership type must be one of Regular / Student / Faculty / Senior.
- Max books allowed: 1–20.
- A member's borrowing limit can't be lowered below their current active-loan count.
- A member with loan history can't be deleted — suspend them instead.

**Loans**
- Loan period: 1–90 days.
- Can't issue a loan if: the member is suspended, the book has 0 available
  copies, the member already has an active loan of the exact same book, or
  the member is already at their personal borrowing limit.
- Returning a loan is blocked if it was already marked returned.
- Overdue fines are calculated automatically at $0.50/day past the due date.

## Requirements

- Python 3.9+
- `tkinter` (bundled with most Python installs; on Ubuntu/Debian install
  with `sudo apt-get install python3-tk` if missing)
- `customtkinter` (see `requirements.txt`)

## Setup & run

```bash
pip install -r requirements.txt
python main.py
```

On first launch the SQLite database (`library.db`) is created automatically
in the project folder, along with a default librarian account:

- **Username:** `admin`
- **Password:** `admin123`

## Project structure

```
library_management_system/
├── main.py              # Entry point (login -> main app)
├── database.py           # SQLite schema + connection helper
├── validators.py         # All input/business-rule validation
├── db_manager.py          # CRUD + business logic (books, members, loans)
├── requirements.txt
└── gui/
    ├── style.py           # Shared colors/fonts
    ├── widgets.py         # Reusable FormDialog, styled Treeview, alerts
    ├── login.py           # Login screen
    ├── app.py             # Main window + sidebar navigation
    ├── dashboard_tab.py
    ├── books_tab.py
    ├── members_tab.py
    ├── loans_tab.py
    └── reports_tab.py
```

## Notes

- Fine rate ($0.50/day) and default loan length (14 days) can be adjusted
  in `db_manager.py` (`FINE_PER_DAY`) and in the "Issue Loan" dialog.
- To reset the database, simply delete `library.db` and restart the app.
