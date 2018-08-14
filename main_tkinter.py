import sys
import unicodedata
# import tkinter
from pymongo import MongoClient

from tkinter import *
from tkinter import ttk

root = Tk()
root.title("Example")

notebook = ttk.Notebook(root)
frame1 = ttk.Frame(notebook)
frame2 = ttk.Frame(notebook)
notebook.add(frame1, text="Frame One")
notebook.add(frame2, text="Frame Two")
notebook.pack()

#(The labels are examples, but the rest of the code is identical in structure).

labelA = ttk.Label(frame1, text = "This is on Frame One")
labelA.grid(column=1, row=1)

labelB = ttk.Label(frame2, text = "This is on Frame Two")
labelB.grid(column=1, row=1)

root.mainloop()
