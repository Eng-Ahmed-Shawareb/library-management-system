"""
members_tab.py
--------------
CRUD screen for managing library members.
"""

import customtkinter as ctk
from tkinter import ttk

import db_manager
from validators import ValidationError, VALID_MEMBERSHIP_TYPES
from gui import style
from gui.widgets import FormDialog, confirm_dialog, info, error


def _member_fields(default=None):
    default = default or {}
    return [
        {"key": "full_name", "label": "Full Name", "default": default.get("full_name")},
        {"key": "email", "label": "Email", "default": default.get("email")},
        {"key": "phone", "label": "Phone", "default": default.get("phone")},
        {"key": "address", "label": "Address", "default": default.get("address")},
        {"key": "membership_type", "label": "Membership Type", "type": "option",
         "options": list(VALID_MEMBERSHIP_TYPES), "default": default.get("membership_type", "Regular")},
        {"key": "max_books_allowed", "label": "Max Books Allowed", "default": default.get("max_books_allowed", 3)},
    ]


class MembersTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=style.CONTENT_BG)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(25, 10))

        title = ctk.CTkLabel(header, text="Members", font=style.font_title())
        title.pack(side="left")

        add_btn = ctk.CTkButton(header, text="+ Add Member", fg_color=style.PRIMARY,
                                 hover_color=style.PRIMARY_DARK, command=self._open_add_dialog)
        add_btn.pack(side="right")

        search_row = ctk.CTkFrame(self, fg_color="transparent")
        search_row.pack(fill="x", padx=30)
        self.search_entry = ctk.CTkEntry(search_row, placeholder_text="Search by name, email or phone...", width=400)
        self.search_entry.pack(side="left", pady=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh())

        table_frame = ctk.CTkFrame(self, fg_color=style.CARD_BG, corner_radius=12)
        table_frame.pack(fill="both", expand=True, padx=30, pady=15)

        columns = ("id", "name", "email", "phone", "type", "max", "status", "joined")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", style="Custom.Treeview")
        headings = ["ID", "Name", "Email", "Phone", "Type", "Max", "Status", "Joined"]
        widths = [40, 160, 190, 110, 90, 50, 80, 90]
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
        ctk.CTkButton(action_row, text="Suspend/Activate", fg_color=style.PRIMARY,
                      command=self._toggle_status).pack(side="left", padx=(0, 10))
        ctk.CTkButton(action_row, text="Delete Selected", fg_color=style.DANGER,
                      command=self._delete_selected).pack(side="left")

    def refresh(self):
        keyword = self.search_entry.get() if hasattr(self, "search_entry") else ""
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            members = db_manager.search_members(keyword)
        except Exception as e:
            error(str(e))
            return
        for m in members:
            self.tree.insert("", "end", values=(
                m["id"], m["full_name"], m["email"], m["phone"], m["membership_type"],
                m["max_books_allowed"], m["status"], m["join_date"]
            ))

    def _selected_member_id(self):
        selection = self.tree.selection()
        if not selection:
            return None
        return self.tree.item(selection[0])["values"][0]

    def _open_add_dialog(self):
        def on_submit(values):
            db_manager.add_member(
                values["full_name"], values["email"], values["phone"], values["address"],
                values["membership_type"], values["max_books_allowed"]
            )
            self.refresh()
            info("Member added successfully.")

        FormDialog(self, "Add New Member", _member_fields(), on_submit, submit_label="Add")

    def _open_edit_dialog(self):
        member_id = self._selected_member_id()
        if member_id is None:
            error("Please select a member to edit.")
            return
        member = db_manager.get_member(member_id)
        if member is None:
            error("Member not found (may have been deleted).")
            self.refresh()
            return

        def on_submit(values):
            db_manager.update_member(
                member_id, values["full_name"], values["email"], values["phone"],
                values["address"], values["membership_type"], values["max_books_allowed"],
                member["status"]
            )
            self.refresh()
            info("Member updated successfully.")

        FormDialog(self, "Edit Member", _member_fields(member), on_submit, submit_label="Save")

    def _toggle_status(self):
        member_id = self._selected_member_id()
        if member_id is None:
            error("Please select a member.")
            return
        member = db_manager.get_member(member_id)
        new_status = "Suspended" if member["status"] == "Active" else "Active"
        try:
            db_manager.update_member(
                member_id, member["full_name"], member["email"], member["phone"],
                member["address"], member["membership_type"], member["max_books_allowed"],
                new_status
            )
            self.refresh()
            info(f"Member status changed to '{new_status}'.")
        except ValidationError as e:
            error(str(e))

    def _delete_selected(self):
        member_id = self._selected_member_id()
        if member_id is None:
            error("Please select a member to delete.")
            return
        if not confirm_dialog(self, "Are you sure you want to delete this member?"):
            return
        try:
            db_manager.delete_member(member_id)
            self.refresh()
            info("Member deleted.")
        except ValidationError as e:
            error(str(e))
