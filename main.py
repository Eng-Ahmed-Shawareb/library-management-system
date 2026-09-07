"""
main.py
-------
Entry point for the Library Management System.

Run with:
    python main.py
"""

from database import initialize_database
from gui.login import LoginWindow
from gui.app import run as run_main_app


def main():
    initialize_database()

    def on_login_success():
        run_main_app()

    login = LoginWindow(on_success=on_login_success)
    login.mainloop()


if __name__ == "__main__":
    main()
