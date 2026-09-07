"""
db_manager.py
-------------
All CRUD / business-logic operations for the Library Management System.
This is the only module that talks directly to the database on behalf
of the GUI; the GUI never writes raw SQL. Every write operation runs
its inputs through validators.py first, so bad data never reaches the
database.
"""

from datetime import datetime, timedelta

from database import get_connection
from validators import (
    ValidationError,
    validate_book_data,
    validate_member_data,
    validate_loan_period,
    validate_loan_request,
    validate_return_request,
    require_positive_int,
)

DATE_FMT = "%Y-%m-%d"
FINE_PER_DAY = 0.50  # currency units per day overdue


def _today_str():
    return datetime.now().strftime(DATE_FMT)


# ======================================================================
# BOOKS
# ======================================================================

def add_book(title, author, isbn, category, publisher, publish_year, total_copies):
    data = validate_book_data(title, author, isbn, category, publisher, publish_year, total_copies)
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM books WHERE isbn = ?", (data["isbn"],))
        if cur.fetchone():
            raise ValidationError(f"A book with ISBN '{data['isbn']}' already exists.")

        cur.execute("""
            INSERT INTO books (title, author, isbn, category, publisher,
                                publish_year, total_copies, available_copies, date_added)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["title"], data["author"], data["isbn"], data["category"],
            data["publisher"], data["publish_year"], data["total_copies"],
            data["total_copies"], _today_str()
        ))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_book(book_id, title, author, isbn, category, publisher, publish_year, total_copies):
    data = validate_book_data(title, author, isbn, category, publisher, publish_year, total_copies)
    conn = get_connection()
    try:
        cur = conn.cursor()
        existing = cur.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
        if existing is None:
            raise ValidationError("Book not found.")

        # ISBN uniqueness check excluding this record
        dup = cur.execute(
            "SELECT id FROM books WHERE isbn = ? AND id != ?", (data["isbn"], book_id)
        ).fetchone()
        if dup:
            raise ValidationError(f"Another book already uses ISBN '{data['isbn']}'.")

        currently_on_loan = existing["total_copies"] - existing["available_copies"]
        if data["total_copies"] < currently_on_loan:
            raise ValidationError(
                f"Cannot set total copies below {currently_on_loan}: that many copies are currently on loan."
            )
        new_available = data["total_copies"] - currently_on_loan

        cur.execute("""
            UPDATE books SET title=?, author=?, isbn=?, category=?, publisher=?,
                              publish_year=?, total_copies=?, available_copies=?
            WHERE id=?
        """, (
            data["title"], data["author"], data["isbn"], data["category"],
            data["publisher"], data["publish_year"], data["total_copies"],
            new_available, book_id
        ))
        conn.commit()
    finally:
        conn.close()


def delete_book(book_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        active = cur.execute(
            "SELECT COUNT(*) AS c FROM loans WHERE book_id=? AND status IN ('Active','Overdue')", (book_id,)
        ).fetchone()["c"]
        if active > 0:
            raise ValidationError("Cannot delete a book that currently has active loans.")

        history = cur.execute(
            "SELECT COUNT(*) AS c FROM loans WHERE book_id=?", (book_id,)
        ).fetchone()["c"]
        if history > 0:
            raise ValidationError(
                "This book has loan history and cannot be deleted (to preserve records). "
                "Set its total copies to 0 instead if it should no longer be loaned."
            )

        cur.execute("DELETE FROM books WHERE id=?", (book_id,))
        conn.commit()
    finally:
        conn.close()


def search_books(keyword=""):
    conn = get_connection()
    try:
        cur = conn.cursor()
        like = f"%{keyword.strip()}%"
        rows = cur.execute("""
            SELECT * FROM books
            WHERE title LIKE ? OR author LIKE ? OR isbn LIKE ? OR category LIKE ?
            ORDER BY title COLLATE NOCASE
        """, (like, like, like, like)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_book(book_id):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ======================================================================
# MEMBERS
# ======================================================================

def add_member(full_name, email, phone, address, membership_type, max_books_allowed):
    data = validate_member_data(full_name, email, phone, address, membership_type, max_books_allowed)
    conn = get_connection()
    try:
        cur = conn.cursor()
        if cur.execute("SELECT id FROM members WHERE email=?", (data["email"],)).fetchone():
            raise ValidationError(f"A member with email '{data['email']}' already exists.")

        cur.execute("""
            INSERT INTO members (full_name, email, phone, address, membership_type,
                                  max_books_allowed, status, join_date)
            VALUES (?, ?, ?, ?, ?, ?, 'Active', ?)
        """, (
            data["full_name"], data["email"], data["phone"], data["address"],
            data["membership_type"], data["max_books_allowed"], _today_str()
        ))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_member(member_id, full_name, email, phone, address, membership_type,
                   max_books_allowed, status):
    data = validate_member_data(full_name, email, phone, address, membership_type, max_books_allowed)
    if status not in ("Active", "Suspended"):
        raise ValidationError("Status must be 'Active' or 'Suspended'.")

    conn = get_connection()
    try:
        cur = conn.cursor()
        if cur.execute("SELECT id FROM members WHERE id=?", (member_id,)).fetchone() is None:
            raise ValidationError("Member not found.")
        dup = cur.execute(
            "SELECT id FROM members WHERE email=? AND id != ?", (data["email"], member_id)
        ).fetchone()
        if dup:
            raise ValidationError(f"Another member already uses email '{data['email']}'.")

        active_loans = cur.execute(
            "SELECT COUNT(*) AS c FROM loans WHERE member_id=? AND status='Active'", (member_id,)
        ).fetchone()["c"]
        if active_loans > data["max_books_allowed"]:
            raise ValidationError(
                f"Cannot lower borrowing limit below current active loans ({active_loans})."
            )

        cur.execute("""
            UPDATE members SET full_name=?, email=?, phone=?, address=?, membership_type=?,
                                max_books_allowed=?, status=?
            WHERE id=?
        """, (
            data["full_name"], data["email"], data["phone"], data["address"],
            data["membership_type"], data["max_books_allowed"], status, member_id
        ))
        conn.commit()
    finally:
        conn.close()


def delete_member(member_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        active = cur.execute(
            "SELECT COUNT(*) AS c FROM loans WHERE member_id=? AND status IN ('Active','Overdue')", (member_id,)
        ).fetchone()["c"]
        if active > 0:
            raise ValidationError("Cannot delete a member with active loans.")

        history = cur.execute(
            "SELECT COUNT(*) AS c FROM loans WHERE member_id=?", (member_id,)
        ).fetchone()["c"]
        if history > 0:
            raise ValidationError(
                "This member has loan history and cannot be deleted (to preserve records). "
                "Set their status to 'Suspended' instead if they should no longer borrow books."
            )

        cur.execute("DELETE FROM members WHERE id=?", (member_id,))
        conn.commit()
    finally:
        conn.close()


def search_members(keyword=""):
    conn = get_connection()
    try:
        like = f"%{keyword.strip()}%"
        rows = conn.execute("""
            SELECT * FROM members
            WHERE full_name LIKE ? OR email LIKE ? OR phone LIKE ?
            ORDER BY full_name COLLATE NOCASE
        """, (like, like, like)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_member(member_id):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM members WHERE id=?", (member_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ======================================================================
# LOANS
# ======================================================================

def issue_loan(book_id, member_id, loan_days=14):
    days = validate_loan_period(loan_days)
    conn = get_connection()
    try:
        cur = conn.cursor()
        book = cur.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()
        member = cur.execute("SELECT * FROM members WHERE id=?", (member_id,)).fetchone()

        active_loan_count = cur.execute(
            "SELECT COUNT(*) AS c FROM loans WHERE member_id=? AND status='Active'", (member_id,)
        ).fetchone()["c"]

        already_has_book = cur.execute(
            "SELECT COUNT(*) AS c FROM loans WHERE member_id=? AND book_id=? AND status='Active'",
            (member_id, book_id)
        ).fetchone()["c"] > 0

        validate_loan_request(member, book, active_loan_count, already_has_book)

        loan_date = datetime.now()
        due_date = loan_date + timedelta(days=days)

        cur.execute("""
            INSERT INTO loans (book_id, member_id, loan_date, due_date, status, fine_amount)
            VALUES (?, ?, ?, ?, 'Active', 0)
        """, (book_id, member_id, loan_date.strftime(DATE_FMT), due_date.strftime(DATE_FMT)))

        cur.execute(
            "UPDATE books SET available_copies = available_copies - 1 WHERE id=?", (book_id,)
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def return_loan(loan_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        loan = cur.execute("SELECT * FROM loans WHERE id=?", (loan_id,)).fetchone()
        validate_return_request(loan)

        today = datetime.now()
        due = datetime.strptime(loan["due_date"], DATE_FMT)
        overdue_days = max((today - due).days, 0)
        fine = round(overdue_days * FINE_PER_DAY, 2)

        cur.execute("""
            UPDATE loans SET return_date=?, status='Returned', fine_amount=?
            WHERE id=?
        """, (today.strftime(DATE_FMT), fine, loan_id))

        cur.execute(
            "UPDATE books SET available_copies = available_copies + 1 WHERE id=?", (loan["book_id"],)
        )
        conn.commit()
        return fine
    finally:
        conn.close()


def refresh_overdue_statuses():
    """Flags any active loan past its due date as 'Overdue' (cosmetic status only)."""
    conn = get_connection()
    try:
        today = _today_str()
        conn.execute("""
            UPDATE loans SET status='Overdue'
            WHERE status='Active' AND due_date < ?
        """, (today,))
        conn.commit()
    finally:
        conn.close()


def get_all_loans(keyword=""):
    conn = get_connection()
    try:
        like = f"%{keyword.strip()}%"
        rows = conn.execute("""
            SELECT loans.*, books.title AS book_title, books.isbn AS book_isbn,
                   members.full_name AS member_name, members.email AS member_email
            FROM loans
            JOIN books ON loans.book_id = books.id
            JOIN members ON loans.member_id = members.id
            WHERE books.title LIKE ? OR members.full_name LIKE ? OR loans.status LIKE ?
            ORDER BY loans.loan_date DESC
        """, (like, like, like)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_dashboard_stats():
    conn = get_connection()
    try:
        cur = conn.cursor()
        total_books = cur.execute("SELECT COALESCE(SUM(total_copies),0) AS c FROM books").fetchone()["c"]
        distinct_titles = cur.execute("SELECT COUNT(*) AS c FROM books").fetchone()["c"]
        total_members = cur.execute("SELECT COUNT(*) AS c FROM members").fetchone()["c"]
        active_loans = cur.execute("SELECT COUNT(*) AS c FROM loans WHERE status IN ('Active','Overdue')").fetchone()["c"]
        overdue_loans = cur.execute(
            "SELECT COUNT(*) AS c FROM loans WHERE status='Active' AND due_date < ?", (_today_str(),)
        ).fetchone()["c"]
        available_copies = cur.execute("SELECT COALESCE(SUM(available_copies),0) AS c FROM books").fetchone()["c"]

        return {
            "total_books": total_books,
            "distinct_titles": distinct_titles,
            "total_members": total_members,
            "active_loans": active_loans,
            "overdue_loans": overdue_loans,
            "available_copies": available_copies,
        }
    finally:
        conn.close()


def authenticate(username, password):
    import hashlib
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM librarians WHERE username=?", (username.strip(),)
        ).fetchone()
        if row is None:
            return False
        hashed = hashlib.sha256(password.encode()).hexdigest()
        return hashed == row["password_hash"]
    finally:
        conn.close()
