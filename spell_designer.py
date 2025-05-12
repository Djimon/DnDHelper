import tkinter as tk
from tkinter import ttk, colorchooser, simpledialog, filedialog
from card_renderer_utils import (
    px, py, fw, fh, fs, hex_with_alpha, fc, draw_icons, draw_text_elements, draw_damage
)
import json
import os

class SpellDesigner:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill="both", expand=True)

        self.current_element = None
        self.config_data = {}
        self.fields = {}

        # Haupt-Layout in 2 Spalten
        self.left_panel = ttk.Frame(self.frame, width=300)
        self.left_panel.pack(side="left", fill="y", padx=10, pady=10)

        self.right_panel = ttk.Frame(self.frame)
        self.right_panel.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.build_left_panel()
        self.build_right_panel()
        self.load_default_config()



    def build_left_panel(self):
        ttk.Label(self.left_panel, text="Element auswählen:").pack(anchor="w")

        ttk.Button(self.left_panel, text="Konfiguration speichern", command=self.save_current_config).pack(fill="x",
                                                                                                           pady=10)

        self.element_selector = ttk.Combobox(self.left_panel, state="readonly")
        self.element_selector.pack(fill="x", pady=(0, 10))
        self.element_selector.bind("<<ComboboxSelected>>", self.on_element_selected)

        self.field_container = ttk.Frame(self.left_panel)
        self.field_container.pack(fill="both", expand=True)

    def build_right_panel(self):
        # Wrapper-Frame für Scrollbar + Canvas
        canvas_frame = ttk.Frame(self.right_panel)
        canvas_frame.pack(fill="both", expand=True)

        # Horizontal scrollbarer Canvas
        self.preview_canvas = tk.Canvas(canvas_frame, bg="white", height=600)
        self.preview_canvas.pack(side="bottom", fill="both", expand=True)

        # Scrollbar hinzufügen
        h_scroll = ttk.Scrollbar(canvas_frame, orient="horizontal", command=self.preview_canvas.xview)
        h_scroll.pack(side="bottom", fill="x")
        self.preview_canvas.configure(xscrollcommand=h_scroll.set)

        # Inhalt (Frame in Canvas)
        self.canvas_inner = ttk.Frame(self.preview_canvas)
        self.preview_canvas.create_window((0, 0), window=self.canvas_inner, anchor="nw")

        # Canvasgröße automatisch anpassen
        self.canvas_inner.bind("<Configure>", lambda e: self.preview_canvas.configure(
            scrollregion=self.preview_canvas.bbox("all"))
                               )
        # Vorschaubutton
        button_frame = ttk.Frame(self.right_panel)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Vorschau aktualisieren", command=self.on_update_preview_clicked).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Design speichern als...", command=self.save_config_as).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Design laden", command=self.load_config_file).pack(side="left", padx=5)

    def load_default_config(self):
        try:
            with open("src/design_config.json", "r", encoding="utf-8") as f:
                self.config_data = json.load(f)
            self.element_selector["values"] = list(self.config_data.keys())
            self.element_selector.current(0)
            self.on_element_selected()  # erste Auswahl direkt anzeigen
        except Exception as e:
            print("Fehler beim Laden der Design-Konfiguration:", e)

        try:
            with open("src/preview_spells.json", "r", encoding="utf-8") as f:
                self.preview_spells = json.load(f)
        except Exception as e:
            print("Fehler beim Laden des Vorschau-Zaubers:", e)
            self.preview_spells = {}

    def on_update_preview_clicked(self):
        self.save_current_config()
        self.redraw_preview()


    def redraw_preview(self):
        for widget in self.canvas_inner.winfo_children():
            widget.destroy()

        card_width = 300
        spacing = 40

        for i, spell in enumerate(self.preview_spells):
            card_canvas = tk.Canvas(self.canvas_inner, width=card_width+20, height=500, bg="white")
            card_canvas.pack(side="left", padx=(0 if i == 0 else spacing), pady=10)
            draw_card_preview(card_canvas, self.config_data, spell)

    def save_current_config(self):
        if not self.current_element:
            return

        # Sicherstellen, dass alle Eingaben übernommen werden
        for key, var in self.fields.items():
            val = var.get()
            # numerische Werte als float speichern, Rest als String
            try:
                val = float(val)
                if val.is_integer():
                    val = int(val)
            except:
                pass
            self.config_data[self.current_element][key] = val

        # In Datei schreiben
        try:
            with open("design_config.json", "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, indent=4)
            print("Konfiguration gespeichert.")
        except Exception as e:
            print("Fehler beim Speichern:", e)


    def save_config_as(self):
        filename = simpledialog.askstring("Design speichern", "Dateiname für das Design (ohne .json):")
        if not filename:
            return
        path = os.path.join("designs", f"{filename}.json")
        try:
            os.makedirs("designs", exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, indent=4)
            print(f"Design gespeichert unter: {path}")
        except Exception as e:
            print("Fehler beim Speichern:", e)

    def load_config_file(self):
        path = filedialog.askopenfilename(initialdir="designs", filetypes=[("JSON Dateien", "*.json")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.config_data = json.load(f)
            self.element_selector["values"] = list(self.config_data.keys())
            self.element_selector.current(0)
            self.on_element_selected()
            self.redraw_preview()
            print(f"Design geladen von: {path}")
        except Exception as e:
            print("Fehler beim Laden:", e)


    def on_element_selected(self, event=None):
        element = self.element_selector.get()
        if not element or element not in self.config_data:
            return

        self.current_element = element
        config = self.config_data[element]

        # Vorherige Felder löschen
        for widget in self.field_container.winfo_children():
            widget.destroy()
        self.fields.clear()

        # Für jedes Feld ein Eingabefeld erzeugen
        for key, value in config.items():
            row = ttk.Frame(self.field_container)
            row.pack(fill="x", pady=3)
            ttk.Label(row, text=key + ":").pack(side="left")

            # --- MODE-DROPDOWN ---
            if self.current_element == "frame" and key == "mode":
                var = tk.StringVar(value=value)
                dropdown = ttk.Combobox(row, textvariable=var, state="readonly", values=["single", "class", "school"])
                dropdown.pack(side="left", padx=5)
                self.fields[key] = var

                def update_color_visibility(*args):
                    show_color = var.get() == "single"
                    if hasattr(self, "color_row_widget"):
                        self.color_row_widget.pack_forget()
                        if show_color:
                            self.color_row_widget.pack(fill="x", pady=3)

                var.trace_add("write", update_color_visibility)

            # --- COLOR-PICKER ---
            elif self.current_element == "frame" and key == "color":
                self.color_row_widget = row  # NICHT in self.fields!
                var = tk.StringVar(value=value)

                def choose_color(k=key, v=var):
                    color = colorchooser.askcolor()[1]
                    if color:
                        v.set(color)

                entry = ttk.Entry(row, textvariable=var, width=10)
                entry.pack(side="left", padx=5)
                btn = ttk.Button(row, text="Wählen", command=choose_color)
                btn.pack(side="left")
                self.fields[key] = var  # Nur das StringVar in fields

            elif isinstance(value, (int, float)):
                var = tk.DoubleVar(value=value)
                entry = ttk.Entry(row, textvariable=var, width=8)
                entry.pack(side="left", padx=5)
                if key in ["x", "y", "width", "height", "max_width"]:
                    ttk.Label(row, text="%").pack(side="left")
                self.fields[key] = var

            elif isinstance(value, str):
                var = tk.StringVar(value=value)
                entry = ttk.Entry(row, textvariable=var, width=20)
                entry.pack(side="left", padx=5)
                self.fields[key] = var

            elif key == "opacity":
                var = tk.IntVar(value=value)
                slider = ttk.Scale(row, from_=0, to=100, variable=var, orient="horizontal")
                slider.pack(side="left", fill="x", expand=True, padx=5)
                self.fields[key] = var



def draw_card_preview(canvas, config_data, spell_data, width_px=300):
    canvas.delete("all")

    # Kartengröße (in Pixel)
    w = width_px
    h = int(w * 88 / 63)
    x0, y0 = 10, 10
    x1, y1 = x0 + w, y0 + h

    # Hintergrund
    bg = config_data.get("background_image", {})
    bg_alpha = bg.get("opacity", 100)
    bg_color = "#dddddd"
    canvas.create_rectangle(x0, y0, x1, y1, fill=hex_with_alpha(bg_color, bg_alpha), outline="")

    # Rahmen
    frame = config_data.get("frame", {})
    color = fc(frame, spell_data)
    thick = frame.get("thickness", 2)
    roundness = frame.get("roundness", 0)
    if roundness > 0:
        draw_rounded_rect(canvas, x0, y0, x1, y1, roundness, color, thick)
    else:
        canvas.create_rectangle(x0, y0, x1, y1, outline=color, width=thick)

    # Textfelder
    draw_text_elements(canvas, config_data, spell_data, x0, y0, w, h)

    # Schadenswürfel
    draw_damage(canvas, config_data, spell_data, x0, y0, w, h)

    # Icons
    draw_icons(canvas, config_data, x0, y0, w, h)

    # Kartenname unter der Karte anzeigen
    canvas.create_text(
        (x0 + x1) // 2, y1 + 10,
        text=spell_data.get("name", "Unbenannt"),
        font=("Arial", 12, "bold")
    )

def hex_with_alpha(hex_color, alpha_percent):
    """Erzeugt eine RGBA-Farbe für Canvas (nur für Fake-Farben)"""
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    # Simulierte Helligkeit
    r = int(r + (255 - r) * (100 - alpha_percent) / 100)
    g = int(g + (255 - g) * (100 - alpha_percent) / 100)
    b = int(b + (255 - b) * (100 - alpha_percent) / 100)
    return f"#{r:02x}{g:02x}{b:02x}"

def draw_rounded_rect(canvas, x0, y0, x1, y1, r, outline, width):
    canvas.create_arc(x0, y0, x0 + 2 * r, y0 + 2 * r, start=90, extent=90, style='arc', outline=outline,
                      width=width)
    canvas.create_arc(x1 - 2 * r, y0, x1, y0 + 2 * r, start=0, extent=90, style='arc', outline=outline, width=width)
    canvas.create_arc(x1 - 2 * r, y1 - 2 * r, x1, y1, start=270, extent=90, style='arc', outline=outline,
                      width=width)
    canvas.create_arc(x0, y1 - 2 * r, x0 + 2 * r, y1, start=180, extent=90, style='arc', outline=outline,
                      width=width)
    canvas.create_line(x0 + r, y0, x1 - r, y0, fill=outline, width=width)
    canvas.create_line(x0 + r, y1, x1 - r, y1, fill=outline, width=width)
    canvas.create_line(x0, y0 + r, x0, y1 - r, fill=outline, width=width)
    canvas.create_line(x1, y0 + r, x1, y1 - r, fill=outline, width=width)
