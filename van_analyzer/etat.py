"""État de session partagé par toutes les pages de l'application."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

from . import donnees, finance

# --------------------------------------------------------------------------
# Clés de session
# --------------------------------------------------------------------------

CLE_DEVISE = "devise"
CLE_PANIER = "panier_comparaison"
CLE_TAUX_COMMUN = "taux_commun_actif"
CLE_TAUX_COMMUN_VALEUR = "taux_commun_valeur"
CLE_ORIGINE_CHARGEE = "origine_projet_charge"

# Clés des champs du calculateur
CLE_NOM = "nom_projet"
CLE_INVESTISSEMENT = "investissement_initial"
CLE_TAUX = "taux_pct"
CLE_DUREE = "duree"

# Clés internes servant à préremplir l'éditeur de flux.
# Un éditeur Streamlit n'accepte pas d'être prérempli par session_state : on fait
# donc varier sa clé (ci-dessous) et on lui fournit les valeurs de départ via le
# paramètre « data ». Ces clés ne sont jamais des clés de widget.
CLE_SOURCE_FLUX = "source_flux"
CLE_VERSION_SOURCE = "version_source_flux"

#: Clé du champ servant à remplir toutes les années d'un même montant.
CLE_MONTANT_UNIFORME = "montant_uniforme"

DUREE_DEFAUT = 3
FLUX_DEFAUT = [0.0, 0.0, 0.0]

#: Pages référencées par :func:`aller_vers` (rempli par ``app.py``).
PAGES: Dict[str, Any] = {}


# --------------------------------------------------------------------------
# Initialisation
# --------------------------------------------------------------------------


def initialiser() -> None:
    """Initialise les valeurs par défaut de la session (idempotent)."""
    if CLE_DEVISE not in st.session_state:
        st.session_state[CLE_DEVISE] = "€"
    if CLE_PANIER not in st.session_state:
        st.session_state[CLE_PANIER] = []
    if CLE_TAUX_COMMUN not in st.session_state:
        st.session_state[CLE_TAUX_COMMUN] = False
    if CLE_TAUX_COMMUN_VALEUR not in st.session_state:
        st.session_state[CLE_TAUX_COMMUN_VALEUR] = 10.0
    if CLE_NOM not in st.session_state:
        st.session_state[CLE_NOM] = ""
    if CLE_INVESTISSEMENT not in st.session_state:
        st.session_state[CLE_INVESTISSEMENT] = 1000.0
    if CLE_TAUX not in st.session_state:
        st.session_state[CLE_TAUX] = 10.0
    if CLE_DUREE not in st.session_state:
        st.session_state[CLE_DUREE] = DUREE_DEFAUT
    if CLE_ORIGINE_CHARGEE not in st.session_state:
        st.session_state[CLE_ORIGINE_CHARGEE] = ""
    if CLE_SOURCE_FLUX not in st.session_state:
        st.session_state[CLE_SOURCE_FLUX] = {}
    if CLE_VERSION_SOURCE not in st.session_state:
        st.session_state[CLE_VERSION_SOURCE] = 0


def reinitialiser_calculateur() -> None:
    """Remet le calculateur à zéro et efface les valeurs saisies."""
    st.session_state[CLE_NOM] = ""
    st.session_state[CLE_INVESTISSEMENT] = 1000.0
    st.session_state[CLE_TAUX] = 10.0
    st.session_state[CLE_DUREE] = DUREE_DEFAUT
    definir_flux_source(DUREE_DEFAUT, FLUX_DEFAUT)
    st.session_state[CLE_ORIGINE_CHARGEE] = ""


# --------------------------------------------------------------------------
# Historique
# --------------------------------------------------------------------------


def historique() -> List[Dict[str, Any]]:
    """Historique courant, lu depuis le fichier local."""
    return donnees.charger_historique()


def recharger_historique() -> List[Dict[str, Any]]:
    return donnees.charger_historique()


def projet_depuis_entree(entree: Dict[str, Any]) -> Optional[finance.Projet]:
    """Reconstruit un objet projet depuis un enregistrement d'historique."""
    return finance.projet_depuis_dict(entree)


def resultat_depuis_entree(
    entree: Dict[str, Any], taux_force: Optional[float] = None
) -> Optional[finance.Resultat]:
    """Analyse un enregistrement d'historique, éventuellement à un taux imposé."""
    projet = projet_depuis_entree(entree)
    if projet is None:
        return None
    if taux_force is not None:
        projet = finance.Projet(
            nom=projet.nom,
            investissement_initial=projet.investissement_initial,
            taux_actualisation=taux_force,
            flux=list(projet.flux),
            identifiant=projet.identifiant,
            date_creation=projet.date_creation,
            origine=projet.origine,
        )
    return finance.analyser(projet)


# --------------------------------------------------------------------------
# Panier de comparaison
# --------------------------------------------------------------------------


def panier() -> List[str]:
    return list(st.session_state.get(CLE_PANIER, []))


def basculer_panier(identifiant: str) -> bool:
    """Ajoute ou retire un projet du panier de comparaison."""
    courant = panier()
    if identifiant in courant:
        courant.remove(identifiant)
        ajoute = False
    else:
        courant.append(identifiant)
        ajoute = True
    st.session_state[CLE_PANIER] = courant
    return ajoute


def definir_panier(identifiants: List[str]) -> None:
    st.session_state[CLE_PANIER] = list(dict.fromkeys(identifiants))


def vider_panier() -> None:
    st.session_state[CLE_PANIER] = []


# --------------------------------------------------------------------------
# Éditeur de flux de trésorerie
# --------------------------------------------------------------------------


def cle_editeur(duree: int) -> str:
    """Clé de l'éditeur de flux, propre à la durée et à la version des données.

    La version change lorsqu'on charge un exemple ou qu'on applique un montant
    uniforme : un nouvel identifiant de widget est alors créé, ce qui permet de
    préremplir le tableau. C'est la solution retenue car Streamlit interdit
    d'écrire directement dans l'état d'un éditeur de données.
    """
    version = int(st.session_state.get(CLE_VERSION_SOURCE, 0))
    return f"editeur_flux_{int(duree)}_{version}"


def definir_flux_source(duree: int, flux: List[float]) -> None:
    """Enregistre les flux de départ de l'éditeur pour la durée donnée."""
    sources = dict(st.session_state.get(CLE_SOURCE_FLUX, {}))
    sources[int(duree)] = [float(valeur) for valeur in flux][: int(duree)]
    st.session_state[CLE_SOURCE_FLUX] = sources
    st.session_state[CLE_VERSION_SOURCE] = (
        int(st.session_state.get(CLE_VERSION_SOURCE, 0)) + 1
    )


def flux_source(duree: int) -> List[float]:
    """Flux de départ à afficher dans l'éditeur pour la durée donnée."""
    duree = int(duree)
    sources = st.session_state.get(CLE_SOURCE_FLUX, {})
    valeurs = sources.get(duree)
    if isinstance(valeurs, list) and len(valeurs) == duree:
        return [float(valeur) for valeur in valeurs]
    return [0.0] * duree


def dataframe_flux(flux: List[float]) -> pd.DataFrame:
    """Tableau modifiable des flux de trésorerie."""
    return pd.DataFrame(
        {
            "Année": [f"Année {index}" for index in range(1, len(flux) + 1)],
            "Flux de trésorerie": [float(valeur) for valeur in flux],
        }
    )


def flux_depuis_dataframe(donnees_editeur: Any) -> List[Optional[float]]:
    """Extrait la liste des flux depuis la valeur renvoyée par l'éditeur."""
    if not isinstance(donnees_editeur, pd.DataFrame):
        return []
    if "Flux de trésorerie" not in donnees_editeur.columns:
        return []
    return [finance.en_nombre(valeur) for valeur in donnees_editeur["Flux de trésorerie"]]


def appliquer_montant_uniforme() -> None:
    """Remplit toutes les années de l'éditeur avec le montant saisi.

    La fonction lit la durée et le montant dans l'état de session plutôt que de
    les recevoir en arguments : un rappel ``on_click`` reçoit en effet les
    valeurs du rendu précédent, ce qui donnerait un résultat décalé d'une étape.
    """
    duree = int(st.session_state.get(CLE_DUREE, DUREE_DEFAUT))
    montant = finance.en_nombre(st.session_state.get(CLE_MONTANT_UNIFORME, 0.0))
    definir_flux_source(duree, [float(montant or 0.0)] * duree)


# --------------------------------------------------------------------------
# Chargement d'un projet dans le calculateur
# --------------------------------------------------------------------------


def charger_dans_calculateur(projet: finance.Projet) -> None:
    """Prépare le calculateur pour afficher le projet fourni."""
    duree = max(finance.DUREE_MIN, min(finance.DUREE_MAX, len(projet.flux)))
    st.session_state[CLE_NOM] = projet.nom
    st.session_state[CLE_INVESTISSEMENT] = float(projet.investissement_initial)
    st.session_state[CLE_TAUX] = float(projet.taux_actualisation) * 100.0
    st.session_state[CLE_DUREE] = duree
    definir_flux_source(duree, list(projet.flux)[:duree])
    st.session_state[CLE_ORIGINE_CHARGEE] = projet.origine


def charger_exemple(exemple: Dict[str, Any]) -> None:
    """Charge un exemple de démonstration dans le calculateur."""
    charger_dans_calculateur(donnees.exemple_en_projet(exemple, horodatage=False))


# --------------------------------------------------------------------------
# Navigation
# --------------------------------------------------------------------------


def aller_vers(cle: str) -> None:
    """Bascule vers une autre page de l'application."""
    page = PAGES.get(cle)
    if page is not None:
        st.switch_page(page)
