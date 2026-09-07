"""
reports_tab.py
--------------
Simple reporting screen: lists overdue loans and lets the librarian
export the current book catalogue or loan history to CSV.
"""

import csv
import customtkinter as ctk
from tkinter import ttk, filedialog

import db_manager
from gui import style
from gui.widgets import info, error


class ReportsTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=style.CONTENT_BG)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(25, 10))
        ctk.CTkLabel(header, text="Reports", font=style.font_title()).pack(side="left")

        export_row = ctk.CTkFrame(self, fg_color="transparent")
        export_row.pack(fill="x", padx=30, pady=(0, 10))
        ctk.CTkButton(export_row, text="Export Books (CSV)", fg_color=style.PRIMARY,
                      command=self._export_books).pack(side="left", padx=(0, 10))
        ctk.CTkButton(export_row, text="Export Loans (CSV)", fg_color=style.PRIMARY,
                      command=self._export_loans).pack(side="left")

        ctk.CTkLabel(self, text="Overdue Loans", font=style.font_subtitle()).pack(
            anchor="w", padx=30, pady=(15, 5))

        table_frame = ctk.CTkFrame(self, fg_color=style.CARD_BG, corner_radius=12)
        table_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        columns = ("id", "book", "member", "due_date", "days_overdue")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", style="Custom.Treeview")
        headings = ["Loan ID", "Book", "Member", "Due Date", "Days Overdue"]
        widths = [70, 220, 180, 100, 110]
        for col, head, w in zip(columns, headings, widths):
            self.tree.heading(col, text=head)
            self.tree.column(col, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10, side="left")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        ctk.CTkButton(self, text="🔄 Refresh", fg_color=style.PRIMARY,
                      command=self.refresh, width=120).pack(anchor="w", padx=30, pady=(0, 20))

    def refresh(self):
        from datetime import datetime
        db_manager.refresh_overdue_statuses()
        for row in self.tree.get_children():
            self.tree.delete(row)
        loans = db_manager.get_all_loans("")
        today = datetime.now()
        for l in loans:
            if l["status"] == "Overdue":
                due = datetime.strptime(l["due_date"], "%Y-%m-%d")
                days_overdue = (today - due).days
                self.tree.insert("", "end", values=(
                    l["id"], l["book_title"], l["member_name"], l["due_date"], days_overdue
                ))

    def _export_books(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                             filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        books = db_manager.search_books("")
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Title", "Author", "ISBN", "Category",
                                  "Publisher", "Year", "Total Copies", "Available Copies"])
                for b in books:
                    writer.writerow([b["id"], b["title"], b["author"], b["isbn"], b["category"],
                                      b["publisher"], b["publish_year"], b["total_copies"],
                                      b["available_copies"]])
            info(f"Books exported to {path}")
        except Exception as e:
            error(f"Could not export: {e}")

    def _export_loans(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                             filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        loans = db_manager.get_all_loans("")
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Book", "Member", "Loan Date", "Due Date",
                                  "Return Date", "Status", "Fine"])
                for l in loans:
                    writer.writerow([l["id"], l["book_title"], l["member_name"], l["loan_date"],
                                      l["due_date"], l["return_date"] or "", l["status"], l["fine_amount"]])
            info(f"Loans exported to {path}")
        except Exception as e:
            error(f"Could not export: {e}")
