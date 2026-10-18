"""VAN Project Analyzer — point d'entrée de l'application Streamlit.

Lancement :

    streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from van_analyzer import (
    donnees,
    etat,
    presentation as pres,
)
from van_analyzer import (
    pages_accueil,
    pages_calculateur,
    pages_comparaison,
    pages_guide,
    pages_historique,
)

st.set_page_config(
    page_title="VAN Project Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _barre_laterale() -> None:
    """Contenu de la barre latérale : devise, rappel de la formule, données."""
    with st.sidebar:
        st.markdown(
            '<div style="padding:6px 2px 2px 2px;">'
            '<div style="font-size:1.05rem;font-weight:800;color:#FFFFFF;'
            'letter-spacing:-.01em;">VAN Project Analyzer</div>'
            '<div style="font-size:.78rem;color:#A9C2E0;margin-top:2px;">'
            "Analyse d'investissement</div></div>",
            unsafe_allow_html=True,
        )
        st.divider()

        st.selectbox(
            "Devise d'affichage",
            pres.DEVISES,
            key=etat.CLE_DEVISE,
            help="La devise choisie est utilisée pour l'affichage uniquement : "
            "les calculs sont identiques quelle que soit la devise.",
        )

        st.divider()
        st.markdown("**Rappel de la formule**")
        st.markdown(
            '<div style="background:rgba(255,255,255,.10);border-radius:10px;'
            'padding:10px 12px;color:#E9EFF8;font-family:SFMono-Regular,Consolas,'
            'monospace;font-size:.83rem;line-height:1.5;">'
            "VAN = −I₀ + Σ [ CF<sub>t</sub> / (1+r)<sup>t</sup> ]"
            "</div>",
            unsafe_allow_html=True,
        )

        st.divider()
        entrees = etat.historique()
        st.markdown(f"**{len(entrees)}** calcul(s) enregistré(s).")
        st.button(
            "Réinitialiser le calculateur",
            icon="♻️",
            width="stretch",
            on_click=etat.reinitialiser_calculateur,
            help="Efface la saisie en cours dans le calculateur.",
        )

        st.divider()
        st.caption(
            "Aucune donnée ne quitte votre machine : les calculs sont enregistrés "
            f"dans le fichier local « {donnees.chemin_historique()} »."
        )


def main() -> None:
    etat.initialiser()
    pres.appliquer_style()

    pages = {
        "accueil": st.Page(
            pages_accueil.rendre,
            title="Accueil",
            icon="🏠",
            url_path="accueil",
            default=True,
        ),
        "calculateur": st.Page(
            pages_calculateur.rendre,
            title="Calculateur VAN",
            icon="🧮",
            url_path="calculateur",
        ),
        "comparaison": st.Page(
            pages_comparaison.rendre,
            title="Comparaison des projets",
            icon="⚖️",
            url_path="comparaison",
        ),
        "historique": st.Page(
            pages_historique.rendre,
            title="Historique",
            icon="🗂️",
            url_path="historique",
        ),
        "guide": st.Page(
            pages_guide.rendre,
            title="Guide pédagogique",
            icon="📘",
            url_path="guide",
        ),
    }
    etat.PAGES.update(pages)

    navigation = st.navigation(list(pages.values()), position="sidebar")
    _barre_laterale()
    navigation.run()


main()
