from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import Color
from reportlab.lib.colors import HexColor
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
from reportlab.platypus import Paragraph
from card_renderer_utils import SCHOOL_COLORS,CLASS_COLORS
import textwrap
import json
import os
import re
from PIL import Image

# Maße
CARD_WIDTH_MM = 63
CARD_HEIGHT_MM = 88
CARDS_PER_ROW = 3
CARDS_PER_COL = 3
MARGIN_MM = 10
SPACING_MM = 5

FONT_NAME="Times-Roman"

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


def render_card_pdf(c, x0, y0, spell, config, assets_dir="src/img"):
    card_w = 63 * mm
    card_h = 88 * mm
    has_concentration = False

    print("== Karte:", spell.get("name", "Unbenannt"), "==")

    # Hilfsfunktionen (wie in Vorschau)
    def px(conf): return x0 + (conf.get("x", 0) / 100) * card_w
    def py(conf):
        corrected_y = ((100- conf.get("y", 0)) / 100)
        print("Y-Pos: ", conf.get("y"), corrected_y)
        return y0 + ((100- conf.get("y", 0)) / 100) * card_h
    def fw(conf, key): return (conf.get(key, 10) / 100) * card_w
    def fs(conf): return conf.get("font_size", 10)
    def fc(conf): return HexColor(conf.get("color", "#000000"))

    # Farben basierend auf Mode
    def fc_dynamic(conf, spell):
        mode = conf.get("mode", "single")
        print(f"[fc] Mode: {mode}, Color: {conf.get('color','None')}, Spell: {conf.get('name')}")
        if mode == "single" or not spell:
            return HexColor(conf.get("color", "#000000"))
        if mode == "class":
            cls = (spell.get("classes") or [None])[0]
            c1 = CLASS_COLORS.get(cls.lower())
            print("Class Color: ",HexColor(c1))
            return HexColor(CLASS_COLORS.get(cls.lower(), "#000000")) #if cls else HexColor("#000000")
        if mode == "school":
            school = spell.get("school", "").lower()
            c1 = SCHOOL_COLORS.get(school.lower())
            print("School Color: ", HexColor(c1))
            return HexColor(SCHOOL_COLORS.get(school, "#000000"))
        return HexColor("#000000")

    # Hintergrund
    bg_conf = config.get("background_image", {})
    bg_path = bg_conf.get("path")
    if bg_path and os.path.exists(bg_path):
        try:
            c.drawImage(bg_path, x0, y0, width=card_w, height=card_h)
        except:
            pass
    else:
        c.setFillColor(HexColor("#ffffff"))
        c.rect(x0, y0, card_w, card_h, fill=1)

    # Rahmen
    frame = config.get("frame", {})
    color = fc_dynamic(frame, spell)
    thickness = frame.get("thickness", 1)
    print("Rahmenfarbe (vor fc_dynamic):", frame.get("color"))
    print("Rahmenmode:", frame.get("mode"))
    print("Bestimmte Farbe (fc_dynamic):", fc_dynamic(frame, spell))
    print("Dicke des Rhmens: ", thickness)
    c.setStrokeColor(color)
    c.setLineWidth(thickness)
    c.roundRect(x0, y0, card_w, card_h, frame.get("roundness", 0), fill=0)
    c.setLineWidth(0) #zurücksetzen für andere icons

    # Beschriftungen
    # Komponenten nur als raw
    comps = spell.get("components", "")
    if isinstance(comps, dict):
        comps = comps.get("raw", comps)

    # Save-DC als Kürzel
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
        "components": f"Components: {comps}"
    }

    for key, text in text_elements.items():
        conf = config.get(key)
        if "concentration" in text.lower():
            has_concentration = True

        if conf:
            tx = px(conf)
            ty = py(conf)
            max_width = fw(conf, "max_width") if "max_width" in conf else card_w - 10
            style = ParagraphStyle(
                name="Normal",
                fontName=FONT_NAME,
                fontSize=fs(conf)-1,
                textColor=fc(conf)
            )
            para = Paragraph(text, style)
            w, h = para.wrap(max_width, 100)
            para.wrapOn(c, max_width, 100)
            print(f"y-Pos final ({key}): {ty- h}= {ty} - {h}")
            para.drawOn(c, tx, ty - h)

    # Desc
    desc = spell.get("description", "")
    desc_conf = config.get("description")
    if desc_conf:
        max_length = 800
        if (len(desc) > max_length):
            desc = desc[:(max_length - 3)] + "..."
        tx = px(desc_conf)
        ty = py(desc_conf)
        max_width = fw(desc_conf, "max_width") if "max_width" in desc_conf else card_w - 10
        style = ParagraphStyle(
            name="Normal",
            fontName=FONT_NAME,
            fontSize=fs(desc_conf) - 1,
            leading=fs(desc_conf) * 1.1,
            textColor=fc(desc_conf)
        )
        para = Paragraph(desc, style)
        w, h = para.wrap(max_width, 100)
        para.wrapOn(c, max_width-10, 100)
        para.drawOn(c, tx, ty - fs(desc_conf) - h)


    # Schadenswürfel extrahieren
    dmg_dicex = extract_damage_dice_from_description(desc)
    print("Desc: ", desc)
    print("extract: ",len(dmg_dicex))
    if len(dmg_dicex)>0:
        conf = config.get("damage_dice", {})
        tx = px(conf)
        ty = py(conf)
        font_size = fs(conf)
        icon_size = font_size + 2
        spacing = 1 * mm
        font_size = font_size - 1
        correctionY = 10  # 21

        c.setFont(FONT_NAME, font_size)
        c.setFillColor(fc(conf))
        c.drawString(tx, ty - correctionY, "Damage:")

        # Position nach dem "Damage:" Label
        label_width = c.stringWidth("Damage:", FONT_NAME, font_size)
        ix = tx + label_width + spacing  # tx + 45
        iy = ty - 1  # kleine Justierung, SVG beginnt oft höher ty - font_size + 1

        for i in range(len(dmg_dicex)):
            print("Schadenswürfel: ", dmg_dicex[i])
            # Schadenswürfel + Icon
            dmg_info = dmg_dicex[i]
            parts = dmg_info.split()
            iyX = iy - i * 10 - correctionY
            tyX = ty - i * 10 - correctionY
            if len(parts) >= 2:
                print("Parts von damage_dice korrekt gefunden?", len(parts), parts[0], parts[1])
                dice, dmg_type = parts[0], parts[1].lower()
                # SVG-Icon
                icon_path = os.path.join(assets_dir, "dmg", f"dmg_{dmg_type}.svg")
                icon_width = 20
                if os.path.exists(icon_path):
                    print(f"SVG gefunden: {icon_path}")
                    drawing = svg2rlg(icon_path)
                    if drawing:
                        scale = icon_size / max(drawing.width, drawing.height)
                        print(f"SVG Size: {drawing.width}x{drawing.height}")
                        print("Debug: svg-Scale: ", scale)
                        print(f"Icon {dmg_type} → Pos: ({tx}, {ty}) / Path: {icon_path}")
                        drawing.scale(scale, scale)
                        print("y-pos-correction: ", iy, iyX)
                        icon_width = drawing.width * scale
                        print("finale y-Pos icon: ", iyX)
                        renderPDF.draw(drawing, c, ix, iyX)
                    else:
                        print("SVG konnte nicht geladen werden.")
                        # Fallback: Kürzel als Text
                        icon_width = c.stringWidth(f"[{dmg_type.upper()}]", FONT_NAME, font_size)
                        w, h = para.wrap(icon_width, 100)
                        print("finale y-Pos Text, h: ", iyX, h)
                        c.drawString(ix, tyX - h, f"[{dmg_type.lower()}]")
                else:
                    print("SVG-Pfad fehlt:", icon_path)
                    if dmg_type.lower() == "when":
                        c.drawString(ix, tyX, "[incr.w.lvl.]")
                        icon_width = c.stringWidth("[incr.w.lvl.]", FONT_NAME, font_size)
                    else:
                        c.drawString(ix, tyX, f"[{dmg_type.lower()}]")
                        icon_width = c.stringWidth(f"[{dmg_type.upper()}]", FONT_NAME, font_size)
                # Schadenswürfel-Zahl
                c.drawString(ix + icon_width + spacing, tyX, dice)
            else:
                print("Damage_element hat keine 2 Teile.")
    else:
        print("Keine Schadenswürfel")

    #Konzentration Icons
    conf = config.get("concentration_icon")
    if conf and has_concentration:
        icon_path = "src/img/concentration.svg"
        ix = px(conf)
        iy = py(conf) -21
        iw = fw(conf, "width")
        ih = fw(conf, "height")
        if os.path.exists(icon_path):
            drawing = svg2rlg(icon_path)
            if drawing:
                scale = min(iw / drawing.width, ih / drawing.height)
                drawing.scale(scale, scale)
                print(f"CON-icon: {ix},{iy} scale: {scale}, h:{ih}, w:{iw}")
                renderPDF.draw(drawing, c, ix, iy -ih)
            else:
                print("SVG konnte nicht geladen werden:", icon_path)
        else:
            print("Konzentrations-Icon nicht gefunden:", icon_path)

    #Schul-Symbol andrucken
    school_name = spell.get("school", "").lower()
    conf = config.get("school_icon")
    if conf and school_name:
        icon_path = f"src/img/school/{school_name}.png"
        ix = px(conf)
        iy = py(conf)
        iyX = iy + 15
        iw = fw(conf, "width")
        ih = fw(conf, "height")
        if os.path.exists(icon_path):
            try:
                c.drawImage(icon_path, ix, iyX, width=iw, height=ih, preserveAspectRatio=True, mask='auto')
            except Exception as e:
                print(f"Fehler beim Zeichnen von {icon_path}: {e}")
        else:
            print("Schul-Icon nicht gefunden:", icon_path)
    else:
        print("keine Schule?")


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
            #draw_cut_marks(c, x, y, mm_to_points(CARD_WIDTH_MM), mm_to_points(CARD_HEIGHT_MM))

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

def extract_damage_dice_from_description(desc):
    matches = re.findall(r"\b(\d+d\d+\s+\w+)\b", desc.lower())
    return matches if matches else []
