"""
Zertifikat-Generator fuer Domus Aperta.

Erzeugt PDF-Zertifikate im A4-Hochformat fuer alle 4 Stufen (Bronze/Silber/Gold/Platin).
Das Logo (logo_pdf.svg) wird pro Stufe automatisch in die Stufenfarbe umgefaerbt.

Usage:
    python generate_certificates.py
    (Erstellt 8 PDFs im Ordner 'zertifikate' -- je 1 Beispiel und 1 Leervorlage pro Stufe)

    # Oder programmatisch:
    from generate_certificates import generate_certificate
    generate_certificate("Max Muster", 82.5, "Gold", "output.pdf", datum="15. Maerz 2026")
"""

import io
from datetime import date
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF

HERE = Path(__file__).parent
LOGO_PDF_SVG = HERE / "logo_pdf.svg"
OUTPUT_DIR = HERE / "zertifikate"

# Stufendefinitionen
STUFEN = {
    "Bronze": {
        "min": 40, "max": 59,
        "titel": "Aspirant der Gastlichkeit",
        "motto": "Erste Schritte im Bund",
        "farbe": "#8B5A2B",
    },
    "Silber": {
        "min": 60, "max": 74,
        "titel": "Gesandter der Gastlichkeit",
        "motto": "Ehrenvoll im Empfang",
        "farbe": "#A8A8A8",
    },
    "Gold": {
        "min": 75, "max": 89,
        "titel": "Meister der Gastlichkeit",
        "motto": "Vorzueglich in Allem",
        "farbe": "#D4AF37",
    },
    "Platin": {
        "min": 90, "max": 105,
        "titel": "Grossmeister der Gastlichkeit",
        "motto": "Barmherziger Samariter",
        "farbe": "#E5E4E2",
    },
}


def _recolored_logo_drawing(farbe_hex: str):
    """Laedt logo_pdf.svg, ersetzt Gold durch die Stufenfarbe und gibt ein RLG-Drawing zurueck."""
    svg_text = LOGO_PDF_SVG.read_text(encoding="utf-8")
    recolored = svg_text.replace("#D4AF37", farbe_hex)
    # svglib braucht bytes (keine str mit XML-Deklaration)
    drawing = svg2rlg(io.BytesIO(recolored.encode("utf-8")))
    return drawing


def generate_certificate(
    name: str,
    punkte: float,
    stufe: str,
    output,
    datum: str | None = None,
    kategorien: dict | None = None,
) -> None:
    """
    Erzeugt ein Zertifikat-PDF.

    Args:
        name: Name des Gastgebers (leer lassen fuer Leervorlage).
        punkte: Punktzahl (0-105), oder None / 0 fuer Leervorlage.
        stufe: "Bronze" | "Silber" | "Gold" | "Platin".
        output: Dateipfad (str) ODER file-like object (z.B. BytesIO).
        datum: Freier Datumstext (z.B. "15. Maerz MMXXVI"). Default: heute.
        kategorien: Dict mit Einzelwerten, optional:
            {"empfang": 8, "essen": 9, "aufmerksamkeit": 8, "wow": 9, "bonus": 2}
    """
    info = STUFEN[stufe]
    farbe_hex = info["farbe"]
    farbe = HexColor(farbe_hex)
    bg = HexColor("#0F0F0F")
    text_hell = HexColor("#EDEDED")
    text_gedaempft = HexColor("#888888")

    W, H = A4

    c = canvas.Canvas(output, pagesize=A4)

    # Schwarzer Hintergrund
    c.setFillColor(bg)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Aeusserer Rahmen in Stufenfarbe
    c.setStrokeColor(farbe)
    c.setLineWidth(1.2)
    margin = 30
    c.rect(margin, margin, W - 2 * margin, H - 2 * margin, stroke=1, fill=0)

    # Innerer duenner Rahmen
    c.setLineWidth(0.4)
    inner = 45
    c.rect(inner, inner, W - 2 * inner, H - 2 * inner, stroke=1, fill=0)

    # -------------------------------------------------------------------
    # Layout: Y-Koordinaten werden von oben nach unten geplant
    # A4 = 595 x 842 pt
    # -------------------------------------------------------------------

    # Logo (umgefaerbt) oben zentriert
    logo_bottom = H - 100  # Fallback
    try:
        drawing = _recolored_logo_drawing(farbe_hex)
        target = 95  # Logo etwas kleiner fuer mehr Platz
        scale = target / drawing.width
        drawing.width *= scale
        drawing.height *= scale
        drawing.scale(scale, scale)
        logo_x = (W - drawing.width) / 2
        logo_y = H - 70 - drawing.height
        renderPDF.draw(drawing, c, logo_x, logo_y)
        logo_bottom = logo_y
    except Exception as e:
        print(f"Warnung: Logo konnte nicht eingefuegt werden ({e})")

    # DOMVS APERTA Titel
    c.setFillColor(farbe)
    c.setFont("Times-Roman", 28)
    title_y = logo_bottom - 32
    c.drawCentredString(W / 2, title_y, "D O M V S   A P E R T A")

    # Untertitel
    c.setFillColor(text_gedaempft)
    c.setFont("Times-Italic", 9)
    c.drawCentredString(W / 2, title_y - 16, "Hospitality Check Verein  .  Bund der Gastlichkeit")

    # Zierlinien + Stern
    c.setStrokeColor(farbe)
    c.setLineWidth(0.5)
    line_y = title_y - 38
    c.line(W / 2 - 80, line_y, W / 2 - 18, line_y)
    c.line(W / 2 + 18, line_y, W / 2 + 80, line_y)
    c.setFillColor(farbe)
    c.setFont("Times-Roman", 12)
    c.drawCentredString(W / 2, line_y - 4, "*")

    # "Hiermit wird verliehen der Rang"
    c.setFillColor(text_hell)
    c.setFont("Times-Roman", 13)
    zert_y = line_y - 38
    c.drawCentredString(W / 2, zert_y, "Hiermit wird verliehen der Rang")

    # Stufe gross
    c.setFillColor(farbe)
    c.setFont("Times-Bold", 44)
    stufe_y = zert_y - 56
    c.drawCentredString(W / 2, stufe_y, stufe.upper())

    # Untertitel der Stufe
    c.setFillColor(text_hell)
    c.setFont("Times-Italic", 16)
    c.drawCentredString(W / 2, stufe_y - 26, info["titel"])

    # Motto der Stufe
    c.setFillColor(text_gedaempft)
    c.setFont("Times-Italic", 11)
    c.drawCentredString(W / 2, stufe_y - 45, f'"{info["motto"]}"')

    # "AN"
    c.setFillColor(text_gedaempft)
    c.setFont("Times-Roman", 9)
    an_y = stufe_y - 85
    c.drawCentredString(W / 2, an_y, "AN")

    # Name
    c.setFillColor(text_hell)
    c.setFont("Times-Bold", 24)
    name_y = an_y - 32
    c.drawCentredString(W / 2, name_y, name if name else "_____________________________")

    # Name-Linie
    c.setStrokeColor(text_gedaempft)
    c.setLineWidth(0.4)
    c.line(W / 2 - 150, name_y - 8, W / 2 + 150, name_y - 8)

    # "MIT DER GESAMTPUNKTZAHL"
    c.setFillColor(text_gedaempft)
    c.setFont("Times-Roman", 9)
    punkte_label_y = name_y - 40
    c.drawCentredString(W / 2, punkte_label_y, "MIT DER GESAMTPUNKTZAHL")

    # Punktzahl gross
    c.setFillColor(farbe)
    c.setFont("Times-Bold", 36)
    punkte_val_y = punkte_label_y - 40
    if punkte and punkte > 0:
        c.drawCentredString(W / 2, punkte_val_y, f"{punkte:.1f} / 105")
    else:
        c.drawCentredString(W / 2, punkte_val_y, "___ / 105")

    # Optionale Kategorie-Tabelle
    if kategorien:
        cat_label_y = punkte_val_y - 40
        cat_value_y = cat_label_y - 18
        spalten = [
            ("EMPFANG (20%)", kategorien.get("empfang", "-")),
            ("ESSEN (30%)", kategorien.get("essen", "-")),
            ("AUFMERKSAMKEIT (25%)", kategorien.get("aufmerksamkeit", "-")),
            ("WOW (25%)", kategorien.get("wow", "-")),
            ("BONUS", kategorien.get("bonus", "-")),
        ]
        col_w = (W - 2 * inner - 40) / len(spalten)
        start_x = inner + 20
        for i, (label, value) in enumerate(spalten):
            cx = start_x + i * col_w + col_w / 2
            c.setFillColor(text_gedaempft)
            c.setFont("Times-Roman", 7)
            c.drawCentredString(cx, cat_label_y, label)
            c.setFillColor(text_hell)
            c.setFont("Times-Roman", 13)
            c.drawCentredString(cx, cat_value_y, str(value))

    # -------------------------------------------------------------------
    # Unterer Bereich: feste Positionen vom unteren Rand
    # Reihenfolge von unten: Motto (55) -> Label (88) -> Name (100)
    #                        Signatur-Linie (115) -> Datum (200)
    # -------------------------------------------------------------------

    # Datum (deutlich ueber den Signaturen, damit Luft zum Unterschreiben bleibt)
    d_text = datum or date.today().strftime("%d. %B %Y")
    c.setFillColor(text_gedaempft)
    c.setFont("Times-Italic", 10)
    c.drawCentredString(W / 2, 200, f"Verliehen am  {d_text}")

    # Drei Signaturen: Gruendungsmitglieder nebeneinander
    gruender = [
        "Jérôme Zurbuchen",
        "Manuel Krattiger",
        "Livia Zahnd",
    ]
    # Zentren der drei Signatur-Blocks: links / mitte / rechts
    sig_centers = [W / 2 - 170, W / 2, W / 2 + 170]
    sig_half = 65  # halbe Linienlaenge

    c.setStrokeColor(text_gedaempft)
    c.setLineWidth(0.4)
    for cx, name_g in zip(sig_centers, gruender):
        # Signatur-Linie
        c.line(cx - sig_half, 115, cx + sig_half, 115)
        # Name des Gruendungsmitglieds
        c.setFillColor(text_hell)
        c.setFont("Times-Roman", 9)
        c.drawCentredString(cx, 103, name_g)
        # Label
        c.setFillColor(text_gedaempft)
        c.setFont("Times-Roman", 7)
        c.drawCentredString(cx, 91, "GRÜNDUNGSMITGLIED")

    # Motto am Fuss
    c.setFillColor(farbe)
    c.setFont("Times-Italic", 10)
    c.drawCentredString(W / 2, 55, "*  HOSPITALITAS  .  HONOR  .  GAUDIUM  *")

    c.save()


def generate_certificate_bytes(
    name: str,
    punkte: float,
    stufe: str,
    datum: str | None = None,
    kategorien: dict | None = None,
) -> bytes:
    """Wie generate_certificate(), liefert das PDF aber als bytes zurueck (fuer st.download_button)."""
    buf = io.BytesIO()
    generate_certificate(name, punkte, stufe, buf, datum=datum, kategorien=kategorien)
    return buf.getvalue()


def _punkte_aus_kategorien(k: dict) -> float:
    """Formel identisch zu app.berechne_gesamt."""
    return round(
        (k["empfang"] * 0.20 + k["essen"] * 0.30 + k["aufmerksamkeit"] * 0.25 + k["wow"] * 0.25) * 10
        + k.get("bonus", 0),
        1,
    )


def generate_all_examples() -> None:
    """Erstellt je 1 Beispiel + 1 Leervorlage pro Stufe im Ordner 'zertifikate'."""
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Kategorien so gewaehlt, dass die berechnete Punktzahl in der jeweiligen Stufe liegt.
    beispiele = {
        "Bronze": {"name": "Antonia Neumann",   "kategorien": {"empfang": 5, "essen": 5, "aufmerksamkeit": 6, "wow": 5, "bonus": 0}},   # 52.5
        "Silber": {"name": "Lukas Berger",      "kategorien": {"empfang": 7, "essen": 7, "aufmerksamkeit": 6, "wow": 7, "bonus": 0}},   # 68.5
        "Gold":   {"name": "Jerome Zurbuchen",  "kategorien": {"empfang": 8, "essen": 8, "aufmerksamkeit": 8, "wow": 8, "bonus": 2}},   # 82.0
        "Platin": {"name": "Familie Schneider", "kategorien": {"empfang": 10, "essen": 10, "aufmerksamkeit": 9, "wow": 9, "bonus": 1}}, # 95.5
    }

    for stufe, daten in beispiele.items():
        daten["punkte"] = _punkte_aus_kategorien(daten["kategorien"])
        # Beispiel
        generate_certificate(
            name=daten["name"],
            punkte=daten["punkte"],
            stufe=stufe,
            output=str(OUTPUT_DIR / f"Zertifikat_{stufe}_Beispiel.pdf"),
            datum="15. Maerz 2026",
            kategorien=daten["kategorien"],
        )
        # Leervorlage
        generate_certificate(
            name="",
            punkte=0,
            stufe=stufe,
            output=str(OUTPUT_DIR / f"Zertifikat_{stufe}_Vorlage.pdf"),
            datum="__. _____________ 2026",
        )
        print(f"Erzeugt: {stufe} (Beispiel + Vorlage)")


if __name__ == "__main__":
    generate_all_examples()
    print(f"\nAlle Zertifikate unter: {OUTPUT_DIR}")
