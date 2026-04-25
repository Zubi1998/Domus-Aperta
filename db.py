"""
Datenbank-Abstraktion fuer Domus Aperta.

Waehlt automatisch zwischen Supabase und SQLite:
- Wenn SUPABASE_URL und SUPABASE_KEY in st.secrets gesetzt sind, wird Supabase verwendet.
- Sonst (z.B. lokal ohne Secrets) wird auf eine lokale SQLite-Datei zurueckgegriffen.

Alle CRUD-Funktionen haben dieselbe Signatur und Rueckgabeform, egal welches Backend aktiv ist.
"""

from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

_SQLITE_PATH = Path(__file__).parent / "domus.db"


# ---------------------------------------------------------------------------
# Backend-Auswahl
# ---------------------------------------------------------------------------

def _supabase_config() -> tuple[str, str] | None:
    """Liefert (url, key) aus Secrets, oder None wenn nicht konfiguriert."""
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except Exception:
        return None
    if not url or not key:
        return None
    return url, key


@st.cache_resource(show_spinner=False)
def _supabase_client():
    """Laedt den Supabase-Client (gecached)."""
    from supabase import create_client  # lazy import

    cfg = _supabase_config()
    if cfg is None:
        raise RuntimeError("Supabase nicht konfiguriert.")
    url, key = cfg
    return create_client(url, key)


def backend_name() -> str:
    """Gibt 'supabase' oder 'sqlite' zurueck."""
    return "supabase" if _supabase_config() else "sqlite"


def backend_label() -> str:
    """Fuer die Status-Anzeige in der App."""
    return "Supabase (Cloud)" if backend_name() == "supabase" else "SQLite (lokal)"


# ---------------------------------------------------------------------------
# SQLite-Helpers
# ---------------------------------------------------------------------------

def _sqlite_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _sqlite_init() -> None:
    with _sqlite_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS gastgeber (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                beschreibung TEXT,
                erstellt TEXT
            );

            CREATE TABLE IF NOT EXISTS checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gastgeber_id INTEGER NOT NULL,
                datum TEXT NOT NULL,
                bewerter TEXT NOT NULL,
                empfang INTEGER,
                essen INTEGER,
                aufmerksamkeit INTEGER,
                wow INTEGER,
                bonus INTEGER DEFAULT 0,
                kommentar TEXT,
                FOREIGN KEY (gastgeber_id) REFERENCES gastgeber(id)
            );
            """
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Initialisiert die Datenbank. Bei Supabase ein No-Op (Tabellen kommen via SQL-Migration).
    Bei SQLite werden die Tabellen angelegt, falls noch nicht vorhanden."""
    if backend_name() == "sqlite":
        _sqlite_init()


def gastgeber_liste() -> pd.DataFrame:
    """Alle Gastgeber, sortiert nach Name."""
    if backend_name() == "supabase":
        client = _supabase_client()
        resp = client.table("gastgeber").select("*").order("name").execute()
        df = pd.DataFrame(resp.data or [])
        if df.empty:
            return pd.DataFrame(columns=["id", "name", "beschreibung", "erstellt"])
        # Nur die vier Standardspalten und in der erwarteten Reihenfolge
        return df[["id", "name", "beschreibung", "erstellt"]]
    else:
        with _sqlite_conn() as conn:
            return pd.read_sql_query(
                "SELECT id, name, beschreibung, erstellt FROM gastgeber ORDER BY name",
                conn,
            )


def gastgeber_hinzufuegen(name: str, beschreibung: str) -> None:
    """Fuegt einen Gastgeber hinzu. Wirft ValueError bei Duplikat."""
    n = name.strip()
    b = beschreibung.strip()
    if not n:
        raise ValueError("Name darf nicht leer sein.")
    if backend_name() == "supabase":
        client = _supabase_client()
        try:
            client.table("gastgeber").insert({"name": n, "beschreibung": b}).execute()
        except Exception as exc:
            msg = str(exc)
            if "duplicate" in msg.lower() or "23505" in msg:
                raise ValueError("Dieser Name existiert bereits.") from exc
            raise
    else:
        try:
            with _sqlite_conn() as conn:
                conn.execute(
                    "INSERT INTO gastgeber (name, beschreibung, erstellt) VALUES (?, ?, ?)",
                    (n, b, date.today().isoformat()),
                )
        except sqlite3.IntegrityError as exc:
            raise ValueError("Dieser Name existiert bereits.") from exc


def check_hinzufuegen(daten: dict) -> None:
    """Speichert einen Check. Erwartet die Felder gastgeber_id, datum, bewerter,
    empfang, essen, aufmerksamkeit, wow, bonus, kommentar."""
    payload: dict[str, Any] = {
        "gastgeber_id": int(daten["gastgeber_id"]),
        "datum": daten["datum"],
        "bewerter": daten["bewerter"],
        "empfang": int(daten["empfang"]),
        "essen": int(daten["essen"]),
        "aufmerksamkeit": int(daten["aufmerksamkeit"]),
        "wow": int(daten["wow"]),
        "bonus": int(daten["bonus"]),
        "kommentar": daten.get("kommentar", "") or "",
    }
    if backend_name() == "supabase":
        client = _supabase_client()
        client.table("checks").insert(payload).execute()
    else:
        with _sqlite_conn() as conn:
            conn.execute(
                """
                INSERT INTO checks
                (gastgeber_id, datum, bewerter, empfang, essen, aufmerksamkeit, wow, bonus, kommentar)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["gastgeber_id"],
                    payload["datum"],
                    payload["bewerter"],
                    payload["empfang"],
                    payload["essen"],
                    payload["aufmerksamkeit"],
                    payload["wow"],
                    payload["bonus"],
                    payload["kommentar"],
                ),
            )


def check_aktualisieren(check_id: int, daten: dict) -> None:
    """Aktualisiert einen bestehenden Check. Felder wie bei check_hinzufuegen
    (ohne gastgeber_id - der Gastgeber bleibt unveraendert)."""
    payload: dict[str, Any] = {
        "datum": daten["datum"],
        "bewerter": daten["bewerter"],
        "empfang": int(daten["empfang"]),
        "essen": int(daten["essen"]),
        "aufmerksamkeit": int(daten["aufmerksamkeit"]),
        "wow": int(daten["wow"]),
        "bonus": int(daten["bonus"]),
        "kommentar": daten.get("kommentar", "") or "",
    }
    if backend_name() == "supabase":
        client = _supabase_client()
        client.table("checks").update(payload).eq("id", int(check_id)).execute()
    else:
        with _sqlite_conn() as conn:
            conn.execute(
                """
                UPDATE checks
                   SET datum = ?, bewerter = ?, empfang = ?, essen = ?,
                       aufmerksamkeit = ?, wow = ?, bonus = ?, kommentar = ?
                 WHERE id = ?
                """,
                (
                    payload["datum"],
                    payload["bewerter"],
                    payload["empfang"],
                    payload["essen"],
                    payload["aufmerksamkeit"],
                    payload["wow"],
                    payload["bonus"],
                    payload["kommentar"],
                    int(check_id),
                ),
            )


def check_loeschen(check_id: int) -> None:
    """Loescht einen Check anhand seiner ID.
    Wirft RuntimeError, wenn die Loeschung stillschweigend fehlschlaegt
    (z.B. wegen Supabase Row Level Security)."""
    cid = int(check_id)
    if backend_name() == "supabase":
        client = _supabase_client()
        resp = client.table("checks").delete().eq("id", cid).execute()
        if not resp.data:
            raise RuntimeError(
                "Check wurde nicht gelöscht. Möglicherweise verhindert eine "
                "Supabase Row-Level-Security-Policy den DELETE-Vorgang. "
                "Prüfe in Supabase unter Authentication > Policies, ob für "
                "die Tabelle 'checks' eine DELETE-Policy existiert."
            )
    else:
        with _sqlite_conn() as conn:
            cur = conn.execute("DELETE FROM checks WHERE id = ?", (cid,))
            if cur.rowcount == 0:
                raise RuntimeError(f"Kein Check mit ID {cid} gefunden.")


def gastgeber_loeschen(gastgeber_id: int) -> None:
    """Loescht einen Gastgeber. Wirft ValueError, wenn noch Checks dafuer existieren."""
    gid = int(gastgeber_id)
    if backend_name() == "supabase":
        client = _supabase_client()
        resp = (
            client.table("checks")
            .select("id")
            .eq("gastgeber_id", gid)
            .limit(1)
            .execute()
        )
        if resp.data:
            raise ValueError(
                "Dieser Gastgeber hat noch Checks. Bitte zuerst die Checks löschen."
            )
        del_resp = client.table("gastgeber").delete().eq("id", gid).execute()
        if not del_resp.data:
            raise RuntimeError(
                "Gastgeber wurde nicht gelöscht. Möglicherweise verhindert eine "
                "Supabase Row-Level-Security-Policy den DELETE-Vorgang."
            )
    else:
        with _sqlite_conn() as conn:
            cur = conn.execute(
                "SELECT COUNT(*) FROM checks WHERE gastgeber_id = ?",
                (gid,),
            )
            anzahl = cur.fetchone()[0]
            if anzahl > 0:
                raise ValueError(
                    f"Dieser Gastgeber hat noch {anzahl} Check(s). Bitte zuerst die Checks löschen."
                )
            cur = conn.execute("DELETE FROM gastgeber WHERE id = ?", (gid,))
            if cur.rowcount == 0:
                raise RuntimeError(f"Kein Gastgeber mit ID {gid} gefunden.")


def checks_raw() -> pd.DataFrame:
    """Alle Checks inkl. Gastgebername, sortiert nach Datum absteigend.
    Ohne berechnete Punktzahl (die erledigt app.py)."""
    cols = [
        "id", "datum", "bewerter", "gastgeber", "empfang", "essen",
        "aufmerksamkeit", "wow", "bonus", "kommentar", "gastgeber_id",
    ]
    if backend_name() == "supabase":
        client = _supabase_client()
        # Zwei separate Queries und Join in Python:
        # robuster als PostgREST-Embedding (umgeht PGRST125).
        checks_resp = (
            client.table("checks")
            .select("id, datum, bewerter, empfang, essen, aufmerksamkeit, wow, bonus, kommentar, gastgeber_id")
            .order("datum", desc=True)
            .order("id", desc=True)
            .execute()
        )
        rows = checks_resp.data or []
        if not rows:
            return pd.DataFrame(columns=cols)
        gg_resp = client.table("gastgeber").select("id, name").execute()
        gg_map = {g["id"]: g["name"] for g in (gg_resp.data or [])}
        for r in rows:
            r["gastgeber"] = gg_map.get(r.get("gastgeber_id"), "?")
        df = pd.DataFrame(rows)
        return df[cols]
    else:
        query = """
            SELECT
                c.id,
                c.datum,
                c.bewerter,
                g.name AS gastgeber,
                c.empfang,
                c.essen,
                c.aufmerksamkeit,
                c.wow,
                c.bonus,
                c.kommentar,
                g.id AS gastgeber_id
            FROM checks c
            JOIN gastgeber g ON g.id = c.gastgeber_id
            ORDER BY c.datum DESC, c.id DESC
        """
        with _sqlite_conn() as conn:
            return pd.read_sql_query(query, conn)
