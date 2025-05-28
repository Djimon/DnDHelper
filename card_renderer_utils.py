CLASS_COLORS = {
    "wizard": "#5e7eff",
    "sorcerer": "#ff66cc",
    "cleric": "#ccccff",
    "paladin": "#ffe680",
    "druid": "#88cc88",
    "bard": "#ff99cc",
    "warlock": "#9900cc",
    "ranger": "#66cc66",
    "fighter": "#cc9966",
    "rogue": "#999999",
    "monk": "#ccffcc",
    "barbarian": "#ff6666",
    "artificer": "#ccffff"
}

SCHOOL_COLORS = {
    "abjuration": "#006699",
    "conjuration": "#00cc99",
    "divination": "#9999ff",
    "enchantment": "#ff99cc",
    "evocation": "#ff3300",
    "illusion": "#cc66ff",
    "necromancy": "#333333",
    "transmutation": "#ffcc00"
}

def px(conf, x0, w):
    return x0 + (conf.get("x", 0) / 100) * w

def py(conf, y0, h):
    return y0 + (conf.get("y", 0) / 100) * h

def fw(conf, key, w):
    return (conf.get(key, 10) / 100) * w

def fh(conf, key, h):
    return (conf.get(key, 10) / 100) * h

def fs(conf):
    return int(conf.get("font_size", 10))

def fc(conf, spell_data=None):
    """Bestimmt die Farbe des Elements abhängig vom Modus (single, class, school)."""
    mode = conf.get("mode", "single")
    color = conf.get("color", "#000000")

    if mode == "single" or not spell_data:
        return color

    if mode == "class":
        # Nimm die erste Klasse als Basis für Farbe
        cls = (spell_data.get("classes") or [None])[0]
        return CLASS_COLORS.get(cls.lower(), color) if cls else color

    if mode == "school":
        school = spell_data.get("school", "").lower()
        return SCHOOL_COLORS.get(school, color)

    return color


def draw_icons(canvas, config_data, x0, y0, w, h):
    icon_elements = {
        "school_icon": "#8888ff",
        "area_icon": "#88cc88",
        "concentration_icon": "#ff8888"
    }

    for key, color in icon_elements.items():
        conf = config_data.get(key)
        if conf:
            ix = px(conf, x0, w)
            iy = py(conf, y0, h)
            iw = fw(conf, "width", w)
            ih = fh(conf, "height", h)
            alpha = conf.get("opacity", 100)
            canvas.create_rectangle(
                ix, iy, ix + iw, iy + ih,
                fill=hex_with_alpha(color, alpha),
                outline="#222"
            )

def draw_text_elements(canvas, config_data, spell_data, x0, y0, w, h):
    components = spell_data.get("components", "")
    if isinstance(components, dict):
        components = components.get("raw", components)

    save_dc = spell_data.get("save_dc", "")
    if isinstance(save_dc, str):
        save_dc = {
            "dexterity": "DEX", "constitution": "CON", "strength": "STR",
            "intelligence": "INT", "wisdom": "WIS", "charisma": "CHA"
        }.get(save_dc.lower(), save_dc)

    text_elements = {
        "spell_name": spell_data.get("name", "Unbenannt"),
        "spell_level": f"Level {spell_data.get('level', '')}",
        "casting_time": spell_data.get("casting_time", ""),
        "duration": spell_data.get("duration", ""),
        "range": f"Range: {spell_data.get('range', '')}",
        "area_of_effect": spell_data.get("area_of_effect", ""),
        "components": f"Components: {components}",
        "save_dc": f"Attack/Save: {save_dc}",
        "description": spell_data.get("description", "")
    }

    for key, text in text_elements.items():
        conf = config_data.get(key)
        if conf:
            max_width = fw(conf, "max_width", w) if "max_width" in conf else w-40
            canvas.create_text(
                px(conf, x0, w), py(conf, y0, h),
                text=text, anchor="nw",
                fill=fc(conf),
                font=("Arial", fs(conf)),
                width=max_width if key not in ["spell_name", "spell_level", "range"] else None
            )

def draw_damage(canvas, config_data, spell_data, x0, y0, w, h):
    conf = config_data.get("damage_dice", {})
    ix = px(conf, x0, w)
    iy = py(conf, y0, h)
    font_size = fs(conf)
    icon_size = font_size + 4
    spacing = 5
    current_y = iy

    # Quelle vorbereiten
    dmg_entries = []

    if isinstance(spell_data.get("DmgDice"), list) and spell_data["DmgDice"]:
        dmg_entries = [
            {"dice": entry.get("dice", ""), "type": entry.get("type", "").capitalize()}
            for entry in spell_data["DmgDice"]
        ]
    else:
        # Fallback auf damage_dice-Textfeld
        damage_info = spell_data.get("damage_dice", "")
        if damage_info:
            parts = damage_info.split()
            if len(parts) >= 2:
                dmg_entries = [{"dice": parts[0], "type": parts[1].capitalize()}]

    if not dmg_entries:
        return  # Keine Anzeige nötig

    # Gemeinsames Rendering
    canvas.create_text(
        ix, current_y,
        text="Damage:",
        anchor="nw",
        fill=fc(conf),
        font=("Arial", font_size)
    )
    current_y += font_size + 4

    for entry in dmg_entries:
        dice = entry["dice"]
        dmg_type = entry["type"]

        canvas.create_oval(ix, current_y, ix + icon_size, current_y + icon_size, fill="#faa", outline="#600")
        canvas.create_text(
            ix + icon_size + spacing, current_y,
            text=f"{dice} {dmg_type}",
            anchor="nw",
            fill=fc(conf),
            font=("Arial", font_size)
        )
        current_y += icon_size + spacing

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

