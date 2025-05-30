# 🧙‍♂️ DnDHelper

DnDHelper ist ein Python-basiertes Tool zur Erstellung, Verwaltung und dem Export von Zauberkarten für Dungeons & Dragons. Es ermöglicht das Design individueller Zauber, deren Organisation in Sammlungen und den Export als druckfertige PDF-Dateien.

## 🔧 Funktionen

- **Zauber-Designer**: Erstelle und bearbeite benutzerdefinierte Zauber mit Attributen wie Name, Level, Schule, Beschreibung und mehr.
- **Sammlungsverwaltung**: Organisiere Zauber in Sammlungen für verschiedene Charaktere oder Kampagnen (Ordner: "collections").
- **Karten-Rendering**: Nutze benutzerdefinierte Designs für die Darstellung der Zauberkarten.
- **PDF-Export**: Generiere druckfertige PDF-Dateien deiner Zaubersammlungen (Ordner: "output").

## 📁 Projektstruktur

```
DnDHelper/
├── collections/               # JSON-Dateien mit Zaubersammlungen
├── designs/                   # Designvorlagen für Zauberkarten
├── designs/                   # PDF-dateien landen hier
├── src/                       # Quellcode des Projekts
├── card_renderer_utils.py     # Hilfsfunktionen für das Kartenrendering
├── export_spellcards_pdf.py   # PDF-Exportfunktionalität
├── main.py                    # Hauptausführungsdatei (UI für alle 3 Module)
├── spell_designer.py          # Zauber-Designer-Modul
├── spell_exporter.py          # Exportmodul für Zauber
└── spell_manager.py           # Modul zur Verwaltung von Zaubern und Sammlungen
```

## 🚀 Installation

1. **Repository klonen**:
   ```bash
   git clone https://github.com/Djimon/DnDHelper.git
   cd DnDHelper
   ```

2. **Abhängigkeiten installieren**:
   ```bash
   pip install -r requirements.txt
   ```

   *Hinweis: Stelle sicher, dass Python 3.7 oder höher installiert ist.*

## 🧪 Nutzung

1. **Starte UI**:
   ```bash
   python main.py
   ```

## 🤝 Mitwirken

Beiträge sind willkommen! Wenn du neue Funktionen hinzufügen, Bugs beheben oder die Dokumentation verbessern möchtest, erstelle bitte einen Pull Request oder eröffne ein Issue.

## 📄 Lizenz

Dieses Projekt steht unter der [MIT-Lizenz](LICENSE).
