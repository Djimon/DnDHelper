import tkinter as tk
from tkinter import ttk

from spell_manager import SpellManager
from spell_designer import SpellDesigner
from spell_exporter import SpellExporter

def main():
    root = tk.Tk()
    root.title("DnD Spell Tool")

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    # Schritt 1: Spell-Verwaltung
    tab1 = ttk.Frame(notebook)
    spell_manager = SpellManager(tab1)  # übergibt Frame als Parent
    notebook.add(tab1, text="1. Spells verwalten")


    # Schritt 2: Karten-Designer
    tab2 = ttk.Frame(notebook)
    spell_designer = SpellDesigner(tab2)
    notebook.add(tab2, text="2. Karten gestalten")

    # Schritt 3: Export
    tab3 = ttk.Frame(notebook)
    spell_exporter = SpellExporter(tab3, spell_manager.collection, spell_designer)
    notebook.add(tab3, text="3. Export")

    root.mainloop()

if __name__ == "__main__":
    main()