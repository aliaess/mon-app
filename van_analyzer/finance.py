"""Moteur de calcul financier du VAN Project Analyzer.

Ce module est volontairement **indépendant de Streamlit** : toutes les fonctions
sont pures et donc directement testables (voir ``tests/test_finance.py``).

Formule de référence
--------------------
    VAN = -I0 + somme( CF_t / (1 + r)^t )   pour t = 1 .. n

avec :
    I0   : investissement initial (positif = décaissement)
    CF_t : flux de trésorerie de l'année t (négatif = décaissement)
    r    : taux d'actualisation exprimé en décimal (0,10 = 10 %)
    n    : durée du projet en années
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

# --------------------------------------------------------------------------
# Constantes
# --------------------------------------------------------------------------

DUREE_MIN = 1
DUREE_MAX = 50

TAUX_PLANCHER_TRI = -0.9999  # borne basse de recherche du TRI (-99,99 %)
TAUX_PLAFOND_TRI = 10.0      # borne haute de recherche du TRI (1 000 %)

#: En dessous de ce montant (exprimé dans l'unité monétaire), on considère que
#: la VAN est nulle : cela évite d'afficher « 0,0000000001 € » comme positif.
TOLERANCE_VAN_NULLE = 0.005


# --------------------------------------------------------------------------
# Structures de données
# --------------------------------------------------------------------------


@dataclass
class Projet:
    """Un projet d'investissement et ses hypothèses."""

    nom: str
    investissement_initial: float
    taux_actualisation: float  # décimal
    flux: List[float] = field(default_factory=list)
    identifiant: str = ""
    date_creation: str = ""
    origine: str = ""  # "exemple" pour les projets de démonstration

    @property
    def duree(self) -> int:
        return len(self.flux)

    @property
    def taux_pourcentage(self) -> float:
        return self.taux_actualisation * 100.0

    @property
    def est_exemple(self) -> bool:
        return self.origine == "exemple"


@dataclass
class LigneAnnee:
    """Une ligne du tableau de calcul (l'année 0 correspond à l'investissement)."""

    annee: int
    flux: float
    facteur: float            # 1 / (1 + r)^t
    flux_actualise: float     # flux * facteur
    cumul_actualise: float    # cumul des flux actualisés depuis l'année 0
    cumul_simple: float       # cumul des flux non actualisés


@dataclass
class Resultat:
    """Résultat complet d'une analyse de projet."""

    projet: Projet
    lignes: List[LigneAnnee]
    van: float
    somme_flux_actualises: float
    somme_flux: float
    van_taux_nul: float
    tri: Optional[float]
    indice_rentabilite: Optional[float]
    delai_recuperation: Optional[float]

    @property
    def est_positive(self) -> bool:
        return self.van > TOLERANCE_VAN_NULLE

    @property
    def est_nulle(self) -> bool:
        return abs(self.van) <= TOLERANCE_VAN_NULLE

    @property
    def est_negative(self) -> bool:
        return self.van < -TOLERANCE_VAN_NULLE


# --------------------------------------------------------------------------
# Utilitaires numériques
# --------------------------------------------------------------------------


def en_nombre(valeur: Any) -> Optional[float]:
    """Convertit une saisie utilisateur en float, ou renvoie ``None``.

    Accepte les nombres, les chaînes (« 1 500,50 »), les virgules décimales et
    les espaces de séparation. Renvoie ``None`` si la conversion échoue ou si
    la valeur n'est pas finie (NaN, infini).
    """
    if valeur is None or isinstance(valeur, bool):
        return None
    if isinstance(valeur, (int, float)):
        nombre = float(valeur)
    else:
        texte = str(valeur).strip().replace("\u202f", "").replace("\xa0", "")
        texte = texte.replace(" ", "").replace(",", ".")
        if texte in ("", "-", "+", "."):
            return None
        try:
            nombre = float(texte)
        except ValueError:
            return None
    if math.isnan(nombre) or math.isinf(nombre):
        return None
    return nombre


def facteur_actualisation(taux: float, annee: int) -> float:
    """Renvoie le coefficient d'actualisation ``1 / (1 + r)^t``."""
    return 1.0 / (1.0 + taux) ** annee


def calculer_van(
    investissement_initial: float, taux: float, flux: Sequence[float]
) -> float:
    """Calcule la VAN d'un projet : ``-I0 + somme( CF_t / (1 + r)^t )``."""
    van = -float(investissement_initial)
    for t, cf in enumerate(flux, start=1):
        van += float(cf) / (1.0 + taux) ** t
    return van


# --------------------------------------------------------------------------
# Validation des saisies
# --------------------------------------------------------------------------


def valider_saisie(
    nom: str,
    investissement_initial: Any,
    taux_pourcentage: Any,
    flux: Sequence[Any],
) -> Tuple[List[str], List[str]]:
    """Valide les données saisies.

    Renvoie un couple ``(erreurs, avertissements)``. Les erreurs empêchent le
    calcul ; les avertissements signalent une situation inhabituelle mais
    mathématiquement valide.
    """
    erreurs: List[str] = []
    avertissements: List[str] = []

    # --- Nom du projet ---------------------------------------------------
    if not str(nom or "").strip():
        erreurs.append("Le nom du projet est obligatoire.")

    # --- Investissement initial -----------------------------------------
    i0 = en_nombre(investissement_initial)
    if i0 is None:
        erreurs.append(
            "L'investissement initial doit être un montant numérique "
            "(par exemple 10 000)."
        )
    elif i0 < 0:
        avertissements.append(
            "L'investissement initial est négatif : cela correspond à un "
            "encaissement initial (subvention, cession d'actif) et non à un "
            "décaissement. Vérifiez que c'est bien votre intention."
        )

    # --- Taux d'actualisation -------------------------------------------
    taux = en_nombre(taux_pourcentage)
    if taux is None:
        erreurs.append(
            "Le taux d'actualisation doit être un pourcentage numérique "
            "(par exemple 8 pour 8 %)."
        )
    elif taux <= -100.0:
        erreurs.append(
            "Le taux d'actualisation doit être supérieur à -100 % : "
            "en dessous, l'actualisation n'a plus de sens économique."
        )
    elif taux < 0:
        avertissements.append(
            "Le taux d'actualisation est négatif. C'est possible en période de "
            "déflation, mais vérifiez que ce n'est pas une erreur de signe."
        )
    elif taux > 100.0:
        avertissements.append(
            "Le taux d'actualisation dépasse 100 % : la valeur actuelle des "
            "flux sera fortement réduite. Vérifiez le taux saisi."
        )

    # --- Durée et flux ---------------------------------------------------
    if not flux:
        erreurs.append("La durée du projet doit être d'au moins 1 an.")
    elif len(flux) > DUREE_MAX:
        erreurs.append(
            f"La durée du projet ne peut pas dépasser {DUREE_MAX} années."
        )

    for index, valeur in enumerate(flux, start=1):
        if en_nombre(valeur) is None:
            erreurs.append(
                f"Année {index} : le flux de trésorerie doit être un nombre "
                "(les montants négatifs sont acceptés, par exemple -2 500)."
            )

    nombres = [en_nombre(v) for v in flux]
    if nombres and all(n is not None for n in nombres):
        if all(n <= 0 for n in nombres):
            avertissements.append(
                "Aucun flux de trésorerie positif n'a été saisi : le projet ne "
                "génère aucun encaissement et sa VAN sera nécessairement "
                "négative."
            )

    return erreurs, avertissements


# --------------------------------------------------------------------------
# Construction du tableau de calcul
# --------------------------------------------------------------------------


def construire_lignes(projet: Projet) -> List[LigneAnnee]:
    """Construit le tableau année par année (année 0 incluse)."""
    lignes: List[LigneAnnee] = []
    cumul_actualise = 0.0
    cumul_simple = 0.0

    # Année 0 : décaissement initial, non actualisé (facteur = 1).
    flux_initial = -float(projet.investissement_initial)
    cumul_actualise += flux_initial
    cumul_simple += flux_initial
    lignes.append(
        LigneAnnee(
            annee=0,
            flux=flux_initial,
            facteur=1.0,
            flux_actualise=flux_initial,
            cumul_actualise=cumul_actualise,
            cumul_simple=cumul_simple,
        )
    )

    for t, cf in enumerate(projet.flux, start=1):
        facteur = facteur_actualisation(projet.taux_actualisation, t)
        flux_actualise = float(cf) * facteur
        cumul_actualise += flux_actualise
        cumul_simple += float(cf)
        lignes.append(
            LigneAnnee(
                annee=t,
                flux=float(cf),
                facteur=facteur,
                flux_actualise=flux_actualise,
                cumul_actualise=cumul_actualise,
                cumul_simple=cumul_simple,
            )
        )

    return lignes


# --------------------------------------------------------------------------
# Indicateurs complémentaires
# --------------------------------------------------------------------------


def _grille_taux() -> List[float]:
    """Points d'essai utilisés pour localiser le TRI (du plus bas au plus haut)."""
    valeurs = {
        -0.9999, -0.999, -0.99, -0.95, -0.9, -0.8, -0.7, -0.6,
        -0.5, -0.4, -0.3, -0.2, -0.15, -0.1, -0.05, -0.02, -0.01, -0.005,
    }
    valeurs |= {i / 1000.0 for i in range(0, 101)}    # 0 % à 10 % (pas de 0,1 %)
    valeurs |= {i / 100.0 for i in range(11, 101)}    # 11 % à 100 % (pas de 1 %)
    valeurs |= {1.2, 1.5, 2.0, 3.0, 5.0, TAUX_PLAFOND_TRI}
    return sorted(valeurs)


def taux_rentabilite_interne(
    investissement_initial: float, flux: Sequence[float]
) -> Optional[float]:
    """Taux de rentabilité interne (TRI), ou ``None`` s'il n'existe pas.

    Le TRI est le taux qui annule la VAN. Il est recherché par balayage puis
    dichotomie sur l'intervalle ``[-99,99 % ; +1 000 %]``.

    Attention : lorsque les flux changent plusieurs fois de signe, il peut
    exister plusieurs TRI. La méthode renvoie alors la plus petite solution
    positive trouvée, et ``None`` si aucune solution n'existe dans
    l'intervalle — l'application indique alors explicitement l'absence de TRI.
    """

    def van_au_taux(r: float) -> float:
        return calculer_van(investissement_initial, r, flux)

    precedent_taux: Optional[float] = None
    precedent_valeur: Optional[float] = None

    for taux in _grille_taux():
        valeur = van_au_taux(taux)
        if valeur == 0.0:
            return taux
        if (
            precedent_taux is not None
            and precedent_valeur is not None
            and (precedent_valeur < 0.0) != (valeur < 0.0)
        ):
            borne_basse, borne_haute = precedent_taux, taux
            valeur_basse = precedent_valeur
            for _ in range(200):  # dichotomie : précision machine atteinte
                milieu = (borne_basse + borne_haute) / 2.0
                valeur_milieu = van_au_taux(milieu)
                if valeur_milieu == 0.0:
                    return milieu
                if (valeur_basse < 0.0) != (valeur_milieu < 0.0):
                    borne_haute = milieu
                else:
                    borne_basse, valeur_basse = milieu, valeur_milieu
            return (borne_basse + borne_haute) / 2.0
        precedent_taux, precedent_valeur = taux, valeur

    return None


def indice_rentabilite(
    investissement_initial: float, somme_flux_actualises: float
) -> Optional[float]:
    """Indice de rentabilité = flux actualisés / investissement initial.

    N'a de sens que si l'investissement initial est strictement positif ;
    renvoie ``None`` sinon.
    """
    if investissement_initial <= 0:
        return None
    return somme_flux_actualises / investissement_initial


def delai_recuperation(lignes: Sequence[LigneAnnee]) -> Optional[float]:
    """Délai de récupération du capital investi (actualisé), en années.

    Le résultat est interpolé linéairement dans l'année de bascule du cumul.
    Renvoie ``None`` si le cumul actualisé reste négatif en fin de projet.
    """
    if not lignes:
        return None
    if lignes[0].cumul_actualise >= 0.0:
        return 0.0

    for index in range(1, len(lignes)):
        ligne = lignes[index]
        precedente = lignes[index - 1]
        if ligne.cumul_actualise >= 0.0 and ligne.flux_actualise > 0.0:
            fraction = -precedente.cumul_actualise / ligne.flux_actualise
            fraction = max(0.0, min(1.0, fraction))
            return precedente.annee + fraction
    return None


# --------------------------------------------------------------------------
# Analyse complète
# --------------------------------------------------------------------------


def analyser(projet: Projet) -> Resultat:
    """Calcule l'ensemble des indicateurs d'un projet supposé valide."""
    lignes = construire_lignes(projet)
    somme_flux_actualises = sum(l.flux_actualise for l in lignes[1:])
    somme_flux = sum(l.flux for l in lignes[1:])
    van = -float(projet.investissement_initial) + somme_flux_actualises

    return Resultat(
        projet=projet,
        lignes=lignes,
        van=van,
        somme_flux_actualises=somme_flux_actualises,
        somme_flux=somme_flux,
        van_taux_nul=-float(projet.investissement_initial) + somme_flux,
        tri=taux_rentabilite_interne(projet.investissement_initial, projet.flux),
        indice_rentabilite=indice_rentabilite(
            projet.investissement_initial, somme_flux_actualises
        ),
        delai_recuperation=delai_recuperation(lignes),
    )


def interpreter(van: float) -> Dict[str, str]:
    """Interprétation automatique d'une VAN (texte pédagogique en français)."""
    if van > TOLERANCE_VAN_NULLE:
        return {
            "statut": "positive",
            "titre": "VAN positive : le projet crée de la valeur",
            "message": (
                "La VAN est positive. Le projet rembourse intégralement le "
                "capital investi, le rémunère au taux d'actualisation retenu, "
                "et dégage en plus un surplus de valeur exprimé en euros "
                "d'aujourd'hui. Au regard du critère de la VAN, le projet est "
                "acceptable et peut être retenu."
            ),
        }
    if van < -TOLERANCE_VAN_NULLE:
        return {
            "statut": "negative",
            "titre": "VAN négative : le projet détruit de la valeur",
            "message": (
                "La VAN est négative. Les flux de trésorerie générés, une fois "
                "actualisés, ne permettent pas de récupérer le capital investi "
                "et de le rémunérer au taux exigé. Au regard du critère de la "
                "VAN, le projet est à rejeter, sauf motif stratégique non "
                "financier dûment justifié."
            ),
        }
    return {
        "statut": "nulle",
        "titre": "VAN nulle : le projet est à l'équilibre",
        "message": (
            "La VAN est nulle (aux arrondis près). Le projet rembourse "
            "exactement le capital investi et le rémunère au taux "
            "d'actualisation retenu, mais ne dégage aucun surplus de valeur. "
            "Financièrement, il y a indifférence : la décision doit se prendre "
            "sur des critères qualitatifs (risque, stratégie, impacts "
            "environnementaux)."
        ),
    }


def profil_van(
    investissement_initial: float,
    flux: Sequence[float],
    taux_max: float = 0.5,
    nb_points: int = 80,
) -> Tuple[List[float], List[float]]:
    """Courbe de la VAN en fonction du taux d'actualisation."""
    if nb_points < 2:
        nb_points = 2
    taux = [taux_max * i / (nb_points - 1) for i in range(nb_points)]
    valeurs = [calculer_van(investissement_initial, t, flux) for t in taux]
    return taux, valeurs


# --------------------------------------------------------------------------
# Sérialisation (utilisée par l'historique)
# --------------------------------------------------------------------------


def projet_vers_dict(projet: Projet) -> Dict[str, Any]:
    """Convertit un projet en dictionnaire sérialisable en JSON."""
    return {
        "identifiant": projet.identifiant,
        "nom": projet.nom,
        "investissement_initial": float(projet.investissement_initial),
        "taux_actualisation": float(projet.taux_actualisation),
        "flux": [float(f) for f in projet.flux],
        "date_creation": projet.date_creation,
        "origine": projet.origine,
    }


def projet_depuis_dict(donnees: Dict[str, Any]) -> Optional[Projet]:
    """Reconstruit un projet depuis un dictionnaire (robuste aux données invalides).

    Renvoie ``None`` si l'enregistrement est inexploitable.
    """
    if not isinstance(donnees, dict):
        return None
    try:
        i0 = float(donnees["investissement_initial"])
        taux = float(donnees["taux_actualisation"])
        flux = [float(f) for f in donnees.get("flux", [])]
    except (KeyError, TypeError, ValueError):
        return None

    if math.isnan(i0) or math.isnan(taux) or any(math.isnan(f) for f in flux):
        return None
    if not flux or taux <= -1.0:
        return None

    return Projet(
        nom=str(donnees.get("nom", "Projet sans nom")),
        investissement_initial=i0,
        taux_actualisation=taux,
        flux=flux,
        identifiant=str(donnees.get("identifiant", "")),
        date_creation=str(donnees.get("date_creation", "")),
        origine=str(donnees.get("origine", "")),
    )
