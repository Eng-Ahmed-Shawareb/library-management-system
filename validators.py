"""
validators.py
--------------
Centralised validation logic for every entity in the system:
books, members, and loans. Every function raises a ValidationError
with a clear, user-facing message on failure so the GUI layer can
simply catch one exception type and display it.
"""

import re
from datetime import datetime


class ValidationError(Exception):
    """Raised when user-provided data fails a business or format rule."""
    pass


# ----------------------------------------------------------------------
# Generic helpers
# ----------------------------------------------------------------------

def require_non_empty(value, field_name):
    if value is None or str(value).strip() == "":
        raise ValidationError(f"{field_name} cannot be empty.")
    return str(value).strip()


def require_positive_int(value, field_name, allow_zero=False):
    try:
        ivalue = int(value)
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} must be a whole number.")
    if allow_zero:
        if ivalue < 0:
            raise ValidationError(f"{field_name} cannot be negative.")
    else:
        if ivalue <= 0:
            raise ValidationError(f"{field_name} must be greater than zero.")
    return ivalue


# ----------------------------------------------------------------------
# Book validation
# ----------------------------------------------------------------------

def validate_isbn(isbn):
    """
    Accepts ISBN-10 or ISBN-13 (with or without hyphens) and verifies
    the checksum digit, not just the length/format.
    """
    isbn = require_non_empty(isbn, "ISBN")
    cleaned = isbn.replace("-", "").replace(" ", "")

    if len(cleaned) == 10:
        if not re.fullmatch(r"\d{9}[\dXx]", cleaned):
            raise ValidationError("ISBN-10 must be 9 digits followed by a digit or 'X'.")
        total = 0
        for i, ch in enumerate(cleaned):
            digit = 10 if ch.upper() == "X" else int(ch)
            total += (10 - i) * digit
        if total % 11 != 0:
            raise ValidationError("ISBN-10 checksum is invalid. Please re-check the number.")

    elif len(cleaned) == 13:
        if not cleaned.isdigit():
            raise ValidationError("ISBN-13 must contain only digits.")
        total = 0
        for i, ch in enumerate(cleaned):
            digit = int(ch)
            total += digit if i % 2 == 0 else digit * 3
        if total % 10 != 0:
            raise ValidationError("ISBN-13 checksum is invalid. Please re-check the number.")
    else:
        raise ValidationError("ISBN must be exactly 10 or 13 digits long.")

    return cleaned


def validate_year(year, field_name="Publish year"):
    current_year = datetime.now().year
    iyear = require_positive_int(year, field_name)
    if iyear > current_year:
        raise ValidationError(f"{field_name} cannot be in the future ({current_year} is the latest valid year).")
    if iyear < 1450:  # roughly the age of the printing press
        raise ValidationError(f"{field_name} looks invalid (before 1450).")
    return iyear


def validate_book_data(title, author, isbn, category, publisher, publish_year, total_copies):
    """
    Validates a full book record. Returns a cleaned dict on success,
    raises ValidationError with the first problem found otherwise.
    """
    clean_title = require_non_empty(title, "Title")
    if len(clean_title) > 200:
        raise ValidationError("Title is too long (max 200 characters).")

    clean_author = require_non_empty(author, "Author")
    if not re.fullmatch(r"[A-Za-z\u00C0-\u024F .,'\-]+", clean_author):
        raise ValidationError("Author name contains invalid characters.")

    clean_isbn = validate_isbn(isbn)
    clean_category = require_non_empty(category, "Category")
    clean_publisher = (publisher or "").strip()
    clean_year = validate_year(publish_year)
    clean_copies = require_positive_int(total_copies, "Total copies")

    if clean_copies > 1000:
        raise ValidationError("Total copies seems unrealistically high (max 1000).")

    return {
        "title": clean_title,
        "author": clean_author,
        "isbn": clean_isbn,
        "category": clean_category,
        "publisher": clean_publisher,
        "publish_year": clean_year,
        "total_copies": clean_copies,
    }


# ----------------------------------------------------------------------
# Member validation
# ----------------------------------------------------------------------

EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PHONE_REGEX = re.compile(r"^\+?\d[\d\s\-]{6,14}\d$")
VALID_MEMBERSHIP_TYPES = ("Regular", "Student", "Faculty", "Senior")


def validate_email(email):
    email = require_non_empty(email, "Email")
    if not EMAIL_REGEX.fullmatch(email):
        raise ValidationError("Email address format is invalid (expected e.g. name@example.com).")
    return email.lower()


def validate_phone(phone):
    phone = require_non_empty(phone, "Phone number")
    if not PHONE_REGEX.fullmatch(phone.strip()):
        raise ValidationError("Phone number is invalid. Use 7-15 digits, optionally starting with '+'.")
    return phone.strip()


def validate_name(name, field_name="Full name"):
    name = require_non_empty(name, field_name)
    if len(name) < 2:
        raise ValidationError(f"{field_name} is too short.")
    if len(name) > 100:
        raise ValidationError(f"{field_name} is too long (max 100 characters).")
    if not re.fullmatch(r"[A-Za-z\u00C0-\u024F .,'\-]+", name):
        raise ValidationError(f"{field_name} may only contain letters, spaces, apostrophes and hyphens.")
    return name


def validate_member_data(full_name, email, phone, address, membership_type, max_books_allowed):
    clean_name = validate_name(full_name, "Full name")
    clean_email = validate_email(email)
    clean_phone = validate_phone(phone)
    clean_address = (address or "").strip()
    if len(clean_address) > 250:
        raise ValidationError("Address is too long (max 250 characters).")

    if membership_type not in VALID_MEMBERSHIP_TYPES:
        raise ValidationError(
            f"Membership type must be one of: {', '.join(VALID_MEMBERSHIP_TYPES)}."
        )

    clean_max_books = require_positive_int(max_books_allowed, "Max books allowed")
    if clean_max_books > 20:
        raise ValidationError("Max books allowed cannot exceed 20.")

    return {
        "full_name": clean_name,
        "email": clean_email,
        "phone": clean_phone,
        "address": clean_address,
        "membership_type": membership_type,
        "max_books_allowed": clean_max_books,
    }


# ----------------------------------------------------------------------
# Loan validation
# ----------------------------------------------------------------------

def validate_loan_period(loan_days):
    days = require_positive_int(loan_days, "Loan period (days)")
    if days > 90:
        raise ValidationError("Loan period cannot exceed 90 days.")
    return days


def validate_loan_request(member_row, book_row, active_loan_count, member_already_has_book):
    """
    Business-rule validation for issuing a new loan. Raises ValidationError
    on the first rule violated. Pure function: takes plain dict-like rows
    so it is easy to unit test without touching the database.
    """
    if member_row is None:
        raise ValidationError("Selected member does not exist.")
    if book_row is None:
        raise ValidationError("Selected book does not exist.")

    if member_row["status"] != "Active":
        raise ValidationError(
            f"Member '{member_row['full_name']}' is not active (status: {member_row['status']}) "
            "and cannot borrow books."
        )

    if book_row["available_copies"] <= 0:
        raise ValidationError(f"No available copies of '{book_row['title']}' left to loan.")

    if member_already_has_book:
        raise ValidationError(
            f"Member '{member_row['full_name']}' already has an active loan for this exact book."
        )

    if active_loan_count >= member_row["max_books_allowed"]:
        raise ValidationError(
            f"Member '{member_row['full_name']}' has reached their borrowing limit "
            f"({member_row['max_books_allowed']} books)."
        )


def validate_return_request(loan_row):
    if loan_row is None:
        raise ValidationError("Loan record does not exist.")
    if loan_row["status"] == "Returned":
        raise ValidationError("This loan has already been marked as returned.")
