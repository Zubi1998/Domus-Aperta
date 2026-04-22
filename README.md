# Domus Aperta

Interne Streamlit-App des Bundes **Domus Aperta** zur Erfassung und Auswertung von Hospitality-Checks unter den Gründern.

*Hospitalitas  .  Honor  .  Gaudium*

---

## Was kann die App?

- **Rangliste**: Alle Gastgeber sortiert nach Durchschnittspunkten, inkl. Stufenkategorie (Bronze / Silber / Gold / Platin).
- **Check eintragen** (nur Grand Maître): Neue Bewertung mit vier Kategorien plus Bonus erfassen. Direkt danach kann das passende Zertifikat als PDF heruntergeladen werden.
- **Gastgeber verwalten** (nur Grand Maître): Neue Gastgeber anlegen.
- **Historie**: Alle erfassten Checks chronologisch, mit Filter nach Gastgeber.

Die App hat zwei Rollen, jeweils mit eigenem Passwort:

| Rolle | Fallback-Passwort | Zugriff |
|---|---|---|
| Mitglied | `Domus2026` | Rangliste + Historie |
| Grand Maître | `GLDomus2026` | Vollzugriff |

Produktiv werden die Passwörter über Streamlit-Secrets überschrieben — siehe `DEPLOYMENT.md`.

---

## Projektstruktur

```
.
├── app.py                      # Streamlit-App (UI, Auth, Tabs)
├── db.py                       # Datenbank-Abstraktion (Supabase ODER SQLite)
├── generate_certificates.py    # PDF-Zertifikate (Bronze/Silber/Gold/Platin)
├── requirements.txt            # Python-Abhängigkeiten
├── supabase_init.sql           # Einmalige Migration für Supabase
├── logo.svg                    # Logo (Gradient, für UI)
├── logo_pdf.svg                # Logo (Hex-Farbe, für PDFs)
├── Manifest_Domus_Aperta.docx  # Manifest für das Gründungstreffen
├── DEPLOYMENT.md               # Schritt-für-Schritt-Anleitung für Streamlit Cloud
└── README.md                   # Diese Datei
```

---

## Datenbank

Die App unterstützt zwei Backends und wählt automatisch:

- **Supabase (Cloud-Postgres)** — sobald `SUPABASE_URL` und `SUPABASE_KEY` in den Streamlit-Secrets stehen. Für den Produktivbetrieb.
- **SQLite (lokale Datei `domus.db`)** — Fallback für lokales Entwickeln ohne Secrets. Daten gehen auf Streamlit Cloud bei jedem Neustart verloren, also nur lokal nutzen.

In der Sidebar der App steht jeweils, welches Backend gerade aktiv ist.

---

## Lokal starten

```bash
pip install -r requirements.txt
streamlit run app.py
```

App öffnet sich auf <http://localhost:8501>.

Ohne Secrets nutzt die App automatisch SQLite (`domus.db` im Projektordner). Wenn du lokal gegen Supabase testen willst, leg `.streamlit/secrets.toml` mit `SUPABASE_URL` und `SUPABASE_KEY` an (ist in `.gitignore`).

---

## Deployen auf Streamlit Cloud

Komplette Anleitung in [`DEPLOYMENT.md`](DEPLOYMENT.md). Grobe Schritte:

1. Supabase-Projekt anlegen, `supabase_init.sql` im SQL Editor ausführen.
2. Repo auf <https://share.streamlit.io> verbinden, `app.py` als Main file.
3. Secrets eintragen (Passwörter + Supabase-URL + Anon-Key).
4. Fertig.

---

## Zertifikate lokal erzeugen

Wer die acht Beispiel- und Leervorlagen als PDFs generieren will:

```bash
python generate_certificates.py
```

Die App erzeugt Zertifikate ohnehin on-demand direkt nach jedem Check — das Script ist vor allem für Vorlagen gedacht.

---

*Nur für den internen Gebrauch des Bundes Domus Aperta.*
