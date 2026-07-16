import tkinter as tk
from tkinter import ttk

from modules.yahooFetcher import build_yahoo_tab
from modules.secFetcher import build_sec_tab


class DataFetcherPopup(tk.Toplevel):

    def __init__(self, parent):

        super().__init__(parent)

        self.title("NEA28 Data Downloader")
        self.geometry("600x700")

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        yahoo = ttk.Frame(notebook)
        sec = ttk.Frame(notebook)

        notebook.add(yahoo, text="Yahoo Finance")
        notebook.add(sec, text="SEC EDGAR")

        build_yahoo_tab(yahoo)
        build_sec_tab(sec)