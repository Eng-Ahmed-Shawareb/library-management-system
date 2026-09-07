"""
app.py
------
Main application shell: sidebar navigation + content area that swaps
between Dashboard, Books, Members, Loans and Reports screens.
"""

import customtkinter as ctk

from gui import style
from gui.widgets import style_treeview
from gui.dashboard_tab import DashboardTab
from gui.books_tab import BooksTab
from gui.members_tab import MembersTab
from gui.loans_tab import LoansTab
from gui.reports_tab import ReportsTab


class LibraryApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Library Management System")
        self.geometry("1100x700")
        self.minsize(950, 600)
        self.configure(fg_color=style.CONTENT_BG)

        style_treeview()

        self.sidebar_buttons = {}
        self.frames = {}
        self.current_frame_name = None

        self._build_sidebar()
        self._build_content_area()
        self._build_frames()
        self.show_frame("Dashboard")

    # ------------------------------------------------------------------
    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, fg_color=style.SIDEBAR_BG, width=220, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        logo = ctk.CTkLabel(sidebar, text="📚 LibrarySys", font=ctk.CTkFont(size=20, weight="bold"),
                             text_color="white")
        logo.pack(pady=(30, 40), padx=20, anchor="w")

        nav_items = [
            ("Dashboard", "🏠"),
            ("Books", "📖"),
            ("Members", "👥"),
            ("Loans", "🔄"),
            ("Reports", "📊"),
        ]

        for name, icon in nav_items:
            btn = ctk.CTkButton(
                sidebar, text=f"  {icon}   {name}", anchor="w",
                fg_color="transparent", hover_color=style.SIDEBAR_HOVER,
                text_color="white", font=style.font_nav(), height=44, corner_radius=8,
                command=lambda n=name: self.show_frame(n)
            )
            btn.pack(fill="x", padx=15, pady=4)
            self.sidebar_buttons[name] = btn

        footer = ctk.CTkLabel(sidebar, text="v1.0 · SQLite backend", font=style.font_small(),
                               text_color=style.TEXT_MUTED)
        footer.pack(side="bottom", pady=20)

    def _build_content_area(self):
        self.content_area = ctk.CTkFrame(self, fg_color=style.CONTENT_BG, corner_radius=0)
        self.content_area.pack(side="left", fill="both", expand=True)

    def _build_frames(self):
        self.frames["Dashboard"] = DashboardTab(self.content_area)
        self.frames["Books"] = BooksTab(self.content_area)
        self.frames["Members"] = MembersTab(self.content_area)
        self.frames["Loans"] = LoansTab(self.content_area)
        self.frames["Reports"] = ReportsTab(self.content_area)

    # ------------------------------------------------------------------
    def show_frame(self, name):
        for frame in self.frames.values():
            frame.pack_forget()
        frame = self.frames[name]
        frame.pack(fill="both", expand=True)

        if hasattr(frame, "refresh"):
            frame.refresh()

        for btn_name, btn in self.sidebar_buttons.items():
            btn.configure(fg_color=style.PRIMARY if btn_name == name else "transparent")

        self.current_frame_name = name


def run():
    app = LibraryApp()
    app.mainloop()
