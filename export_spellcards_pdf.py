from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import Color
from reportlab.lib.colors import HexColor
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
from reportlab.platypus import Paragraph
from card_renderer_utils import fc as fcSpell

import textwrap
import json
import os
from PIL import Image

# Maße
CARD_WIDTH_MM = 63
CARD_HEIGHT_MM = 88
CARDS_PER_ROW = 3
CARDS_PER_COL = 3
MARGIN_MM = 10
SPACING_MM = 5

def mm_to_points(mm_val):
    return mm_val * mm

def draw_cut_marks(c, x, y, w, h):
    mark_len = mm_to_points(2)
    color = Color(0.5, 0.5, 0.5)
    c.setStrokeColor(color)
    c.setLineWidth(0.2)
    # horizontal top
    c.line(x, y, x + mark_len, y)
    c.line(x + w - mark_len, y, x + w, y)
    # horizontal bottom
    c.line(x, y + h, x + mark_len, y + h)
    c.line(x + w - mark_len, y + h, x + w, y + h)
    # vertical left
    c.line(x, y, x, y + mark_len)
    c.line(x, y + h - mark_len, x, y + h)
    # vertical right
    c.line(x + w, y, x + w, y + mark_len)
    c.line(x + w, y + h - mark_len, x + w, y + h)

def hex_to_rgb(hex_color):
    """Wandle Hex in RGB Tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4))

def render_card_pdf(c: canvas.Canvas, x, y, spell, config, assets_dir="src/img"):
    card_w = 63 * mm
    card_h = 88 * mm

    def px(conf, key="x"):
        return x + (conf.get(key, 0) / 100) * card_w

    def py(conf, key="y"):
        #return y + (conf.get(key, 0) / 100) * card_h
        return y + (1 - conf.get("y", 0) / 100) * card_h

    def fw(conf, key):
        return (conf.get(key, 10) / 100) * card_w

    def fh(conf, key):
        return (conf.get(key, 10) / 100) * card_h

    def fs(conf):
        return conf.get("font_size", 10)

    def fc(conf):
        return conf.get("color", "#000000")

    # Hintergrund
    bg_conf = config.get("background_image", {})
    bg_path = bg_conf.get("path")
    if bg_path and os.path.exists(bg_path):
        try:
            c.drawImage(bg_path, x, y, width=card_w, height=card_h)
        except:
            pass
    else:
        c.setFillColor(HexColor("#ffffff"))
        c.rect(x, y, card_w, card_h, fill=1)

    # Rahmen
    frame = config.get("frame", {})
    c.setLineWidth(frame.get("thickness", 1))
    c.setStrokeColor(HexColor(fcSpell(frame, spell)))
    r = frame.get("roundness", 0)
    if r > 0:
        c.roundRect(x, y, card_w, card_h, radius=r, stroke=1, fill=0)
    else:
        c.rect(x, y, card_w, card_h, stroke=1, fill=0)

    # Optional: Komponente nur als raw darstellen
    components = spell.get("components", "")
    if isinstance(components, dict):
        components = components.get("raw", components)

    # Kürzel für Saving Throws
    save_dc = spell.get("save_dc", "")
    if isinstance(save_dc, str):
        save_dc = {
            "dexterity": "DEX", "constitution": "CON", "strength": "STR",
            "intelligence": "INT", "wisdom": "WIS", "charisma": "CHA"
        }.get(save_dc.lower(), save_dc)

    text_elements = {
        "spell_name": spell.get("name", "Unbenannt"),
        "spell_level": f"Level {spell.get('level', '')}",
        "casting_time": spell.get("casting_time", ""),
        "duration": spell.get("duration", ""),
        "range": f"Range: {spell.get('range', '')}",
        "area_of_effect": spell.get("area_of_effect", ""),
        "components": f"Components: {components}",
        "save_dc": f"Attack/Save: {save_dc}",
        "description": spell.get("description", "")
    }

    for key, text in text_elements.items():
        conf = config.get(key)
        if not conf:
            continue
        c.setFont("Helvetica", fs(conf))
        c.setFillColor(HexColor(fc(conf)))

        max_width = fw(conf, "max_width") if "max_width" in conf else card_w - 10
        tx = px(conf)
        ty = py(conf)

        #c.drawString(tx, ty, text)
        p = Paragraph(text, ParagraphStyle(
            name="Normal",
            fontName="Helvetica",
            fontSize=fs(conf),
            textColor=HexColor(fc(conf))
        ))
        p.wrapOn(c, max_width, 200)
        p.drawOn(c, tx, ty - fs(conf))

    # Schadenswürfel + Icon
    dmg_info = spell.get("damage_dice", "")
    if dmg_info:
        parts = dmg_info.split()
        if len(parts) >= 2:
            dice, dmg_type = parts[0], parts[1].lower()
            conf = config.get("damage_dice", {})
            tx = px(conf)
            ty = py(conf)
            font_size = fs(conf)
            spacing = 2 * mm
            icon_size = font_size + 4

            # "Damage:" Label
            c.setFont("Helvetica", font_size)
            c.setFillColor(HexColor(fc(conf)))
            c.drawString(tx, ty, "Damage:")

            # Position nach dem "Damage:" Label
            label_width = c.stringWidth("Damage:", "Helvetica", font_size)
            ix = tx + label_width + spacing
            iy = ty - 1  # kleine Justierung, SVG beginnt oft höher

            # SVG-Icon
            icon_path = os.path.join(assets_dir, "dmg", f"dmg_{dmg_type}.svg")
            if os.path.exists(icon_path):
                drawing = svg2rlg(icon_path)
                scale = icon_size / max(drawing.width, drawing.height)
                print("Debug: svg-Scale:" + scale)
                drawing.scale(scale, scale)
                if drawing.width == 0 or drawing.height == 0:
                    print("Fehler: SVG konnte nicht geladen oder skaliert werden.")
                renderPDF.draw(drawing, c, ix, iy)
                icon_width = drawing.width * scale
            else:
                # Fallback: Kürzel als Text
                c.drawString(ix, ty, f"[{dmg_type.lower()}]")
                icon_width = c.stringWidth(f"[{dmg_type.upper()}]", "Helvetica", font_size)

            # Schadenswürfel-Zahl
            c.drawString(ix + icon_width + spacing, ty, dice)

    # Icons (einfache Platzhalterfarben oder echte Icons)
    icon_elements = {
        "school_icon": os.path.join(assets_dir, "school.png"),
        "concentration_icon": os.path.join(assets_dir, "concentration.png")
    }

    for key, path in icon_elements.items():
        conf = config.get(key)
        if conf and os.path.exists(path):
            iw = fw(conf, "width")
            ih = fh(conf, "height")
            ix = px(conf)
            iy = py(conf)
            c.drawImage(path, ix, iy, width=iw, height=ih, mask='auto')

def render_backside_image(c, x, y, path):
    w = mm_to_points(CARD_WIDTH_MM)
    h = mm_to_points(CARD_HEIGHT_MM)
    try:
        img = Image.open(path)
        img = img.resize((int(w), int(h)))
        temp_path = "_temp_backside.jpg"
        img.save(temp_path)
        c.drawImage(temp_path, x, y, width=w, height=h)
        os.remove(temp_path)
    except Exception as e:
        print("Fehler beim Laden der Rückseite:", e)

def export_spellcards_pdf(spells, design_config, output_dir="output", backside_option="none", backside_path=None):
    os.makedirs(output_dir, exist_ok=True)
    base_name = "MyCollection"
    output_path = os.path.join(output_dir, f"DNDZauber_{base_name}.pdf")

    c = canvas.Canvas(output_path, pagesize=A4)
    page_width, page_height = A4

    cards_per_page = CARDS_PER_ROW * CARDS_PER_COL
    total_pages = (len(spells) + cards_per_page - 1) // cards_per_page

    print(f"Exportiere {len(spells)} Karten auf {total_pages} Seite(n)...")

    for page_idx in range(total_pages):
        for idx in range(cards_per_page):
            global_idx = page_idx * cards_per_page + idx
            if global_idx >= len(spells):
                break
            spell = spells[global_idx]

            col = idx % CARDS_PER_ROW
            row = idx // CARDS_PER_ROW

            #x = mm_to_points(MARGIN_MM + col * (CARD_WIDTH_MM + SPACING_MM))
            # Gesamtbreite des Kartenrasters berechnen
            total_width = CARDS_PER_ROW * CARD_WIDTH_MM + (CARDS_PER_ROW - 1) * SPACING_MM
            offset_x = (A4[0] - mm_to_points(total_width)) / 2  # zentrieren

            x = offset_x + mm_to_points(col * (CARD_WIDTH_MM + SPACING_MM))

            y = page_height - mm_to_points(MARGIN_MM + (row + 1) * CARD_HEIGHT_MM + row * SPACING_MM)

            #render_dummy_card(c, x, y, spell) # dummy
            render_card_pdf(c, x, y, spell, design_config)
            draw_cut_marks(c, x, y, mm_to_points(CARD_WIDTH_MM), mm_to_points(CARD_HEIGHT_MM))

        c.showPage()

    # Rückseiten rendern, falls gewünscht
    if backside_option != "none":
        for page_idx in range(total_pages):
            for idx in range(cards_per_page):
                col = idx % CARDS_PER_ROW
                row = idx // CARDS_PER_ROW

                x = mm_to_points(MARGIN_MM + col * (CARD_WIDTH_MM + SPACING_MM))
                y = page_height - mm_to_points(MARGIN_MM + (row + 1) * CARD_HEIGHT_MM + row * SPACING_MM)

                if backside_option == "custom" and backside_path:
                    render_backside_image(c, x, y, backside_path)
                elif backside_option == "preset":
                    render_backside_image(c, x, y, f"src/img/backdrop_1.png")

                draw_cut_marks(c, x, y, mm_to_points(CARD_WIDTH_MM), mm_to_points(CARD_HEIGHT_MM))

            c.showPage()

    c.save()
    print(f"PDF erfolgreich gespeichert unter: {output_path}")
