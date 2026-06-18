import tkinter as tk
from modules.database_browser import DatabaseBrowser


def launch_database_viewer():

    win = tk.Tk()
    win.title("Database Viewer")
    win.geometry("1300x800")

    app = DatabaseBrowser(win)
    app.build()

    win.mainloop()