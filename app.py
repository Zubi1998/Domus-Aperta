"""
Domus Aperta - Hospitality Check Verein
Streamlit-Anwendung fuer Bewertungen im Freundeskreis.
"""

import base64
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from generate_certificates import generate_certificate_bytes
import db  # Datenbank-Abstraktion: waehlt Supabase oder SQLite anhand der Secrets

# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------

LOGO_PATH = Path(__file__).parent / "logo.svg"

GEWICHTE = {
    "empfang": 0.20,
    "essen": 0.30,
    "aufmerksamkeit": 0.25,
    "wow": 0.25,
}

STUFEN = [
    (90, 105, "Platin",  "Grossmeister der Gastlichkeit", "Unerreichte Vollkommenheit", "#E5E4E2"),
    (75, 89,  "Gold",    "Meister der Gastlichkeit",      "Vorzueglich in Allem",        "#D4AF37"),
    (60, 74,  "Silber",  "Gesandter der Gastlichkeit",    "Ehrenvoll im Empfang",        "#A8A8A8"),
    (40, 59,  "Bronze",  "Aspirant der Gastlichkeit",     "Erste Schritte im Bund",      "#8B5A2B"),
]

# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def get_passwords() -> dict:
    """Gibt ein dict mit Passwoertern je Rolle zurueck.
    'gast'  -> Rangliste + Historie (nur Lesen)
    'admin' -> Vollzugriff inkl. Checks erfassen und Gastgeber verwalten
    """
    try:
        gast = st.secrets["APP_PASSWORD_GUEST"]
    except Exception:
        gast = "Domus2026"
    try:
        admin = st.secrets["APP_PASSWORD_ADMIN"]
    except Exception:
        admin = "GLDomus2026"
    return {"gast": gast, "admin": admin}


def authenticate(pwd: str) -> str | None:
    """Gibt 'gast', 'admin' oder None zurueck."""
    pw = get_passwords()
    if pwd == pw["admin"]:
        return "admin"
    if pwd == pw["gast"]:
        return "gast"
    return None


def load_logo_base64() -> str:
    if not LOGO_PATH.exists():
        return ""
    data = LOGO_PATH.read_bytes()
    return base64.b64encode(data).decode("utf-8")


def berechne_gesamt(empfang: int, essen: int, aufmerksamkeit: int, wow: int, bonus: int) -> float:
    rohwert = (
        empfang * GEWICHTE["empfang"]
        + essen * GEWICHTE["essen"]
        + aufmerksamkeit * GEWICHTE["aufmerksamkeit"]
        + wow * GEWICHTE["wow"]
    ) * 10
    return round(rohwert + bonus, 1)


def stufe_fuer_punkte(punkte: float) -> dict:
    for low, high, name, titel, motto, farbe in STUFEN:
        if low <= punkte <= high:
            return {"name": name, "titel": titel, "motto": motto, "farbe": farbe}
    return {"name": "-", "titel": "Noch kein Rang", "motto": "Weiter so", "farbe": "#555555"}


# ---------------------------------------------------------------------------
# Datenbank-Wrapper (nutzt db.py; Supabase oder SQLite je nach Secrets)
# ---------------------------------------------------------------------------

def init_db() -> None:
    db.init_db()


def gastgeber_liste() -> pd.DataFrame:
    return db.gastgeber_liste()


def gastgeber_hinzufuegen(name: str, beschreibung: str) -> None:
    db.gastgeber_hinzufuegen(name, beschreibung)


def check_hinzufuegen(daten: dict) -> None:
    db.check_hinzufuegen(daten)


def checks_mit_punkten() -> pd.DataFrame:
    df = db.checks_raw()
    if df.empty:
        return df
    # Datum als ISO-String normalisieren (Supabase liefert datetime, SQLite liefert str)
    df["datum"] = df["datum"].astype(str).str.slice(0, 10)
    df["gesamt"] = df.apply(
        lambda r: berechne_gesamt(r.empfang, r.essen, r.aufmerksamkeit, r.wow, r.bonus),
        axis=1,
    )
    df["stufe"] = df["gesamt"].apply(lambda p: stufe_fuer_punkte(p)["name"])
    return df


def rangliste() -> pd.DataFrame:
    df = checks_mit_punkten()
    if df.empty:
        return df
    rang = (
        df.groupby(["gastgeber_id", "gastgeber"], as_index=False)
        .agg(
            anzahl_checks=("id", "count"),
            durchschnitt=("gesamt", "mean"),
            bestes=("gesamt", "max"),
            letzter_check=("datum", "max"),
        )
        .sort_values("durchschnitt", ascending=False)
    )
    rang["durchschnitt"] = rang["durchschnitt"].round(1)
    rang["aktuelle_stufe"] = rang["durchschnitt"].apply(lambda p: stufe_fuer_punkte(p)["name"])
    return rang.reset_index(drop=True)


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --gold: #D4AF37;
            --gold-dark: #9A7817;
            --bg: #0F0F0F;
            --card: #1A1A1A;
        }
        .stApp {
            background-color: var(--bg);
            color: #EDEDED;
            font-family: Georgia, 'Cormorant Garamond', serif;
        }
        h1, h2, h3, h4 {
            color: var(--gold);
            font-family: 'Cormorant Garamond', Georgia, serif;
            letter-spacing: 2px;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 1.5rem;
            border-bottom: 1px solid var(--gold-dark);
        }
        .stTabs [data-baseweb="tab"] {
            color: #CCCCCC;
            background-color: transparent;
            letter-spacing: 2px;
        }
        .stTabs [aria-selected="true"] {
            color: var(--gold) !important;
            border-bottom: 2px solid var(--gold);
        }
        .stButton > button {
            background-color: transparent;
            color: var(--gold);
            border: 1px solid var(--gold);
            letter-spacing: 3px;
            padding: 0.5rem 1.5rem;
        }
        .stButton > button:hover {
            background-color: var(--gold);
            color: #0F0F0F;
            border: 1px solid var(--gold);
        }
        .domus-card {
            background-color: var(--card);
            border: 1px solid #333;
            border-radius: 8px;
            padding: 1.2rem 1.5rem;
            margin-bottom: 1rem;
        }
        .domus-score {
            font-size: 2.4rem;
            color: var(--gold);
            letter-spacing: 4px;
            font-family: 'Cormorant Garamond', Georgia, serif;
        }
        .domus-motto {
            text-align: center;
            color: var(--gold);
            letter-spacing: 6px;
            font-size: 0.85rem;
            margin-top: 2rem;
            opacity: 0.8;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def header() -> None:
    logo_b64 = load_logo_base64()
    if logo_b64:
        st.markdown(
            f"""
            <div style="text-align:center; padding-top: 0.5rem;">
                <img src="data:image/svg+xml;base64,{logo_b64}" width="120"/>
                <h1 style="letter-spacing: 12px; margin-top: 0.6rem; margin-bottom: 0;">DOMVS APERTA</h1>
                <div style="color:#888; letter-spacing: 6px; font-size: 0.75rem;">
                    HOSPITALITY CHECK &middot; MMXXVI
                </div>
            </div>
            <hr style="border:none; border-top: 1px solid #333; margin: 1.5rem 0;"/>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.title("Domus Aperta")


def footer() -> None:
    st.markdown(
        '<div class="domus-motto">&#x2726; HOSPITALITAS &middot; HONOR &middot; GAUDIUM &#x2726;</div>',
        unsafe_allow_html=True,
    )


def login_view() -> bool:
    inject_css()
    header()
    st.markdown("#### Zutritt")
    pwd = st.text_input("Passwort", type="password", label_visibility="collapsed", placeholder="Passwort")
    col1, _ = st.columns([1, 3])
    with col1:
        if st.button("EINTRETEN"):
            rolle = authenticate(pwd)
            if rolle:
                st.session_state["role"] = rolle
                st.rerun()
            else:
                st.error("Falsches Passwort.")
    st.markdown(
        '<div style="color:#666; font-size:0.8rem; margin-top:1rem; letter-spacing:2px;">'
        'Mitglieder-Passwort: Rangliste &amp; Historie &nbsp;&nbsp;|&nbsp;&nbsp; '
        'Grand-Ma&icirc;tre-Passwort: Vollzugriff'
        '</div>',
        unsafe_allow_html=True,
    )
    footer()
    return bool(st.session_state.get("role"))


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

def tab_rangliste() -> None:
    st.markdown("### Rangliste")
    rang = rangliste()
    if rang.empty:
        st.info("Noch keine Checks erfasst. Gehe zum Tab 'Check eintragen'.")
        return

    anzeige = rang.rename(
        columns={
            "gastgeber": "Gastgeber",
            "anzahl_checks": "Checks",
            "durchschnitt": "&Oslash; Punkte",
            "bestes": "Bestwert",
            "letzter_check": "Letzter Check",
            "aktuelle_stufe": "Stufe",
        }
    )[["Gastgeber", "Checks", "&Oslash; Punkte", "Bestwert", "Letzter Check", "Stufe"]]
    anzeige.index = anzeige.index + 1
    st.dataframe(anzeige, use_container_width=True)


def _datum_deutsch(d: date) -> str:
    """Formatiert ein Datum auf Deutsch, z.B. '15. Maerz 2026'."""
    monate = [
        "Januar", "Februar", "Maerz", "April", "Mai", "Juni",
        "Juli", "August", "September", "Oktober", "November", "Dezember",
    ]
    return f"{d.day}. {monate[d.month - 1]} {d.year}"


def _zertifikat_download_block(gastgeber_name: str, punkte: float, stufe_name: str,
                               datum: date, kategorien: dict, key_suffix: str) -> None:
    """Rendert einen Zertifikats-Download-Button unterhalb eines gespeicherten Checks.
    Wird nur angezeigt, wenn die Punktzahl in einer Stufe (>=40) liegt."""
    if punkte < 40:
        st.info(
            f"Die Punktzahl {punkte} liegt unter der Bronze-Schwelle (40). "
            "Fuer diesen Check wird kein Zertifikat ausgestellt."
        )
        return

    # URL + Gast-Passwort fuer den QR-Code auf dem Zertifikat
    try:
        app_url = st.secrets.get("APP_URL", "https://domus-aperta.streamlit.app/")
    except Exception:
        app_url = "https://domus-aperta.streamlit.app/"
    gast_passwort = get_passwords()["gast"]

    try:
        pdf_bytes = generate_certificate_bytes(
            name=gastgeber_name,
            punkte=punkte,
            stufe=stufe_name,
            datum=_datum_deutsch(datum),
            kategorien=kategorien,
            app_url=app_url,
            gast_passwort=gast_passwort,
        )
        safe_name = "".join(c for c in gastgeber_name if c.isalnum() or c in " _-").strip().replace(" ", "_")
        filename = f"Zertifikat_{stufe_name}_{safe_name or 'Gastgeber'}.pdf"
        st.download_button(
            label=f"ZERTIFIKAT {stufe_name.upper()} HERUNTERLADEN",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            key=f"dl_{key_suffix}",
        )
    except Exception as exc:
        st.error(f"Zertifikat konnte nicht erzeugt werden: {exc}")


def tab_check_eintragen() -> None:
    st.markdown("### Check eintragen")
    gg = gastgeber_liste()
    if gg.empty:
        st.warning("Zuerst mindestens einen Gastgeber im Tab 'Gastgeber' anlegen.")
        return

    with st.form("check_form", clear_on_submit=False):
        col_a, col_b = st.columns(2)
        with col_a:
            gg_name = st.selectbox("Gastgeber", gg["name"].tolist())
            datum = st.date_input("Datum", value=date.today())
        with col_b:
            bewerter = st.text_input("Bewerter", placeholder="Dein Name")
            kommentar = st.text_area("Kommentar", height=80)

        st.markdown("---")
        st.markdown("#### Bewertung (1-10 pro Kategorie)")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            empfang = st.slider("Empfang & Begruessung (20%)", 1, 10, 7)
        with c2:
            essen = st.slider("Essen & Getraenke (30%)", 1, 10, 7)
        with c3:
            aufmerksamkeit = st.slider("Aufmerksamkeit (25%)", 1, 10, 7)
        with c4:
            wow = st.slider("Wow-Faktor (25%)", 1, 10, 7)

        bonus = st.slider("Bonus / Malus", -5, 5, 0)

        # Live-Vorschau
        punkte = berechne_gesamt(empfang, essen, aufmerksamkeit, wow, bonus)
        stufe = stufe_fuer_punkte(punkte)

        st.markdown(
            f"""
            <div class="domus-card" style="text-align:center;">
                <div style="color:#999; letter-spacing: 4px; font-size: 0.8rem;">VORSCHAU</div>
                <div class="domus-score">{punkte} / 105</div>
                <div style="color:{stufe['farbe']}; letter-spacing: 4px; margin-top: 0.4rem;">
                    {stufe['name'].upper()} &middot; {stufe['titel']}
                </div>
                <div style="color:#888; font-style: italic; margin-top: 0.3rem;">
                    {stufe['motto']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        submitted = st.form_submit_button("CHECK SPEICHERN")

    if submitted:
        if not bewerter.strip():
            st.error("Bitte Bewerter eintragen.")
            return
        gg_id = int(gg.loc[gg["name"] == gg_name, "id"].iloc[0])
        check_hinzufuegen({
            "gastgeber_id": gg_id,
            "datum": datum.isoformat(),
            "bewerter": bewerter.strip(),
            "empfang": empfang,
            "essen": essen,
            "aufmerksamkeit": aufmerksamkeit,
            "wow": wow,
            "bonus": bonus,
            "kommentar": kommentar.strip(),
        })
        # Merke fuer Zertifikats-Download (ueberlebt bis Tab gewechselt wird)
        st.session_state["last_check"] = {
            "gastgeber": gg_name,
            "punkte": punkte,
            "stufe": stufe["name"],
            "datum": datum.isoformat(),
            "kategorien": {
                "empfang": empfang,
                "essen": essen,
                "aufmerksamkeit": aufmerksamkeit,
                "wow": wow,
                "bonus": bonus,
            },
        }

    # Zertifikats-Block nach erfolgtem Speichern
    last = st.session_state.get("last_check")
    if last:
        st.success(
            f"Check gespeichert: {last['gastgeber']} - {last['punkte']} Punkte ({last['stufe']})."
        )
        st.markdown("##### Zertifikat")
        _zertifikat_download_block(
            gastgeber_name=last["gastgeber"],
            punkte=last["punkte"],
            stufe_name=last["stufe"],
            datum=date.fromisoformat(last["datum"]),
            kategorien=last["kategorien"],
            key_suffix="lastcheck",
        )


def tab_gastgeber() -> None:
    st.markdown("### Gastgeber verwalten")

    with st.form("gg_form", clear_on_submit=True):
        name = st.text_input("Name")
        beschreibung = st.text_area("Beschreibung", height=80)
        if st.form_submit_button("HINZUFUEGEN"):
            if not name.strip():
                st.error("Name darf nicht leer sein.")
            else:
                try:
                    gastgeber_hinzufuegen(name, beschreibung)
                    st.success(f"Gastgeber '{name}' hinzugefuegt.")
                except ValueError as exc:
                    st.error(str(exc))
                except Exception as exc:
                    st.error(f"Fehler beim Speichern: {exc}")

    st.markdown("---")
    gg = gastgeber_liste()
    if gg.empty:
        st.info("Noch keine Gastgeber.")
    else:
        st.dataframe(
            gg.rename(columns={"name": "Name", "beschreibung": "Beschreibung", "erstellt": "Erstellt"})[
                ["Name", "Beschreibung", "Erstellt"]
            ],
            use_container_width=True,
        )


def tab_historie(is_admin: bool = False) -> None:
    st.markdown("### Historie aller Checks")
    df = checks_mit_punkten()
    if df.empty:
        st.info("Noch keine Checks vorhanden.")
        return

    # Filter
    gastgeber_opt = ["Alle"] + sorted(df["gastgeber"].unique().tolist())
    gg_filter = st.selectbox("Gastgeber filtern", gastgeber_opt)
    if gg_filter != "Alle":
        df = df[df["gastgeber"] == gg_filter]

    for _, row in df.iterrows():
        stufe = stufe_fuer_punkte(row.gesamt)
        st.markdown(
            f"""
            <div class="domus-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div style="font-size: 1.2rem; color: var(--gold); letter-spacing: 3px;">
                            {row.gastgeber}
                        </div>
                        <div style="color:#888; font-size: 0.85rem;">
                            {row.datum} &middot; Bewerter: {row.bewerter}
                        </div>
                    </div>
                    <div style="text-align:right;">
                        <div class="domus-score">{row.gesamt}</div>
                        <div style="color:{stufe['farbe']}; letter-spacing: 3px; font-size: 0.8rem;">
                            {stufe['name'].upper()}
                        </div>
                    </div>
                </div>
                <hr style="border:none; border-top: 1px solid #333; margin: 0.8rem 0;"/>
                <div style="display:grid; grid-template-columns: repeat(5, 1fr); gap: 0.8rem; font-size: 0.85rem;">
                    <div><span style="color:#888;">Empfang</span><br/>{row.empfang} / 10</div>
                    <div><span style="color:#888;">Essen</span><br/>{row.essen} / 10</div>
                    <div><span style="color:#888;">Aufmerksamkeit</span><br/>{row.aufmerksamkeit} / 10</div>
                    <div><span style="color:#888;">Wow</span><br/>{row.wow} / 10</div>
                    <div><span style="color:#888;">Bonus</span><br/>{row.bonus:+d}</div>
                </div>
                {"<div style='margin-top: 0.8rem; color:#CCC; font-style: italic;'>&laquo; " + row.kommentar + " &raquo;</div>" if row.kommentar else ""}
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Zertifikats-Download (nur fuer Admin)
        if is_admin and row.gesamt >= 40:
            with st.expander(f"Zertifikat fuer {row.gastgeber} ({stufe['name']}) erstellen"):
                _zertifikat_download_block(
                    gastgeber_name=row.gastgeber,
                    punkte=float(row.gesamt),
                    stufe_name=stufe["name"],
                    datum=date.fromisoformat(row.datum),
                    kategorien={
                        "empfang": int(row.empfang),
                        "essen": int(row.essen),
                        "aufmerksamkeit": int(row.aufmerksamkeit),
                        "wow": int(row.wow),
                        "bonus": int(row.bonus),
                    },
                    key_suffix=f"hist_{row.id}",
                )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def sidebar_logout(rolle: str) -> None:
    """Status-Anzeige und Logout-Button in der Sidebar."""
    with st.sidebar:
        rolle_label = "GRAND MAITRE" if rolle == "admin" else "MITGLIED"
        st.markdown(
            f'<div style="color:#D4AF37; letter-spacing:3px; font-size:0.85rem;">'
            f'ANGEMELDET ALS'
            f'</div>'
            f'<div style="color:#EDEDED; letter-spacing:2px; margin-bottom:1rem;">'
            f'{rolle_label}'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button("ABMELDEN"):
            st.session_state.clear()
            st.rerun()

        st.markdown(
            f'<div style="color:#666; font-size:0.75rem; letter-spacing:2px; margin-top:2rem;">'
            f'DATENBANK<br/>'
            f'<span style="color:#888;">{db.backend_label()}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )


def main() -> None:
    st.set_page_config(
        page_title="Domus Aperta",
        page_icon="&#x2726;",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    init_db()

    rolle = st.session_state.get("role")
    if not rolle:
        login_view()
        return

    inject_css()
    header()
    sidebar_logout(rolle)

    if rolle == "admin":
        tab_r, tab_c, tab_g, tab_h = st.tabs(
            ["RANGLISTE", "CHECK EINTRAGEN", "GASTGEBER", "HISTORIE"]
        )
        with tab_r:
            tab_rangliste()
        with tab_c:
            tab_check_eintragen()
        with tab_g:
            tab_gastgeber()
        with tab_h:
            tab_historie(is_admin=True)
    else:
        # Gast: nur Rangliste + Historie
        tab_r, tab_h = st.tabs(["RANGLISTE", "HISTORIE"])
        with tab_r:
            tab_rangliste()
        with tab_h:
            tab_historie(is_admin=False)

    footer()


if __name__ == "__main__":
    main()
