"""Formatage francophone, palette de couleurs et feuille de style de l'application."""

from __future__ import annotations

import html
from typing import Any, Optional

import streamlit as st

# --------------------------------------------------------------------------
# Palette
# --------------------------------------------------------------------------

BLEU_FONCE = "#0B2545"
BLEU = "#1B4F8A"
BLEU_MOYEN = "#2E6BB0"
BLEU_CLAIR = "#5B9BD5"
BLEU_TRES_CLAIR = "#EAF1FA"

VERT = "#12A150"
VERT_CLAIR = "#E8F7EF"
VERT_FONCE = "#0B7A3B"

ROUGE = "#D92D20"
ROUGE_CLAIR = "#FDECEA"

ORANGE = "#E8830C"
ORANGE_CLAIR = "#FDF3E5"

GRIS = "#64748B"
GRIS_CLAIR = "#F1F5F9"
GRIS_BORDURE = "#DCE3EC"
BLANC = "#FFFFFF"

#: Devises proposées dans la barre latérale (symbole affiché après le montant).
DEVISES = ["€", "$", "CHF", "DH", "FCFA", "£", "TND", "DZD"]


def devise() -> str:
    """Symbole de la devise choisie par l'utilisateur (par défaut l'euro)."""
    return st.session_state.get("devise", "€")


# --------------------------------------------------------------------------
# Formatage des nombres (conventions françaises)
# --------------------------------------------------------------------------

ESPACE_FINE = "\u202f"  # espace fine insécable, séparateur de milliers en français


def formater_nombre(valeur: Optional[float], decimales: int = 2) -> str:
    """Formate un nombre à la française : ``1 234,57``."""
    if valeur is None:
        return "—"
    nombre = float(valeur)
    # Évite l'affichage « -0,00 » pour des valeurs négligeables.
    if abs(nombre) < 0.5 * 10 ** (-decimales):
        nombre = 0.0
    texte = f"{nombre:,.{decimales}f}"
    texte = texte.replace(",", ESPACE_FINE).replace(".", ",")
    # Signe moins typographique (−) plutôt que le trait d'union : c'est le
    # caractère attendu en français et celui qu'utilisent les axes des
    # graphiques, ce qui évite deux graphies différentes dans l'application.
    if texte.startswith("-"):
        texte = "\u2212" + texte[1:]
    return texte


def formater_montant(
    valeur: Optional[float], decimales: int = 2, symbole: Optional[str] = None
) -> str:
    """Formate un montant avec sa devise : ``1 234,57 €``."""
    if valeur is None:
        return "—"
    return f"{formater_nombre(valeur, decimales)} {symbole or devise()}"


def formater_montant_signe(
    valeur: Optional[float], decimales: int = 2, symbole: Optional[str] = None
) -> str:
    """Comme :func:`formater_montant`, mais affiche explicitement le signe ``+``."""
    if valeur is None:
        return "—"
    prefixe = "+" if valeur > 0 else ""
    return f"{prefixe}{formater_montant(valeur, decimales, symbole)}"


def formater_pourcentage(valeur: Optional[float], decimales: int = 2) -> str:
    """Formate un pourcentage exprimé en décimal : ``0.1`` → ``10,00 %``."""
    if valeur is None:
        return "—"
    return f"{formater_nombre(valeur * 100.0, decimales)} %"


def formater_facteur(valeur: Optional[float]) -> str:
    """Formate un coefficient d'actualisation (4 décimales)."""
    if valeur is None:
        return "—"
    return formater_nombre(valeur, 4)


def formater_duree(valeur: Optional[float]) -> str:
    """Formate un délai en années : ``2,35 ans``."""
    if valeur is None:
        return "non atteint"
    unites = "an" if abs(valeur) < 2 else "ans"
    return f"{formater_nombre(valeur, 2)} {unites}"


# --------------------------------------------------------------------------
# Couleurs sémantiques
# --------------------------------------------------------------------------


def couleur_van(van: float) -> str:
    """Couleur associée au signe de la VAN."""
    if van > 0:
        return VERT
    if van < 0:
        return ROUGE
    return GRIS


def couleur_pour_van(valeur: Optional[float]) -> str:
    if valeur is None:
        return GRIS
    return couleur_van(valeur)


def libelle_van(van: float) -> str:
    if van > 0:
        return "Création de valeur"
    if van < 0:
        return "Destruction de valeur"
    return "À l'équilibre"


# --------------------------------------------------------------------------
# Feuille de style
# --------------------------------------------------------------------------

STYLE = f"""
<style>
  /* ---------- Général ---------- */
  html, body, [class*="css"] {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                   "Helvetica Neue", Arial, sans-serif;
  }}
  .block-container {{ padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1240px; }}
  [data-testid="stAppDeployButton"] {{ display: none; }}
  h1, h2, h3, h4 {{ color: {BLEU_FONCE}; letter-spacing: -0.01em; }}
  h1 {{ font-weight: 800; }}
  a {{ color: {BLEU}; }}

  /* ---------- Barre latérale ---------- */
  [data-testid="stSidebar"] {{
      background: linear-gradient(180deg, {BLEU_FONCE} 0%, #133A6B 100%);
      border-right: 1px solid rgba(255,255,255,0.08);
  }}
  [data-testid="stSidebar"] .stMarkdown p,
  [data-testid="stSidebar"] label,
  [data-testid="stSidebar"] h1,
  [data-testid="stSidebar"] h2,
  [data-testid="stSidebar"] h3 {{ color: #E9EFF8; }}
  [data-testid="stSidebarNav"] ul {{ padding-top: .35rem; }}
  [data-testid="stSidebarNav"] a {{
      border-radius: 10px; padding: 6px 10px; color: #D7E3F4;
      transition: background .15s ease;
  }}
  [data-testid="stSidebarNav"] a:hover {{ background: rgba(255,255,255,.10); }}
  [data-testid="stSidebarNav"] a[aria-current="page"] {{
      background: rgba(255,255,255,.18); color: #FFFFFF; font-weight: 600;
  }}
  [data-testid="stSidebarNav"] a span {{ color: inherit; }}

  /* ---------- Cartes ---------- */
  div[data-testid="stMetric"] {{
      background: {BLANC};
      border: 1px solid {GRIS_BORDURE};
      border-radius: 14px;
      padding: 14px 16px;
      box-shadow: 0 1px 2px rgba(11,37,69,.05), 0 6px 18px rgba(11,37,69,.05);
  }}
  div[data-testid="stMetric"] [data-testid="stMetricLabel"] p {{
      color: {GRIS}; font-size: .78rem; font-weight: 700;
      text-transform: uppercase; letter-spacing: .03em;
      /* Sans ces règles, Streamlit tronque le libellé par des points de
         suspension : on préfère un retour à la ligne. */
      white-space: normal; overflow: visible; text-overflow: clip;
      line-height: 1.25; overflow-wrap: break-word;
  }}
  div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
      color: {BLEU_FONCE};
      font-size: clamp(1.05rem, 1.5vw, 1.55rem);
      white-space: normal;
  }}
  div[data-testid="stMetric"] {{
      min-height: 116px;
  }}

  div[data-testid="stContainer"] {{
      border-radius: 14px;
  }}
  [data-testid="stVerticalBlockBorderWrapper"] {{
      border-radius: 14px;
      border-color: {GRIS_BORDURE};
      box-shadow: 0 1px 2px rgba(11,37,69,.04);
  }}

  /* ---------- Boutons ---------- */
  .stButton > button, .stDownloadButton > button {{
      border-radius: 10px; font-weight: 600; border: 1px solid {GRIS_BORDURE};
      transition: transform .06s ease, box-shadow .15s ease;
  }}
  .stButton > button:hover, .stDownloadButton > button:hover {{
      border-color: {BLEU_MOYEN}; color: {BLEU}; box-shadow: 0 3px 10px rgba(27,79,138,.15);
  }}
  .stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {{
      background: {BLEU}; border-color: {BLEU};
  }}
  .stButton > button[kind="primary"]:hover,
  .stDownloadButton > button[kind="primary"]:hover {{
      background: {BLEU_FONCE}; border-color: {BLEU_FONCE}; color: #fff;
  }}

  /* ---------- Tableaux ---------- */
  [data-testid="stDataFrame"], [data-testid="stDataEditor"] {{
      border-radius: 12px; border: 1px solid {GRIS_BORDURE};
  }}
  table.van-table {{
      width: 100%; border-collapse: collapse; font-size: .90rem;
      background: {BLANC}; border-radius: 12px; overflow: hidden;
  }}
  table.van-table thead th {{
      background: {BLEU_TRES_CLAIR}; color: {BLEU_FONCE}; text-align: left;
      padding: 9px 12px; font-weight: 700; border-bottom: 1px solid {GRIS_BORDURE};
  }}
  table.van-table tbody td {{
      padding: 8px 12px; border-bottom: 1px solid {GRIS_CLAIR}; color: #1F2937;
  }}
  table.van-table tbody tr:last-child td {{ border-bottom: none; }}
  table.van-table td.nombre, table.van-table th.nombre {{ text-align: right; font-variant-numeric: tabular-nums; }}
  table.van-table tbody tr.total td {{
      background: {BLEU_TRES_CLAIR}; font-weight: 700; color: {BLEU_FONCE};
  }}

  /* ---------- Bandeau d'accueil ---------- */
  .hero {{
      background: linear-gradient(120deg, {BLEU_FONCE} 0%, {BLEU} 55%, {BLEU_MOYEN} 100%);
      border-radius: 18px; padding: 34px 38px; color: #FFFFFF;
      box-shadow: 0 12px 30px rgba(11,37,69,.22);
  }}
  .hero h1 {{ color: #FFFFFF; margin: 0 0 6px 0; font-size: 2.05rem; }}
  .hero .sous-titre {{ color: #C9DBF2; font-size: 1.02rem; margin: 0 0 4px 0; }}
  .hero .etiquette {{
      display: inline-block; background: rgba(255,255,255,.16);
      border: 1px solid rgba(255,255,255,.25); color: #EAF1FA;
      border-radius: 999px; padding: 3px 12px; font-size: .76rem;
      letter-spacing: .05em; text-transform: uppercase; margin-bottom: 14px;
  }}

  /* ---------- Cartes de contenu ---------- */
  .carte {{
      background: {BLANC}; border: 1px solid {GRIS_BORDURE}; border-radius: 14px;
      padding: 18px 20px; height: 100%;
      box-shadow: 0 1px 2px rgba(11,37,69,.05), 0 6px 18px rgba(11,37,69,.04);
  }}
  .carte .icone {{ font-size: 1.5rem; }}
  .carte h4 {{ margin: 8px 0 6px 0; font-size: 1.02rem; }}
  .carte p {{ margin: 0; color: {GRIS}; font-size: .90rem; line-height: 1.5; }}

  /* ---------- Encadrés d'interprétation ---------- */
  .encadre {{
      border-radius: 14px; padding: 18px 20px; border-left: 6px solid {GRIS};
      background: {GRIS_CLAIR};
  }}
  .encadre h4 {{ margin: 0 0 8px 0; font-size: 1.05rem; }}
  .encadre p {{ margin: 0; line-height: 1.55; color: #29323F; font-size: .94rem; }}
  .encadre.positif {{ background: {VERT_CLAIR}; border-left-color: {VERT}; }}
  .encadre.positif h4 {{ color: {VERT_FONCE}; }}
  .encadre.negatif {{ background: {ROUGE_CLAIR}; border-left-color: {ROUGE}; }}
  .encadre.negatif h4 {{ color: {ROUGE}; }}
  .encadre.neutre {{ background: {BLEU_TRES_CLAIR}; border-left-color: {BLEU}; }}
  .encadre.neutre h4 {{ color: {BLEU_FONCE}; }}
  .encadre.attention {{ background: {ORANGE_CLAIR}; border-left-color: {ORANGE}; }}
  .encadre.attention h4 {{ color: {ORANGE}; }}

  /* ---------- Étiquettes ---------- */
  .etiquette {{ display:inline-block; border-radius:999px; padding:2px 10px; font-size:.74rem;
                font-weight:700; letter-spacing:.03em; text-transform:uppercase; }}
  .etiquette.exemple {{ background:{ORANGE_CLAIR}; color:{ORANGE}; border:1px solid #F5D6A8; }}
  .etiquette.reel {{ background:{BLEU_TRES_CLAIR}; color:{BLEU}; border:1px solid #C6DAF0; }}
  .etiquette.positif {{ background:{VERT_CLAIR}; color:{VERT_FONCE}; border:1px solid #B7E4C9; }}
  .etiquette.negatif {{ background:{ROUGE_CLAIR}; color:{ROUGE}; border:1px solid #F5C6C1; }}

  .formule {{
      background: {BLEU_FONCE}; color: #EAF1FA; border-radius: 12px;
      padding: 16px 20px; font-family: "SFMono-Regular", Consolas, monospace;
      font-size: 1.0rem; overflow-x: auto;
  }}
  /* ---------- Carte VAN principale ---------- */
  .carte-van {{ border-radius: 16px; padding: 18px 22px; border: 1px solid #DCE3EC; background: #fff; }}
  .carte-van .libelle {{ font-size: .79rem; text-transform: uppercase; letter-spacing: .06em;
                        font-weight: 700; color: #64748B; }}
  .carte-van .valeur {{ font-size: clamp(1.35rem, 2vw, 2.05rem); font-weight: 800;
                       letter-spacing: -.02em; line-height: 1.2; margin: 6px 0 2px 0;
                       font-variant-numeric: tabular-nums; word-break: break-word; }}
  .carte-van .statut {{ font-size: .88rem; font-weight: 600; }}
  .carte-van {{ min-height: 116px; display: flex; flex-direction: column;
                justify-content: center; }}
  .carte-van.positif {{ background: linear-gradient(135deg, #E8F7EF 0%, #FFFFFF 72%); border-color: #B7E4C9; }}
  .carte-van.positif .valeur, .carte-van.positif .statut {{ color: #0B7A3B; }}
  .carte-van.negatif {{ background: linear-gradient(135deg, #FDECEA 0%, #FFFFFF 72%); border-color: #F5C6C1; }}
  .carte-van.negatif .valeur, .carte-van.negatif .statut {{ color: #D92D20; }}
  .carte-van.neutre {{ background: linear-gradient(135deg, #EAF1FA 0%, #FFFFFF 72%); border-color: #C6DAF0; }}
  .carte-van.neutre .valeur, .carte-van.neutre .statut {{ color: #1B4F8A; }}

  /* ---------- Rangées de cartes : passage à la ligne si l'écran est étroit,
     plutôt que des libellés tronqués ou coupés au milieu d'un mot. ----------
     Les clés de conteneur (st.container(key=...)) deviennent des classes
     CSS préfixées par « st-key- ». */
  .st-key-cartes_resultats [data-testid="stHorizontalBlock"],
  .st-key-cartes_accueil [data-testid="stHorizontalBlock"],
  .st-key-hypotheses_projet [data-testid="stHorizontalBlock"] {{
      flex-wrap: wrap; row-gap: 10px;
  }}
  .st-key-cartes_resultats [data-testid="stColumn"],
  .st-key-cartes_accueil [data-testid="stColumn"] {{ min-width: 208px; }}
  .st-key-hypotheses_projet [data-testid="stColumn"] {{ min-width: 190px; }}
  .st-key-cartes_resultats [data-testid="stMetric"],
  .st-key-cartes_accueil [data-testid="stMetric"] {{ height: 100%; }}

  /* ---------- Lisibilité des intitulés ----------
     Streamlit autorise par défaut la coupure au milieu d'un mot
     (« désélectionne / r ») : on la réserve aux mots réellement trop
     longs pour la largeur disponible. Attention : l'intitulé d'un champ
     est un <label>, pas un <div>. */
  [data-testid="stWidgetLabel"] p,
  [data-testid="stButton"] button p,
  [data-testid="stDownloadButton"] button p {{
      word-break: keep-all; overflow-wrap: normal;
  }}

  .note {{ color: {GRIS}; font-size: .84rem; }}
  .section-titre {{
      color: {BLEU_FONCE}; font-weight: 700; font-size: 1.22rem;
      margin: 6px 0 2px 0;
  }}
</style>
"""


def appliquer_style() -> None:
    """Injecte la feuille de style de l'application."""
    st.markdown(STYLE, unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Petits composants HTML
# --------------------------------------------------------------------------


def echapper(texte: Any) -> str:
    """Échappe le HTML : indispensable avant d'afficher une saisie utilisateur.

    Sans cette précaution, un nom de projet contenant du HTML serait interprété
    comme du code par le navigateur.
    """
    return html.escape(str(texte))


def bandeau(titre: str, sous_titre: str, etiquette: str = "") -> None:
    """Affiche le bandeau dégradé bleu foncé."""
    balise = f'<div class="etiquette">{echapper(etiquette)}</div>' if etiquette else ""
    st.markdown(
        f'<div class="hero">{balise}<h1>{echapper(titre)}</h1>'
        f'<p class="sous-titre">{echapper(sous_titre)}</p></div>',
        unsafe_allow_html=True,
    )


def carte(icone: str, titre: str, texte: str) -> None:
    """Affiche une carte de présentation."""
    st.markdown(
        f'<div class="carte"><div class="icone">{echapper(icone)}</div>'
        f"<h4>{echapper(titre)}</h4><p>{echapper(texte)}</p></div>",
        unsafe_allow_html=True,
    )


def carte_van(
    valeur: str,
    statut: str,
    libelle: str = "Valeur actuelle nette",
    ton: str = "neutre",
) -> None:
    """Affiche la grande carte de résultat de la VAN, colorée selon son signe."""
    if ton not in ("positif", "negatif", "neutre"):
        ton = "neutre"
    st.markdown(
        f'<div class="carte-van {ton}"><div class="libelle">{echapper(libelle)}</div>'
        f'<div class="valeur">{echapper(valeur)}</div>'
        f'<div class="statut">{echapper(statut)}</div></div>',
        unsafe_allow_html=True,
    )


def encadre(titre: str, message: str, ton: str = "neutre") -> None:
    """Affiche un encadré coloré.

    ``ton`` peut valoir ``positif``, ``negatif``, ``neutre`` ou ``attention``.
    """
    if ton not in ("positif", "negatif", "neutre", "attention"):
        ton = "neutre"
    st.markdown(
        f'<div class="encadre {ton}"><h4>{echapper(titre)}</h4>'
        f"<p>{echapper(message)}</p></div>",
        unsafe_allow_html=True,
    )


def liste_encadre(titre: str, elements: list, ton: str = "neutre") -> None:
    """Affiche un encadré contenant une liste à puces (messages de validation)."""
    if ton not in ("positif", "negatif", "neutre", "attention"):
        ton = "neutre"
    items = "".join(f"<li>{echapper(element)}</li>" for element in elements)
    st.markdown(
        f'<div class="encadre {ton}"><h4>{echapper(titre)}</h4>'
        f'<ul style="margin:6px 0 0 0;padding-left:20px;color:#29323F;font-size:.93rem;">'
        f"{items}</ul></div>",
        unsafe_allow_html=True,
    )


def etiquette(texte: str, ton: str = "reel") -> str:
    """Renvoie une étiquette HTML (à insérer dans une chaîne)."""
    return f'<span class="etiquette {ton}">{echapper(texte)}</span>'


def titre_section(texte: str, note: str = "") -> None:
    """Affiche un titre de section, avec une note facultative."""
    suffixe = f' <span class="note">{echapper(note)}</span>' if note else ""
    st.markdown(
        f'<div class="section-titre">{echapper(texte)}{suffixe}</div>',
        unsafe_allow_html=True,
    )


def tableau_html(
    entetes: list,
    lignes: list,
    classe_derniere: str = "",
    hauteur_max: Optional[int] = None,
) -> str:
    """Construit un tableau HTML à partir d'en-têtes et de lignes.

    ``entetes`` est une liste de couples ``(texte, classe_css)``.
    ``lignes`` est une liste de triplets ``(cellules, classes_cellules, classe_ligne)``
    où les cellules sont des chaînes déjà formatées et échappées par l'appelant.
    ``hauteur_max`` ajoute un défilement vertical lorsque le tableau est long.
    """
    html_entetes = "".join(f'<th class="{classe}">{texte}</th>' for texte, classe in entetes)
    html_lignes = []
    for index, (cellules, classes, classe_ligne) in enumerate(lignes):
        dernier = index == len(lignes) - 1
        classe = classe_derniere if (dernier and classe_derniere) else classe_ligne
        cellules_html = "".join(
            f'<td class="{classes[i] if i < len(classes) else ""}">{cellules[i]}</td>'
            for i in range(len(cellules))
        )
        html_lignes.append(f'<tr class="{classe}">{cellules_html}</tr>')

    tableau = (
        f'<table class="van-table"><thead><tr>{html_entetes}</tr></thead>'
        f"<tbody>{''.join(html_lignes)}</tbody></table>"
    )
    if hauteur_max:
        return (
            f'<div style="max-height:{hauteur_max}px;overflow-y:auto;'
            f'border-radius:12px;">{tableau}</div>'
        )
    return tableau
