"""
books_tab.py
------------
CRUD screen for managing the book catalogue.
"""

import customtkinter as ctk
from tkinter import ttk

import db_manager
from validators import ValidationError
from gui import style
from gui.widgets import FormDialog, confirm_dialog, info, error


BOOK_FIELDS_TEMPLATE = [
    {"key": "title", "label": "Title"},
    {"key": "author", "label": "Author"},
    {"key": "isbn", "label": "ISBN (10 or 13 digits)"},
    {"key": "category", "label": "Category"},
    {"key": "publisher", "label": "Publisher"},
    {"key": "publish_year", "label": "Publish Year"},
    {"key": "total_copies", "label": "Total Copies"},
]


class BooksTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=style.CONTENT_BG)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(25, 10))

        title = ctk.CTkLabel(header, text="Books", font=style.font_title())
        title.pack(side="left")

        add_btn = ctk.CTkButton(header, text="+ Add Book", fg_color=style.PRIMARY,
                                 hover_color=style.PRIMARY_DARK, command=self._open_add_dialog)
        add_btn.pack(side="right")

        search_row = ctk.CTkFrame(self, fg_color="transparent")
        search_row.pack(fill="x", padx=30)
        self.search_entry = ctk.CTkEntry(search_row, placeholder_text="Search by title, author, ISBN or category...", width=400)
        self.search_entry.pack(side="left", pady=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh())

        table_frame = ctk.CTkFrame(self, fg_color=style.CARD_BG, corner_radius=12)
        table_frame.pack(fill="both", expand=True, padx=30, pady=15)

        columns = ("id", "title", "author", "isbn", "category", "year", "total", "available")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", style="Custom.Treeview")
        headings = ["ID", "Title", "Author", "ISBN", "Category", "Year", "Total", "Available"]
        widths = [40, 220, 150, 120, 110, 60, 60, 80]
        for col, head, w in zip(columns, headings, widths):
            self.tree.heading(col, text=head)
            self.tree.column(col, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10, side="left")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        action_row = ctk.CTkFrame(self, fg_color="transparent")
        action_row.pack(fill="x", padx=30, pady=(0, 20))
        ctk.CTkButton(action_row, text="Edit Selected", fg_color=style.WARNING,
                      command=self._open_edit_dialog).pack(side="left", padx=(0, 10))
        ctk.CTkButton(action_row, text="Delete Selected", fg_color=style.DANGER,
                      command=self._delete_selected).pack(side="left")

    def refresh(self):
        keyword = self.search_entry.get() if hasattr(self, "search_entry") else ""
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            books = db_manager.search_books(keyword)
        except Exception as e:
            error(str(e))
            return
        for b in books:
            self.tree.insert("", "end", values=(
                b["id"], b["title"], b["author"], b["isbn"], b["category"],
                b["publish_year"], b["total_copies"], b["available_copies"]
            ))

    def _selected_book_id(self):
        selection = self.tree.selection()
        if not selection:
            return None
        return self.tree.item(selection[0])["values"][0]

    def _open_add_dialog(self):
        def on_submit(values):
            db_manager.add_book(
                values["title"], values["author"], values["isbn"], values["category"],
                values["publisher"], values["publish_year"], values["total_copies"]
            )
            self.refresh()
            info("Book added successfully.")

        FormDialog(self, "Add New Book", BOOK_FIELDS_TEMPLATE, on_submit, submit_label="Add")

    def _open_edit_dialog(self):
        book_id = self._selected_book_id()
        if book_id is None:
            error("Please select a book to edit.")
            return
        book = db_manager.get_book(book_id)
        if book is None:
            error("Book not found (it may have been deleted).")
            self.refresh()
            return

        fields = []
        for f in BOOK_FIELDS_TEMPLATE:
            f2 = dict(f)
            f2["default"] = book[f["key"]]
            fields.append(f2)

        def on_submit(values):
            db_manager.update_book(
                book_id, values["title"], values["author"], values["isbn"], values["category"],
                values["publisher"], values["publish_year"], values["total_copies"]
            )
            self.refresh()
            info("Book updated successfully.")

        FormDialog(self, "Edit Book", fields, on_submit, submit_label="Save")

    def _delete_selected(self):
        book_id = self._selected_book_id()
        if book_id is None:
            error("Please select a book to delete.")
            return
        if not confirm_dialog(self, "Are you sure you want to delete this book?"):
            return
        try:
            db_manager.delete_book(book_id)
            self.refresh()
            info("Book deleted.")
        except ValidationError as e:
            error(str(e))
