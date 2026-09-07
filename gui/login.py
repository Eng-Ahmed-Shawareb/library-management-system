"""
login.py
--------
Simple librarian login screen shown before the main application.
"""

import customtkinter as ctk
from tkinter import messagebox

import db_manager
from gui import style


class LoginWindow(ctk.CTk):
    def __init__(self, on_success):
        super().__init__()
        self.on_success = on_success
        self.title("Library Management System - Login")
        self.geometry("420x480")
        self.resizable(False, False)
        self.configure(fg_color=style.CONTENT_BG)
        self._build_ui()

    def _build_ui(self):
        card = ctk.CTkFrame(self, fg_color=style.CARD_BG, corner_radius=16)
        card.pack(expand=True, fill="both", padx=30, pady=40)

        icon = ctk.CTkLabel(card, text="📚", font=ctk.CTkFont(size=48))
        icon.pack(pady=(40, 10))

        title = ctk.CTkLabel(card, text="Library Management System",
                              font=style.font_title(), text_color=style.PRIMARY)
        title.pack(pady=(0, 5))

        subtitle = ctk.CTkLabel(card, text="Sign in to continue",
                                 font=style.font_body(), text_color=style.TEXT_MUTED)
        subtitle.pack(pady=(0, 25))

        self.username_entry = ctk.CTkEntry(card, placeholder_text="Username", width=260, height=40)
        self.username_entry.pack(pady=8)
        self.username_entry.insert(0, "admin")

        self.password_entry = ctk.CTkEntry(card, placeholder_text="Password", show="•", width=260, height=40)
        self.password_entry.pack(pady=8)
        self.password_entry.bind("<Return>", lambda e: self._attempt_login())

        self.error_label = ctk.CTkLabel(card, text="", text_color=style.DANGER, font=style.font_small())
        self.error_label.pack(pady=(5, 0))

        login_btn = ctk.CTkButton(card, text="Log In", width=260, height=40,
                                   fg_color=style.PRIMARY, hover_color=style.PRIMARY_DARK,
                                   font=style.font_subtitle(), command=self._attempt_login)
        login_btn.pack(pady=20)

        hint = ctk.CTkLabel(card, text="Default: admin / admin123",
                             font=style.font_small(), text_color=style.TEXT_MUTED)
        hint.pack(pady=(0, 20))

    def _attempt_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            self.error_label.configure(text="Please enter both username and password.")
            return

        try:
            ok = db_manager.authenticate(username, password)
        except Exception as exc:
            messagebox.showerror("Database error", str(exc))
            return

        if ok:
            self.destroy()
            self.on_success()
        else:
            self.error_label.configure(text="Invalid username or password.")
