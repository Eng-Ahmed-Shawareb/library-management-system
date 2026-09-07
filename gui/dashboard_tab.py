"""
dashboard_tab.py
----------------
Landing screen showing at-a-glance statistics about the library.
"""

import customtkinter as ctk

import db_manager
from gui import style


class DashboardTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=style.CONTENT_BG)
        self.cards = {}
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        title = ctk.CTkLabel(self, text="Dashboard", font=style.font_title())
        title.pack(anchor="w", padx=30, pady=(25, 5))

        subtitle = ctk.CTkLabel(self, text="Overview of your library at a glance",
                                 font=style.font_body(), text_color=style.TEXT_MUTED)
        subtitle.pack(anchor="w", padx=30, pady=(0, 20))

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="x", padx=30)

        stats_spec = [
            ("distinct_titles", "Distinct Titles", "📖", style.PRIMARY),
            ("total_books", "Total Copies", "📚", style.PRIMARY_DARK),
            ("available_copies", "Available Now", "✅", style.SUCCESS),
            ("total_members", "Members", "👥", style.PRIMARY),
            ("active_loans", "Active Loans", "🔄", style.WARNING),
            ("overdue_loans", "Overdue Loans", "⚠️", style.DANGER),
        ]

        for i, (key, label, icon, color) in enumerate(stats_spec):
            card = ctk.CTkFrame(grid, fg_color=style.CARD_BG, corner_radius=14, width=220, height=120)
            card.grid(row=i // 3, column=i % 3, padx=10, pady=10, sticky="nsew")
            card.grid_propagate(False)

            icon_label = ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=26))
            icon_label.pack(anchor="w", padx=18, pady=(15, 0))

            value_label = ctk.CTkLabel(card, text="0", font=style.font_stat(), text_color=color)
            value_label.pack(anchor="w", padx=18)

            name_label = ctk.CTkLabel(card, text=label, font=style.font_body(),
                                       text_color=style.TEXT_MUTED)
            name_label.pack(anchor="w", padx=18, pady=(0, 10))

            self.cards[key] = value_label

        for col in range(3):
            grid.grid_columnconfigure(col, weight=1)

        refresh_btn = ctk.CTkButton(self, text="🔄 Refresh", fg_color=style.PRIMARY,
                                     hover_color=style.PRIMARY_DARK, command=self.refresh, width=120)
        refresh_btn.pack(anchor="w", padx=30, pady=20)

    def refresh(self):
        db_manager.refresh_overdue_statuses()
        stats = db_manager.get_dashboard_stats()
        for key, label_widget in self.cards.items():
            label_widget.configure(text=str(stats.get(key, 0)))
