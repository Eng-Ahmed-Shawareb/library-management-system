"""
style.py
--------
Central place for colors, fonts and sizing so every screen in the
app looks consistent.
"""

import customtkinter as ctk

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# Palette
PRIMARY = "#2454FF"
PRIMARY_DARK = "#1638B0"
SIDEBAR_BG = "#101A33"
SIDEBAR_HOVER = "#1D2B4F"
CONTENT_BG = "#F4F6FB"
CARD_BG = "#FFFFFF"
SUCCESS = "#1FA97C"
WARNING = "#E0A106"
DANGER = "#E5484D"
TEXT_MUTED = "#6B7280"
BORDER = "#E2E5EC"

FONT_FAMILY = "Segoe UI"

def font_title():
    return ctk.CTkFont(family=FONT_FAMILY, size=24, weight="bold")

def font_subtitle():
    return ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold")

def font_body():
    return ctk.CTkFont(family=FONT_FAMILY, size=13)

def font_small():
    return ctk.CTkFont(family=FONT_FAMILY, size=11)

def font_stat():
    return ctk.CTkFont(family=FONT_FAMILY, size=28, weight="bold")

def font_nav():
    return ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold")
