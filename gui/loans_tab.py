"""
loans_tab.py
------------
Screen for issuing new loans, returning books, and viewing loan history
with automatic overdue detection and fine calculation.
"""

import customtkinter as ctk
from tkinter import ttk

import db_manager
from validators import ValidationError
from gui import style
from gui.widgets import confirm_dialog, info, error


class LoansTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=style.CONTENT_BG)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(25, 10))
        title = ctk.CTkLabel(header, text="Loans", font=style.font_title())
        title.pack(side="left")

        issue_btn = ctk.CTkButton(header, text="+ Issue Loan", fg_color=style.PRIMARY,
                                   hover_color=style.PRIMARY_DARK, command=self._open_issue_dialog)
        issue_btn.pack(side="right")

        search_row = ctk.CTkFrame(self, fg_color="transparent")
        search_row.pack(fill="x", padx=30)
        self.search_entry = ctk.CTkEntry(search_row, placeholder_text="Search by book title, member name or status...", width=420)
        self.search_entry.pack(side="left", pady=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh())

        table_frame = ctk.CTkFrame(self, fg_color=style.CARD_BG, corner_radius=12)
        table_frame.pack(fill="both", expand=True, padx=30, pady=15)

        columns = ("id", "book", "member", "loan_date", "due_date", "return_date", "status", "fine")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", style="Custom.Treeview")
        headings = ["ID", "Book", "Member", "Loaned", "Due", "Returned", "Status", "Fine"]
        widths = [40, 200, 160, 90, 90, 90, 90, 60]
        for col, head, w in zip(columns, headings, widths):
            self.tree.heading(col, text=head)
            self.tree.column(col, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10, side="left")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        action_row = ctk.CTkFrame(self, fg_color="transparent")
        action_row.pack(fill="x", padx=30, pady=(0, 20))
        ctk.CTkButton(action_row, text="Mark as Returned", fg_color=style.SUCCESS,
                      command=self._return_selected).pack(side="left")

    def refresh(self):
        db_manager.refresh_overdue_statuses()
        keyword = self.search_entry.get() if hasattr(self, "search_entry") else ""
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            loans = db_manager.get_all_loans(keyword)
        except Exception as e:
            error(str(e))
            return
        for l in loans:
            self.tree.insert("", "end", values=(
                l["id"], l["book_title"], l["member_name"], l["loan_date"],
                l["due_date"], l["return_date"] or "-", l["status"], l["fine_amount"]
            ))

    def _selected_loan_id(self):
        selection = self.tree.selection()
        if not selection:
            return None
        return self.tree.item(selection[0])["values"][0]

    def _open_issue_dialog(self):
        books = [b for b in db_manager.search_books("") if b["available_copies"] > 0]
        members = [m for m in db_manager.search_members("") if m["status"] == "Active"]

        if not books:
            error("No books with available copies to loan.")
            return
        if not members:
            error("No active members available to receive a loan.")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Issue Loan")
        dialog.geometry("420x320")
        dialog.resizable(False, False)
        dialog.configure(fg_color=style.CONTENT_BG)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Issue New Loan", font=style.font_subtitle()).pack(pady=(20, 15))

        book_map = {f'{b["title"]} (ISBN {b["isbn"]}) - {b["available_copies"]} left': b["id"] for b in books}
        member_map = {f'{m["full_name"]} ({m["email"]})': m["id"] for m in members}

        book_row = ctk.CTkFrame(dialog, fg_color="transparent")
        book_row.pack(fill="x", padx=25, pady=6)
        ctk.CTkLabel(book_row, text="Book", width=90, anchor="w").pack(side="left")
        book_var = ctk.StringVar(value=list(book_map.keys())[0])
        ctk.CTkOptionMenu(book_row, values=list(book_map.keys()), variable=book_var, width=260).pack(side="left")

        member_row = ctk.CTkFrame(dialog, fg_color="transparent")
        member_row.pack(fill="x", padx=25, pady=6)
        ctk.CTkLabel(member_row, text="Member", width=90, anchor="w").pack(side="left")
        member_var = ctk.StringVar(value=list(member_map.keys())[0])
        ctk.CTkOptionMenu(member_row, values=list(member_map.keys()), variable=member_var, width=260).pack(side="left")

        days_row = ctk.CTkFrame(dialog, fg_color="transparent")
        days_row.pack(fill="x", padx=25, pady=6)
        ctk.CTkLabel(days_row, text="Loan period (days)", width=140, anchor="w").pack(side="left")
        days_entry = ctk.CTkEntry(days_row, width=210)
        days_entry.insert(0, "14")
        days_entry.pack(side="left")

        error_label = ctk.CTkLabel(dialog, text="", text_color=style.DANGER,
                                    font=style.font_small(), wraplength=370, justify="left")
        error_label.pack(pady=(10, 0), padx=20)

        def submit():
            try:
                book_id = book_map[book_var.get()]
                member_id = member_map[member_var.get()]
                db_manager.issue_loan(book_id, member_id, days_entry.get())
                dialog.destroy()
                self.refresh()
                info("Loan issued successfully.")
            except ValidationError as e:
                error_label.configure(text=str(e))
            except Exception as e:
                error_label.configure(text=f"Unexpected error: {e}")

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack(pady=20)
        ctk.CTkButton(btn_row, text="Cancel", fg_color=style.TEXT_MUTED, width=100,
                      command=dialog.destroy).pack(side="left", padx=10)
        ctk.CTkButton(btn_row, text="Issue", fg_color=style.PRIMARY, hover_color=style.PRIMARY_DARK,
                      width=100, command=submit).pack(side="left", padx=10)

    def _return_selected(self):
        loan_id = self._selected_loan_id()
        if loan_id is None:
            error("Please select a loan to mark as returned.")
            return
        if not confirm_dialog(self, "Mark this loan as returned?"):
            return
        try:
            fine = db_manager.return_loan(loan_id)
            self.refresh()
            if fine > 0:
                info(f"Book returned. Overdue fine charged: ${fine:.2f}")
            else:
                info("Book returned on time. No fine charged.")
        except ValidationError as e:
            error(str(e))
