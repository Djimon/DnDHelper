import tkinter as tk
from tkinter import ttk, filedialog
import json
import pathlib

class SpellManager:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill="both", expand=True)
        self.root = self.frame

        self.all_spells = []
        self.filtered_spells = []
        self.collection = []

        # UI-Layout
        self.setup_ui()

        #Custom Spells
        self.custom_spells = []  # Eigene Zauber aus custom_spells.json

        # Custom spells laden
        custom_path = pathlib.Path("src/custom_spells.json")
        if custom_path.exists():
            with open(custom_path, "r", encoding="utf-8") as f:
                self.custom_spells = json.load(f)
                self.all_spells.extend(self.custom_spells)
                self.set_status(f"{len(self.custom_spells)} eigene Zauber geladen.")
            for spell in self.custom_spells:
                spell.setdefault("source", "Homebrew")

        # Versuche Standardliste zu laden
        default_path = pathlib.Path("src/spells.json")
        if default_path.exists():
            self.load_spells_from_path(default_path)

    def load_spells_from_path(self, path):
        with open(path, "r", encoding="utf-8") as f:
            core_spells = json.load(f)
            for spell in core_spells:
                spell.setdefault("source", "Core")

        # Kombiniere core + custom spells
        combined_spells = core_spells + self.custom_spells

        # Duplikate vermeiden (nach Name+Source)
        unique = {}
        for spell in combined_spells:
            key = (spell.get("name", "").lower(), spell.get("source", "Core").lower())
            unique[key] = spell

        self.all_spells = sorted(unique.values(), key=lambda s: s.get("name", "").lower())
        self.filtered_spells = self.all_spells

        self.set_status(f"{len(self.all_spells)} Zauber geladen.")
        self.update_spell_list()
        self.update_dynamic_filters()


    def setup_ui(self):
        # Frame: Filter
        filter_frame = ttk.LabelFrame(self.root, text="Filter")
        filter_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        # Statusleiste
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w")
        self.status_label.grid(row=3, column=0, padx=10, pady=(0, 5), sticky="ew")

        # Klassen + Schulen nebeneinander in Frame
        filter_subframe = ttk.Frame(filter_frame)
        filter_subframe.grid(row=0, column=1, sticky="ew")

        # Klassen-Label
        ttk.Label(filter_subframe, text="Klassen:").grid(row=0, column=0, sticky="w")
        class_frame = ttk.Frame(filter_subframe)
        class_frame.grid(row=1, column=0, padx=(0, 10), pady=2)

        self.class_listbox = tk.Listbox(class_frame, selectmode=tk.MULTIPLE, height=6, exportselection=False)
        class_scroll = ttk.Scrollbar(class_frame, orient="vertical", command=self.class_listbox.yview)
        self.class_listbox.config(yscrollcommand=class_scroll.set)
        self.class_listbox.grid(row=0, column=0, sticky="ns")
        class_scroll.grid(row=0, column=1, sticky="ns")
        self.class_listbox.bind("<<ListboxSelect>>", lambda e:  self.apply_filter())

        # Schulen-Label
        ttk.Label(filter_subframe, text="Schulen:").grid(row=0, column=1, sticky="w")
        school_frame = ttk.Frame(filter_subframe)
        school_frame.grid(row=1, column=1, pady=2)

        self.school_listbox = tk.Listbox(school_frame, selectmode=tk.MULTIPLE, height=6, exportselection=False)
        school_scroll = ttk.Scrollbar(school_frame, orient="vertical", command=self.school_listbox.yview)
        self.school_listbox.config(yscrollcommand=school_scroll.set)
        self.school_listbox.grid(row=0, column=0, sticky="ns")
        school_scroll.grid(row=0, column=1, sticky="ns")
        self.school_listbox.bind("<<ListboxSelect>>", lambda e:  self.apply_filter())

        # Frame für Level-Buttons
        ttk.Label(filter_subframe, text="Level:").grid(row=0, column=2, sticky="w", padx=(10, 0))
        self.selected_levels = set()
        level_frame = ttk.Frame(filter_subframe)
        level_frame.grid(row=1, column=2, padx=(10, 0), pady=2, sticky="nw")

        self.level_buttons = {}

        for i, label in enumerate(["cantrip"] + list(map(str, range(1, 10)))):
            btn = tk.Button(level_frame, text=label, width=6, relief="raised",
                            command=lambda lvl=label: self.toggle_level(lvl))
            btn.grid(row=i // 5, column=i % 5, padx=2, pady=2)
            self.level_buttons[label] = btn

        ttk.Button(filter_frame, text="Filter zurücksetzen", command=self.reset_filters).grid(row=3, column=0, columnspan=2, pady=5)



        # Container für SpellList
        list_detail_frame = ttk.Frame(self.root)
        list_detail_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        # Scrollbarer Bereich für Spell-Checkbox-Liste
        spell_canvas = tk.Canvas(list_detail_frame, width=300, height=400)
        scrollbar = ttk.Scrollbar(list_detail_frame, orient="vertical", command=spell_canvas.yview)
        spell_canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.grid(row=0, column=1, sticky="ns")
        spell_canvas.grid(row=0, column=0, sticky="nsew")

        self.spell_list_container = ttk.Frame(spell_canvas)
        self.spell_list_container.bind(
            "<Configure>",
            lambda e: spell_canvas.configure(scrollregion=spell_canvas.bbox("all"))
        )

        spell_canvas.create_window((0, 0), window=self.spell_list_container, anchor="nw")
        self.spell_canvas = spell_canvas  # Merke Referenz

        # Mousewheel aktivieren für gesamten Spellbereich
        def _on_mousewheel(event):
            spell_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        # Scroll auch aktivieren, wenn Maus über innerem Bereich liegt
        self.spell_list_container.bind("<Enter>", lambda e: spell_canvas.bind_all("<MouseWheel>", _on_mousewheel))
        self.spell_list_container.bind("<Leave>", lambda e: spell_canvas.unbind_all("<MouseWheel>"))

        # Spell-Details rechts daneben (mit Suchfeld & Button)
        self.detail_frame = ttk.Frame(list_detail_frame)
        self.detail_frame.grid(row=0, column=2, sticky="nsew", padx=(10, 0))

        # Suchfeld über der Detailansicht
        search_frame = ttk.Frame(self.detail_frame)
        search_frame.pack(anchor="nw", pady=(0, 5))

        #Button für eigene Zauber
        ttk.Button(search_frame, text="Neuer Zauber", command=self.new_spell_dialog).pack(side="left", padx=5)

        ttk.Label(search_frame, text="Suchen:").pack(side="left")
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side="left", padx=5)
        search_entry.bind("<KeyRelease>", self.update_search_selection)

        # Textbereich für Spell-Details
        self.spell_detail = tk.Text(self.detail_frame, width=50, height=20, state="disabled", wrap="word")
        self.spell_detail.pack(fill="both", expand=True)

        # Button zum Hinzufügen/Entfernen
        self.toggle_button = ttk.Button(self.detail_frame, text="Hinzufügen", command=self.toggle_current_spell)
        self.toggle_button.pack(fill="x", pady=(5, 0))

        # Speichert den aktuell angezeigten Spell
        self.current_detail_spell = None

        # Frame: Buttons
        button_frame = ttk.Frame(self.root)
        button_frame.grid(row=2, column=0, pady=10)

        ttk.Button(button_frame, text="JSON laden", command=self.load_json).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Sammlung speichern", command=self.save_collection).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="Sammlung laden", command=self.load_collection).grid(row=0, column=3, padx=5)


    def set_status(self, message):
        self.status_var.set(message)
        self.root.update_idletasks()

    def update_search_selection(self, event=None):
        query = self.search_var.get().lower()
        if not query:
            return

        for name, (var, spell) in self.checkbox_vars.items():
            if name.startswith(query):
                self.show_spell_details(spell)
                return

    def toggle_current_spell(self):
        spell = self.current_detail_spell
        if not spell:
            return

        key = (spell["name"].lower(), spell.get("source", "Core").lower())
        #var = self.checkbox_vars.get(spell["name"].lower(), (None,))[0] # OLD
        var = self.checkbox_vars.get(key, (None,))[0]
        if not var:
            return

        # Toggle Zustand
        new_state = not var.get()
        var.set(new_state)
        self.toggle_collection(spell, var)

        # Button-Text aktualisieren
        self.toggle_button.config(text="Entfernen" if new_state else "Hinzufügen")


    def reset_filters(self):
        self.class_listbox.selection_clear(0, tk.END)
        self.school_listbox.selection_clear(0, tk.END)

        self.selected_levels.clear()
        for btn in self.level_buttons.values():
            btn.config(relief="raised", bg=self.root.cget("bg"))

        self.apply_filter()


    def load_json(self):
        filepath = filedialog.askopenfilename(title="Spell JSON laden", filetypes=[("JSON Files", "*.json")])
        if not filepath:
            return
        self.load_spells_from_path(filepath)


    def toggle_level(self, level):
        if level in self.selected_levels:
            self.selected_levels.remove(level)
            self.level_buttons[level].config(relief="raised", bg=self.root.cget("bg"))
        else:
            self.selected_levels.add(level)
            self.level_buttons[level].config(relief="sunken", bg="#d0ffd0")
        self.apply_filter()


    def update_dynamic_filters(self):
        class_set = set()
        school_set = set()

        for spell in self.all_spells:
            for cls in spell.get("classes", []):
                class_set.add(cls.lower())
            school_set.add(spell.get("school", "").lower())

        self.class_listbox.delete(0, tk.END)
        for cls in sorted(class_set):
            self.class_listbox.insert(tk.END, cls.capitalize())

        self.school_listbox.delete(0, tk.END)
        for sch in sorted(school_set):
            self.school_listbox.insert(tk.END, sch.capitalize())

    def get_listbox_selection(self, listbox):
        selected = [listbox.get(i).lower() for i in listbox.curselection()]
        return selected  # keine spezielle "alle"-Behandlung mehr


    def apply_filter(self):
        selected_classes = self.get_listbox_selection(self.class_listbox)
        selected_schools = self.get_listbox_selection(self.school_listbox)

        selected_levels = self.selected_levels

        def match(spell):
            matches_class = any(cls in [c.lower() for c in spell.get("classes", [])] for cls in
                                selected_classes) if selected_classes else True
            matches_school = spell.get("school", "").lower() in selected_schools if selected_schools else True
            spell_lvl = str(spell.get("level", "")).lower()
            matches_level = spell_lvl in selected_levels if selected_levels else True
            return matches_class and matches_school and matches_level

        # if selected list is empty → keine Filterung (zeigt alle)
        self.filtered_spells = sorted(
            [s for s in self.all_spells if match(s)],
            key=lambda s: s.get("name", "").lower()
        )
        self.update_spell_list()

    def update_spell_list(self):
        for widget in self.spell_list_container.winfo_children():
            widget.destroy()

        self.checkbox_vars = {}
        self.label_refs = {}

        for spell in self.filtered_spells:
            row = ttk.Frame(self.spell_list_container)
            row.pack(fill="x", anchor="w", pady=1)

            var = tk.BooleanVar(value=spell in self.collection)
            cb = tk.Checkbutton(row, variable=var, command=lambda s=spell, v=var: self.toggle_collection(s, v))
            cb.grid(row=0, column=0, sticky="w")

            source = spell.get("source", "Core")
            label_text = f"{spell.get('name', 'Unbenannt')} ({source})"

            label = tk.Label(row, text=label_text, fg="blue", cursor="hand2", anchor="w")
            label.grid(row=0, column=1, sticky="w", padx=(5, 0))
            label.bind("<Button-1>", lambda e, s=spell: self.show_spell_details(s))
            # allow same spells from different sources
            key = (spell.get("name", "").lower(), spell.get("source", "Core").lower())
            self.checkbox_vars[key] = (var, spell)
            self.label_refs[key] = label

    def scroll_to_widget(self, widget):
        self.spell_canvas.update_idletasks()

        canvas_height = self.spell_canvas.winfo_height()
        container_height = self.spell_list_container.winfo_height()
        widget_y = widget.winfo_y()
        widget_height = widget.winfo_height()

        # Ziel: widget mittig scrollen
        center_y = widget_y + widget_height // 2 - canvas_height // 2

        # relative Position (0..1) in der Scrollregion berechnen
        rel_pos = center_y / max(container_height, 1)
        rel_pos = max(0, min(1, rel_pos))  # clamp between 0 and 1

        self.spell_canvas.yview_moveto(rel_pos)

    def show_spell_details(self, spell):
        # 1. Visuelle Markierung zurücksetzen
        for label in self.label_refs.values():
            label.config(bg=None)

        # 2. Selektiertes Spell-Label hervorheben
        spell_key = spell["name"].lower()
        if spell_key in self.label_refs:
            selected_label = self.label_refs[spell_key]
            selected_label.config(bg="#d0ebff")  # zartes Blau

            # 3. Scroll dahin
            #self.scroll_to_widget(selected_label)

        self.spell_detail.config(state="normal")
        self.spell_detail.delete("1.0", tk.END)

        text = f"Quelle: {spell.get('source', '-')}\n"
        text += f"Name: {spell.get('name')}\n"
        text += f"Level: {spell.get('level')}\n"
        text += f"Schule: {spell.get('school')}\n"
        text += f"Klassen: {', '.join(spell.get('classes', []))}\n"
        text += f"Wirkzeit: {spell.get('casting_time')}\n"
        text += f"Reichweite: {spell.get('range')}\n"
        text += f"Dauer: {spell.get('duration')}\n"
        text += f"Ritual: {'Ja' if spell.get('ritual') else 'Nein'}\n"
        text += f"\nBeschreibung:\n{spell.get('description')}\n"

        # Zusätzliche Felder (falls vorhanden)
        if spell.get("AreaOfEffect"):
            text += f"\nWirkungsbereich: {spell['AreaOfEffect']}\n"

        if spell.get("AttackSave") and spell["AttackSave"].lower() != "none":
            text += f"Angriff/Wurf: {spell['AttackSave']}\n"

        if spell.get("DmgDice"):
            text += "Schaden:\n"
            for entry in spell["DmgDice"]:
                dice = entry.get("dice", "")
                dtype = entry.get("type", "").capitalize()
                text += f"  {dice} {dtype}\n"

        self.spell_detail.insert("1.0", text)
        self.spell_detail.config(state="disabled")

        self.current_detail_spell = spell
        # Buttonstatus anpassen
        var = self.checkbox_vars.get(spell["name"].lower(), (None,))[0]
        if var and var.get():
            self.toggle_button.config(text="Entfernen")
        else:
            self.toggle_button.config(text="Hinzufügen")

    def toggle_collection(self, spell, var):
        if var.get():
            if spell not in self.collection:
                self.collection.append(spell)
        else:
            if spell in self.collection:
                self.collection.remove(spell)
        self.set_status(f"{len(self.collection)} Zauber in Sammlung")


    def save_collection(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if not filepath:
            return
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.collection, f, indent=4)
        self.set_status(f"{len(self.collection)} Zauber gespeichert.")

    def load_collection(self):
        filepath = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if not filepath:
            return
        with open(filepath, "r", encoding="utf-8") as f:
            self.collection = json.load(f)
        self.set_status(f"{len(self.collection)} Zauber in Sammlung geladen.")

    def new_spell_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Zauber erstellen")

        ttk.Label(dialog, text="Wie möchtest du den Zauber erstellen?").pack(pady=10)

        ttk.Button(dialog, text="Aus Vorlage", command=lambda: [dialog.destroy(), self.select_spell_template()]).pack(
            pady=5)
        ttk.Button(dialog, text="Neu", command=lambda: [dialog.destroy(), self.open_spell_editor({})]).pack(pady=5)

    def select_spell_template(self):
        selector = tk.Toplevel(self.root)
        selector.title("Vorlage auswählen")

        ttk.Label(selector, text="Wähle einen bestehenden Zauber:").pack(pady=5)

        spell_names = [s["name"] for s in self.all_spells]
        selected_spell = tk.StringVar(value=spell_names[0] if spell_names else "")

        dropdown = ttk.Combobox(selector, values=spell_names, textvariable=selected_spell, state="readonly", width=40)
        dropdown.pack(pady=5)

        def confirm():
            name = selected_spell.get()
            spell = next((s for s in self.all_spells if s["name"] == name), None)
            if spell:
                self.open_spell_editor(spell)
            selector.destroy()

        ttk.Button(selector, text="Weiter", command=confirm).pack(pady=5)

    def open_spell_editor(self, spell_data):
        editor = tk.Toplevel(self.root)
        editor.title("Zauber bearbeiten")

        entries = {}

        # --- Quelle (Entry, Standard: Homebrew) ---
        frame = ttk.Frame(editor)
        frame.pack(fill="x", pady=2)
        ttk.Label(frame, text="Quelle:").pack(side="left", padx=(0, 10))
        source_entry = ttk.Entry(frame)
        source_entry.insert(0, spell_data.get("source", "Homebrew"))
        source_entry.pack(fill="x", expand=True)
        entries["source"] = source_entry

        # --- Name ---
        frame = ttk.Frame(editor)
        frame.pack(fill="x", pady=2)
        ttk.Label(frame, text="Name:").pack(side="left", padx=(0, 10))
        name_entry = ttk.Entry(frame)
        name_entry.insert(0, spell_data.get("name", ""))
        name_entry.pack(fill="x", expand=True)
        entries["name"] = name_entry

        # --- Level (Dropdown) ---
        frame = ttk.Frame(editor)
        frame.pack(fill="x", pady=2)
        ttk.Label(frame, text="Level:").pack(side="left", padx=(0, 10))
        levels = ["Cantrip"] + [str(i) for i in range(1, 10)]
        level_var = tk.StringVar(value=str(spell_data.get("level", "Cantrip")))
        ttk.OptionMenu(frame, level_var, level_var.get(), *levels).pack(fill="x")
        entries["level"] = level_var

        # --- Schule (Dropdown) ---
        frame = ttk.Frame(editor)
        frame.pack(fill="x", pady=2)
        ttk.Label(frame, text="Schule:").pack(side="left", padx=(0, 10))
        school_options = sorted({s.get("school", "") for s in self.all_spells if s.get("school")})
        school_var = tk.StringVar(value=spell_data.get("school", ""))
        ttk.OptionMenu(frame, school_var, school_var.get(), *school_options).pack(fill="x")
        entries["school"] = school_var

        # --- Klassen (Checkboxen) ---
        frame = ttk.Frame(editor)
        frame.pack(fill="x", pady=2)
        ttk.Label(frame, text="Klassen:").pack(anchor="w")
        all_classes = sorted({cls for s in self.all_spells for cls in s.get("classes", [])})
        selected_classes = set(spell_data.get("classes", []))
        class_vars = {}
        for cls in all_classes:
            var = tk.BooleanVar(value=cls in selected_classes)
            chk = ttk.Checkbutton(frame, text=cls, variable=var)
            chk.pack(side="left", padx=2)
            class_vars[cls] = var
        entries["classes"] = class_vars

        # --- Komponenten (Checkboxen) ---
        frame = ttk.Frame(editor)
        frame.pack(fill="x", pady=2)
        ttk.Label(frame, text="Komponenten:").pack(anchor="w")
        comp_data = spell_data.get("components", {})
        comp_vars = {}
        for comp in ["verbal", "somatic", "material"]:
            var = tk.BooleanVar(value=comp_data.get(comp, False))
            chk = ttk.Checkbutton(frame, text=comp.capitalize(), variable=var)
            chk.pack(side="left", padx=2)
            comp_vars[comp] = var
        entries["components"] = comp_vars

        # --- Wirkzeit (Dropdown) ---
        frame = ttk.Frame(editor)
        frame.pack(fill="x", pady=2)
        ttk.Label(frame, text="Wirkzeit:").pack(side="left", padx=(0, 10))
        casting_options = ["1 Action", "1 Bonus Action", "1 Reaction", "Ritual", "Other"]
        cast_var = tk.StringVar(value=spell_data.get("casting_time", ""))
        ttk.OptionMenu(frame, cast_var, cast_var.get(), *casting_options).pack(fill="x")
        entries["casting_time"] = cast_var

        # --- Reichweite (Entry) ---
        frame = ttk.Frame(editor)
        frame.pack(fill="x", pady=2)
        ttk.Label(frame, text="Reichweite:").pack(side="left", padx=(0, 10))
        range_entry = ttk.Entry(frame)
        range_entry.insert(0, spell_data.get("range", ""))
        range_entry.pack(fill="x", expand=True)
        entries["range"] = range_entry

        # --- Dauer (Dropdown) ---
        frame = ttk.Frame(editor)
        frame.pack(fill="x", pady=2)
        ttk.Label(frame, text="Dauer:").pack(side="left", padx=(0, 10))
        duration_options = ["Instantaneous", "1 Round", "1 Minute", "10 Minutes", "1 Hour", "8 Hours", "24 Hours",
                            "Until Dispelled", "Special"]
        duration_var = tk.StringVar(value=spell_data.get("duration", ""))
        ttk.OptionMenu(frame, duration_var, duration_var.get(), *duration_options).pack(fill="x")
        entries["duration"] = duration_var

        # --- Ritual (Checkbox) ---
        frame = ttk.Frame(editor)
        frame.pack(fill="x", pady=2)
        ttk.Label(frame, text="Ritual:").pack(side="left", padx=(0, 10))
        ritual_var = tk.BooleanVar(value=spell_data.get("ritual", False))
        ttk.Checkbutton(frame, variable=ritual_var).pack(side="left")
        entries["ritual"] = ritual_var

        # --- Beschreibung (Text) ---
        frame = ttk.Frame(editor)
        frame.pack(fill="x", pady=2)
        ttk.Label(frame, text="Beschreibung:").pack(anchor="w")
        description = tk.Text(frame, height=6, wrap="word")
        description.insert("1.0", spell_data.get("description", ""))
        description.pack(fill="x", expand=True)
        entries["description"] = description

        # --- Wirkungsbereich (Entry) ---
        frame = ttk.Frame(editor)
        frame.pack(fill="x", pady=2)
        ttk.Label(frame, text="Wirkungsbereich:").pack(side="left", padx=(0, 10))
        aoe_entry = ttk.Entry(frame)
        aoe_entry.insert(0, spell_data.get("AreaOfEffect", ""))
        aoe_entry.pack(fill="x", expand=True)
        entries["AreaOfEffect"] = aoe_entry

        # --- Attack/Save (Dropdown) ---
        frame = ttk.Frame(editor)
        frame.pack(fill="x", pady=2)
        ttk.Label(frame, text="Attack/Save:").pack(side="left", padx=(0, 10))
        save_options = ["None", "STR Save", "DEX Save", "CON Save", "INT Save", "WIS Save", "CHA Save", "Spell Attack"]
        save_var = tk.StringVar(value=spell_data.get("AttackSave", "None"))
        ttk.OptionMenu(frame, save_var, save_var.get(), *save_options).pack(fill="x")
        entries["AttackSave"] = save_var

        # --- Schadenswürfel (mehrzeilig) ---
        damage_types = ["Acid", "Bludgeoning", "Cold", "Fire", "Force", "Lightning", "Necrotic", "Piercing", "Poison",
                        "Psychic", "Radiant", "Slashing", "Thunder"]

        dmg_frame = ttk.Frame(editor)
        dmg_frame.pack(fill="x", pady=5)
        ttk.Label(dmg_frame, text="Schadenswürfel:").pack(anchor="w")

        dmg_rows_frame = ttk.Frame(dmg_frame)
        dmg_rows_frame.pack(fill="x")
        dmg_entries = []

        def add_damage_row(data=None):
            row = ttk.Frame(dmg_rows_frame)
            row.pack(fill="x", pady=1)

            dice_entry = ttk.Entry(row, width=10)
            dice_entry.insert(0, data["dice"] if data else "")
            dice_entry.pack(side="left", padx=(0, 5))

            dmg_type = tk.StringVar(value=data["type"] if data else damage_types[0])
            ttk.OptionMenu(row, dmg_type, dmg_type.get(), *damage_types).pack(side="left")

            dmg_entries.append((dice_entry, dmg_type))

        # Zeilen laden
        for dmg in spell_data.get("DmgDice", []):
            add_damage_row(dmg)
        if not spell_data.get("DmgDice"):
            add_damage_row()

        # + Button unterhalb der Zeilen
        ttk.Button(dmg_frame, text="+ add Dice", command=add_damage_row).pack(pady=(5, 0), anchor="w")

        entries["DmgDice"] = dmg_entries

        # --- Speichern ---
        def save_spell():
            new_spell = {
                "source": entries["source"].get().strip(),
                "name": entries["name"].get().strip(),
                "level": 0 if entries["level"].get() == "Cantrip" else int(entries["level"].get()),
                "school": entries["school"].get().strip(),
                "classes": [cls for cls, var in entries["classes"].items() if var.get()],
                "components": {k: v.get() for k, v in entries["components"].items()},
                "casting_time": entries["casting_time"].get().strip(),
                "range": entries["range"].get().strip(),
                "duration": entries["duration"].get().strip(),
                "ritual": entries["ritual"].get(),
                "description": entries["description"].get("1.0", "end").strip(),
                "AreaOfEffect": entries["AreaOfEffect"].get().strip(),
                "AttackSave": entries["AttackSave"].get().strip(),
                "DmgDice": [
                    {"dice": dice_entry.get().strip(), "type": type_var.get().strip()}
                    for dice_entry, type_var in entries["DmgDice"]
                    if dice_entry.get().strip()
                ]
            }

            self.custom_spells = [s for s in self.custom_spells if s.get("name") != new_spell["name"]]
            self.custom_spells.append(new_spell)
            self.save_custom_spells()

            self.all_spells.append(new_spell)
            self.filtered_spells = self.all_spells
            self.update_spell_list()
            self.update_dynamic_filters()
            editor.destroy()
            self.set_status(f"Neuer Custom-Zauber '{new_spell.get('name')}' hinzugefügt.")

        ttk.Button(editor, text="Speichern", command=save_spell).pack(pady=10)

    def save_custom_spells(self):
        custom_path = pathlib.Path("src/custom_spells.json")
        with open(custom_path, "w", encoding="utf-8") as f:
            json.dump(self.custom_spells, f, indent=4, ensure_ascii=False)
        self.set_status("Custom-Zauber gespeichert.")


if __name__ == "__main__":
    root = tk.Tk()
    app = SpellManager(root)
    root.mainloop()
