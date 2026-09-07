"""
widgets.py
----------
Reusable building blocks shared by the Books, Members and Loans tabs:
- FormDialog: a modal pop-up that renders a form from a field spec,
  runs the provided validator/submit callback, and displays validation
  errors inline instead of crashing or closing silently.
- style_treeview: applies a consistent look to ttk.Treeview widgets
  (used for tables) so they match the customtkinter theme.
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

from gui import style
from validators import ValidationError


def style_treeview():
    ttk_style = ttk.Style()
    ttk_style.theme_use("clam")
    ttk_style.configure(
        "Custom.Treeview",
        background=style.CARD_BG,
        foreground="#1F2430",
        fieldbackground=style.CARD_BG,
        rowheight=32,
        borderwidth=0,
        font=(style.FONT_FAMILY, 12),
    )
    ttk_style.configure(
        "Custom.Treeview.Heading",
        background=style.SIDEBAR_BG,
        foreground="white",
        font=(style.FONT_FAMILY, 12, "bold"),
        borderwidth=0,
    )
    ttk_style.map(
        "Custom.Treeview",
        background=[("selected", style.PRIMARY)],
        foreground=[("selected", "white")],
    )


class FormDialog(ctk.CTkToplevel):
    """
    A generic modal form.

    fields: list of dicts, each like:
        {"key": "title", "label": "Title", "type": "entry"|"option", "options": [...], "default": "..."}
    on_submit: callable(values_dict) -> None. Should raise ValidationError on bad input;
               the dialog will display the message and stay open for correction.
    """

    def __init__(self, master, title, fields, on_submit, submit_label="Save"):
        super().__init__(master)
        self.title(title)
        self.geometry("420x" + str(120 + 60 * len(fields)))
        self.resizable(False, False)
        self.configure(fg_color=style.CONTENT_BG)
        self.grab_set()  # modal

        self.fields = fields
        self.on_submit = on_submit
        self.entries = {}

        header = ctk.CTkLabel(self, text=title, font=style.font_subtitle())
        header.pack(pady=(20, 10))

        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=25)

        for field in fields:
            row = ctk.CTkFrame(form_frame, fg_color="transparent")
            row.pack(fill="x", pady=6)
            label = ctk.CTkLabel(row, text=field["label"], font=style.font_body(), width=140, anchor="w")
            label.pack(side="left")

            if field.get("type") == "option":
                var = ctk.StringVar(value=field.get("default", field["options"][0]))
                widget = ctk.CTkOptionMenu(row, values=field["options"], variable=var, width=220)
                widget.pack(side="left")
                self.entries[field["key"]] = var
            else:
                widget = ctk.CTkEntry(row, width=220)
                if field.get("default") is not None:
                    widget.insert(0, str(field["default"]))
                widget.pack(side="left")
                self.entries[field["key"]] = widget

        self.error_label = ctk.CTkLabel(self, text="", text_color=style.DANGER,
                                         font=style.font_small(), wraplength=380, justify="left")
        self.error_label.pack(pady=(10, 0), padx=20)

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=20)
        cancel_btn = ctk.CTkButton(btn_row, text="Cancel", fg_color=style.TEXT_MUTED,
                                    width=100, command=self.destroy)
        cancel_btn.pack(side="left", padx=10)
        submit_btn = ctk.CTkButton(btn_row, text=submit_label, fg_color=style.PRIMARY,
                                    hover_color=style.PRIMARY_DARK, width=100, command=self._submit)
        submit_btn.pack(side="left", padx=10)

    def _submit(self):
        values = {}
        for key, widget in self.entries.items():
            if isinstance(widget, ctk.StringVar):
                values[key] = widget.get()
            else:
                values[key] = widget.get()
        try:
            self.on_submit(values)
            self.destroy()
        except ValidationError as e:
            self.error_label.configure(text=str(e))
        except Exception as e:
            self.error_label.configure(text=f"Unexpected error: {e}")


def confirm_dialog(master, message):
    from tkinter import messagebox
    return messagebox.askyesno("Confirm", message)


def info(message, title="Success"):
    from tkinter import messagebox
    messagebox.showinfo(title, message)


def error(message, title="Error"):
    from tkinter import messagebox
    messagebox.showerror(title, message)
