from tkinter import ttk, filedialog, StringVar
import os
from export_spellcards_pdf import export_spellcards_pdf

class SpellExporter:
    def __init__(self, parent, collection, designer_ref):
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill="both", expand=True)
        self.collection = collection
        self.collection_name = 'MyCollection'
        self.designer = designer_ref

        ttk.Label(self.frame, text="PDF-Export von Zauberkarten", font=("Arial", 12, "bold")).pack(pady=10)

        self.collection_path = "collection.json"
        self.backside_option = StringVar(value="none")

        # Sammlung laden
        ttk.Button(self.frame, text="Sammlung laden", command=self.choose_collection).pack(pady=5)

        # Rückseitenoptionen
        ttk.Label(self.frame, text="Rückseite:").pack()
        options = [("Keine Rückseite", "none"), ("Vorgefertigtes Bild", "preset"), ("Eigenes Bild wählen", "custom")]
        for text, val in options:
            ttk.Radiobutton(self.frame, text=text, variable=self.backside_option, value=val).pack(anchor="w", padx=20)

        # PDF erzeugen
        ttk.Button(self.frame, text="PDF erzeugen", command=self.export_pdf).pack(pady=15)

        # Statusausgabe
        self.status_label = ttk.Label(self.frame, text="", foreground="gray")
        self.status_label.pack()

        self.custom_backside_path = None

    def choose_collection(self):
        path = filedialog.askopenfilename(initialdir="collections", filetypes=[("JSON Dateien", "*.json")])
        if path:
            self.collection_path = path
            self.collection_name = os.path.splitext(os.path.basename(path))[0]
            try:
                import json
                with open(path, "r", encoding="utf-8") as f:
                    self.collection = json.load(f)
                self.status_label.config(text=f"Sammlung geladen: {os.path.basename(path)}")
            except Exception as e:
                self.status_label.config(text=f"Fehler beim Laden der Sammlung: {e}")

    def export_pdf(self):
        # Falls Benutzer "custom" gewählt hat, Bild erfragen
        if self.backside_option.get() == "custom":
            image_path = filedialog.askopenfilename(filetypes=[("Bilddateien", "*.png;*.jpg;*.jpeg")])
            if not image_path:
                self.status_label.config(text="Export abgebrochen: Kein Bild gewählt.")
                return
            self.custom_backside_path = image_path
        else:
            self.custom_backside_path = None

        try:
            export_spellcards_pdf(
                spells=self.collection,
                design_config=self.designer.config_data,
                output_dir="output",
                backside_option=self.backside_option.get(),
                backside_path=self.custom_backside_path,
                base_name=self.collection_name
            )
            self.status_label.config(text="Export abgeschlossen.")
        except Exception as e:
            self.status_label.config(text=f"Fehler beim Export: {e}")