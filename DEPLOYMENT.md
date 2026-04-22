# Deployment-Anleitung - Domus Aperta

Diese Anleitung beschreibt, wie du die Streamlit-App kostenlos auf der **Streamlit Community Cloud** deployst, damit sie unter einer öffentlichen URL erreichbar ist.

---

## Voraussetzungen

- Ein **GitHub-Konto** (gratis) - <https://github.com/signup>
- Ein **Streamlit-Konto** (gratis, via GitHub-Login) - <https://share.streamlit.io>
- Lokal installiert: `git` (und optional `python` zum Testen)

---

## Schritt 1 - Lokal testen

Bevor du deployst, stelle sicher, dass die App lokal läuft.

```bash
cd "Verein Domus Apera"
pip install -r requirements.txt
streamlit run app.py
```

Die App öffnet sich auf <http://localhost:8501>. Passwort (Fallback): `domus2026`.

Wenn alles läuft, weiter mit Schritt 2.

---

## Schritt 2 - GitHub-Repo anlegen

1. Einloggen auf <https://github.com> und oben rechts auf **+ → New repository** klicken.
2. Felder ausfüllen:
   - **Repository name**: `domus-aperta` (oder frei wählbar)
   - **Visibility**: *Private* (empfohlen, da der App-Passwort-Fallback im Code steht)
   - **Initialize**: *nicht* ankreuzen (wir pushen eigene Dateien)
3. **Create repository** klicken.

GitHub zeigt dir nun Befehle zum Hochladen. Merk dir die HTTPS-URL, z.B.:
`https://github.com/DEIN_USERNAME/domus-aperta.git`

---

## Schritt 3 - Dateien pushen

Im Projektordner (`Verein Domus Apera/`) in der Konsole:

```bash
git init
git add app.py requirements.txt .gitignore logo.svg logo_pdf.svg generate_certificates.py DEPLOYMENT.md
git commit -m "Initial commit - Domus Aperta"
git branch -M main
git remote add origin https://github.com/DEIN_USERNAME/domus-aperta.git
git push -u origin main
```

**Wichtig:** Die Datei `domus.db` (SQLite) sollte **nicht** ins Repo - sie ist bereits in `.gitignore`. Dadurch wird bei jedem App-Neustart eine frische DB erzeugt (siehe Schritt 6).

---

## Schritt 4 - Streamlit Cloud verbinden

1. Einloggen auf <https://share.streamlit.io> (mit GitHub).
2. **New app** klicken.
3. Repository auswählen: `DEIN_USERNAME/domus-aperta`.
4. **Branch**: `main`
5. **Main file path**: `app.py`
6. **App URL**: frei wählbar, z.B. `domus-aperta.streamlit.app`
7. **Deploy** klicken.

Die App wird gebaut (dauert ca. 1-2 Minuten) und ist danach unter deiner Wunsch-URL erreichbar.

---

## Schritt 5 - Passwörter als Secrets setzen

Die App hat zwei Rollen mit je einem Passwort:

- **Mitglied** (`Domus2026` als Fallback) - sieht nur Rangliste und Historie
- **Grand Maître** (`GLDomus2026` als Fallback) - hat Vollzugriff, kann Checks erfassen und Zertifikate herunterladen

Damit die Passwörter nicht im Code stehen, hinterlege sie als Secrets:

1. In der Streamlit-Cloud-Ansicht deiner App: **⋮ (Drei Punkte) → Settings → Secrets**.
2. Folgenden Inhalt eintragen:

```toml
APP_PASSWORD_GUEST = "dein-mitglieder-passwort"
APP_PASSWORD_ADMIN = "dein-grand-maitre-passwort"
```

3. **Save** klicken. Die App startet automatisch neu und nutzt die neuen Passwörter.

Die Fallbacks (`Domus2026` / `GLDomus2026`) greifen nur lokal bzw. wenn keine Secrets gesetzt sind.

---

## Schritt 6 - Supabase als Datenbank (empfohlen)

Die App unterstützt **zwei Backends**:

- **Supabase** (Postgres, Cloud) - Daten bleiben dauerhaft erhalten, auch nach App-Neustart. Empfohlen für den Produktiv-Betrieb.
- **SQLite** (lokale Datei) - Fallback, wird nur verwendet, wenn keine Supabase-Credentials in den Secrets stehen. Auf Streamlit Cloud **gehen diese Daten bei jedem Neustart verloren** - also nur für lokales Entwickeln geeignet.

### 6.1 Supabase-Projekt anlegen

1. Auf <https://supabase.com> einloggen und ein neues Projekt erstellen (Free-Tier reicht).
2. Sobald das Projekt bereit ist, im linken Menü auf **SQL Editor → New query** gehen.
3. Den Inhalt der Datei `supabase_init.sql` (im Projektordner) kopieren und ausführen.
   Das legt die Tabellen `gastgeber` und `checks` an, inklusive Row-Level-Security und Policies.
4. Danach unter **Settings → API** zwei Werte notieren:
   - **Project URL** (z.B. `https://deinprojekt.supabase.co`)
   - **Publishable anon key** (bzw. `anon public` Key)

### 6.2 Secrets in Streamlit Cloud ergänzen

In **⋮ → Settings → Secrets** die bestehende `secrets.toml` um die folgenden Zeilen erweitern:

```toml
APP_PASSWORD_GUEST = "dein-mitglieder-passwort"
APP_PASSWORD_ADMIN = "dein-grand-maitre-passwort"

SUPABASE_URL = "https://deinprojekt.supabase.co"
SUPABASE_KEY = "dein-anon-key"
```

Nach dem Speichern startet die App automatisch neu. In der Sidebar sollte danach **„DATENBANK: Supabase (Cloud)"** stehen.

### 6.3 Lokal mit Supabase testen (optional)

Wenn du lokal gegen Supabase testen willst, lege die Datei `.streamlit/secrets.toml` im Projektordner an (die Datei ist in `.gitignore` und kommt **nicht** ins GitHub-Repo):

```toml
SUPABASE_URL = "https://deinprojekt.supabase.co"
SUPABASE_KEY = "dein-anon-key"
```

Ohne diese Datei nutzt die App automatisch SQLite (`domus.db`).

---

## Updates pushen

Änderungen an der App:

```bash
git add .
git commit -m "Kurze Beschreibung"
git push
```

Streamlit Cloud erkennt den Push automatisch und redeployt (~30 Sekunden).

---

## Häufige Probleme

**App startet nicht - ModuleNotFoundError**
→ Paket fehlt in `requirements.txt`. Ergänzen und pushen.

**Logo wird nicht angezeigt**
→ `logo.svg` ist nicht im Repo. Mit `git add logo.svg && git commit && git push` nachreichen.

**Passwort falsch, obwohl korrekt eingegeben**
→ Im Secrets-Editor prüfen, ob Zeichen (z.B. Anführungszeichen) korrekt gesetzt sind.

**App läuft langsam**
→ Community Cloud hat limitierte Ressourcen. Bei vielen Gastgebern/Checks auf ein bezahltes Hosting oder eigenen Server umziehen.

---

## Nächste Schritte nach Deployment

1. URL an die drei Gründer schicken.
2. Erste Gastgeber und Bewerter in der App anlegen.
3. Ersten Check eintragen - fertig.
4. Manifest (`Manifest_Domus_Aperta.docx`) am Gründungstreffen ausdrucken und unterschreiben lassen.
5. Zertifikat-Generator (`generate_certificates.py`) lokal laufen lassen, wenn ein Gastgeber ausgezeichnet werden soll.

---

*Hospitalitas  .  Honor  .  Gaudium*
