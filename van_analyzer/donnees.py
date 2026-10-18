"""Persistance locale de l'historique et jeux de données de démonstration.

L'application ne possède **aucun serveur ni base de données** : l'historique est
écrit dans un simple fichier JSON situé dans le dossier du projet
(``.van_data/historique.json``). Il est donc conservé d'une session à l'autre,
y compris après actualisation de la page ou redémarrage de l'application.

L'utilisateur peut en outre exporter et réimporter ce fichier depuis la page
« Historique » pour sauvegarder ou transférer ses travaux.
"""

from __future__ import annotations

import json
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from . import finance

# --------------------------------------------------------------------------
# Emplacement du fichier de données
# --------------------------------------------------------------------------

DOSSIER_DONNEES = Path(__file__).resolve().parent.parent / ".van_data"
FICHIER_HISTORIQUE = DOSSIER_DONNEES / "historique.json"


def chemin_historique() -> Path:
    """Chemin du fichier JSON utilisé pour conserver l'historique."""
    return FICHIER_HISTORIQUE


# --------------------------------------------------------------------------
# Lecture / écriture
# --------------------------------------------------------------------------


def charger_historique() -> List[Dict[str, Any]]:
    """Lit l'historique sur le disque.

    Renvoie une liste vide si le fichier n'existe pas ou s'il est illisible.
    Un fichier corrompu est sauvegardé sous ``historique_corrompu.json`` afin
    de ne jamais perdre silencieusement le travail de l'utilisateur.
    """
    if not FICHIER_HISTORIQUE.exists():
        return []

    try:
        contenu = FICHIER_HISTORIQUE.read_text(encoding="utf-8")
        donnees = json.loads(contenu)
    except (OSError, json.JSONDecodeError):
        _sauvegarder_copie_corrompue()
        return []

    if not isinstance(donnees, list):
        return []

    # On ne conserve que les enregistrements exploitables.
    entrees: List[Dict[str, Any]] = []
    for enregistrement in donnees:
        projet = finance.projet_depuis_dict(enregistrement)
        if projet is not None:
            entrees.append(enregistrement)
    return entrees


def _sauvegarder_copie_corrompue() -> None:
    try:
        DOSSIER_DONNEES.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(
            FICHIER_HISTORIQUE, DOSSIER_DONNEES / "historique_corrompu.json"
        )
    except OSError:
        pass


def sauvegarder_historique(entrees: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """Écrit l'historique de façon atomique. Renvoie ``(succès, message)``."""
    try:
        DOSSIER_DONNEES.mkdir(parents=True, exist_ok=True)
        temporaire = FICHIER_HISTORIQUE.with_suffix(".json.tmp")
        temporaire.write_text(
            json.dumps(entrees, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        os.replace(temporaire, FICHIER_HISTORIQUE)
        return True, ""
    except OSError as erreur:
        return False, f"Impossible d'écrire l'historique : {erreur}"


# --------------------------------------------------------------------------
# Manipulation des entrées
# --------------------------------------------------------------------------


def creer_entree(projet: finance.Projet, resultat: finance.Resultat) -> Dict[str, Any]:
    """Construit un enregistrement d'historique à partir d'un projet analysé."""
    entree = finance.projet_vers_dict(projet)
    entree["identifiant"] = projet.identifiant or uuid.uuid4().hex[:12]
    entree["date_creation"] = projet.date_creation or datetime.now().strftime(
        "%Y-%m-%d %H:%M"
    )
    # Indicateurs figés au moment de l'enregistrement (traçabilité).
    entree["van_enregistree"] = round(resultat.van, 2)
    entree["tri_enregistre"] = (
        round(resultat.tri * 100, 4) if resultat.tri is not None else None
    )
    return entree


def ajouter_entree(entree: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], bool, str]:
    """Ajoute un enregistrement en tête de l'historique et le sauvegarde."""
    entrees = charger_historique()
    entrees = [e for e in entrees if e.get("identifiant") != entree.get("identifiant")]
    entrees.insert(0, entree)
    succes, message = sauvegarder_historique(entrees)
    return entrees, succes, message


def supprimer_entree(identifiant: str) -> Tuple[List[Dict[str, Any]], bool, str]:
    """Supprime un enregistrement de l'historique."""
    entrees = [e for e in charger_historique() if e.get("identifiant") != identifiant]
    succes, message = sauvegarder_historique(entrees)
    return entrees, succes, message


def vider_historique() -> Tuple[bool, str]:
    """Efface tout l'historique."""
    return sauvegarder_historique([])


def rechercher(entrees: List[Dict[str, Any]], terme: str) -> List[Dict[str, Any]]:
    """Filtre les enregistrements dont le nom contient ``terme``."""
    terme = (terme or "").strip().lower()
    if not terme:
        return list(entrees)
    return [e for e in entrees if terme in str(e.get("nom", "")).lower()]


def trouver(entrees: List[Dict[str, Any]], identifiant: str) -> Optional[Dict[str, Any]]:
    for entree in entrees:
        if entree.get("identifiant") == identifiant:
            return entree
    return None


# --------------------------------------------------------------------------
# Import / export
# --------------------------------------------------------------------------


def exporter_texte(entrees: List[Dict[str, Any]]) -> str:
    """Sérialise l'historique en JSON lisible."""
    return json.dumps(entrees, ensure_ascii=False, indent=2)


def importer_texte(texte: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Analyse un fichier JSON importé.

    Renvoie ``(entrées_valides, erreurs)``.
    """
    erreurs: List[str] = []
    try:
        donnees = json.loads(texte)
    except json.JSONDecodeError:
        return [], ["Le fichier importé n'est pas un JSON valide."]

    if isinstance(donnees, dict) and "historique" in donnees:
        donnees = donnees["historique"]
    if not isinstance(donnees, list):
        return [], ["Le fichier importé doit contenir une liste de projets."]

    valides: List[Dict[str, Any]] = []
    for position, enregistrement in enumerate(donnees, start=1):
        projet = finance.projet_depuis_dict(enregistrement)
        if projet is None:
            erreurs.append(f"Entrée {position} ignorée : données incomplètes ou invalides.")
            continue
        if not enregistrement.get("identifiant"):
            enregistrement["identifiant"] = uuid.uuid4().hex[:12]
        if not enregistrement.get("date_creation"):
            enregistrement["date_creation"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        valides.append(enregistrement)

    return valides, erreurs


# --------------------------------------------------------------------------
# Exemples de démonstration
# --------------------------------------------------------------------------
# Ces trois projets sont fournis à titre pédagogique. Ils sont explicitement
# signalés comme exemples dans l'interface et dans l'historique : il ne s'agit
# jamais de résultats présentés comme issus des calculs de l'utilisateur.

ORIGINE_EXEMPLE = "exemple"

PROJETS_DEMONSTRATION: List[Dict[str, Any]] = [
    {
        "nom": "Projet A — Atelier de production",
        "investissement_initial": 1000.0,
        "taux_actualisation": 0.10,
        "flux": [500.0, 500.0, 500.0],
        "origine": ORIGINE_EXEMPLE,
    },
    {
        "nom": "Projet B — Ligne automatisée",
        "investissement_initial": 1000.0,
        "taux_actualisation": 0.10,
        "flux": [100.0, 600.0, 900.0],
        "origine": ORIGINE_EXEMPLE,
    },
    {
        "nom": "Projet C — Rénovation énergétique",
        "investissement_initial": 1000.0,
        "taux_actualisation": 0.10,
        "flux": [300.0, 300.0, 300.0],
        "origine": ORIGINE_EXEMPLE,
    },
]

#: Projet utilisé comme exemple numérique corrigé dans le guide pédagogique.
EXEMPLE_PEDAGOGIQUE: Dict[str, Any] = {
    "nom": "Exemple — Atelier de production",
    "investissement_initial": 1000.0,
    "taux_actualisation": 0.10,
    "flux": [500.0, 500.0, 500.0],
    "origine": ORIGINE_EXEMPLE,
}


def exemple_en_projet(exemple: Dict[str, Any], horodatage: bool = True) -> finance.Projet:
    """Convertit un exemple en objet :class:`finance.Projet`."""
    projet = finance.Projet(
        nom=exemple["nom"],
        investissement_initial=float(exemple["investissement_initial"]),
        taux_actualisation=float(exemple["taux_actualisation"]),
        flux=[float(f) for f in exemple["flux"]],
        identifiant=uuid.uuid4().hex[:12],
        date_creation=datetime.now().strftime("%Y-%m-%d %H:%M") if horodatage else "",
        origine=str(exemple.get("origine", ORIGINE_EXEMPLE)),
    )
    return projet


def charger_exemples_dans_historique() -> int:
    """Ajoute les projets de démonstration à l'historique. Renvoie le nombre ajouté."""
    entrees = charger_historique()
    existants = {e.get("nom") for e in entrees}
    ajoutes = 0
    for exemple in PROJETS_DEMONSTRATION:
        if exemple["nom"] in existants:
            continue
        projet = exemple_en_projet(exemple)
        resultat = finance.analyser(projet)
        entrees.insert(0, creer_entree(projet, resultat))
        ajoutes += 1
    if ajoutes:
        sauvegarder_historique(entrees)
    return ajoutes
