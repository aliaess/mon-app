"""Page « Comparaison des projets » : classement et arbitrage entre plusieurs projets."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import streamlit as st

from . import donnees, etat, finance, graphiques, presentation as pres


def _libelle_entree(entree: Dict[str, object]) -> str:
    """Libellé lisible d'un enregistrement d'historique."""
    nom = str(entree.get("nom", "Projet"))
    date = str(entree.get("date_creation", "")) or "sans date"
    van = entree.get("van_enregistree")
    if isinstance(van, (int, float)):
        return f"{nom} · {date} · VAN {pres.formater_montant(float(van))}"
    return f"{nom} · {date}"


def _ajouter_exemples() -> None:
    """Callback : ajoute les projets fictifs à l'historique puis les sélectionne.

    Un callback est nécessaire — et non un ``if st.button(...)`` suivi d'une
    affectation — car Streamlit interdit d'écrire dans la clé d'un widget
    (ici le multiselect de sélection) une fois ce widget instancié. Le callback
    s'exécute avant le script, donc avant la création du multiselect.
    """
    ajoutes = donnees.charger_exemples_dans_historique()
    noms_exemples = {projet["nom"] for projet in donnees.PROJETS_DEMONSTRATION}
    identifiants = [
        str(entree.get("identifiant", ""))
        for entree in etat.historique()
        if str(entree.get("nom", "")) in noms_exemples
    ]
    _appliquer_selection(identifiants)
    if ajoutes:
        st.toast(f"{ajoutes} projet(s) de démonstration ajouté(s) à l'historique.")


def _tout_selectionner() -> None:
    """Callback : sélectionne tous les projets de l'historique."""
    _appliquer_selection(
        [str(entree.get("identifiant", "")) for entree in etat.historique()]
    )


def _tout_deselectionner() -> None:
    """Callback : vide la sélection."""
    _appliquer_selection([])


def _appliquer_selection(identifiants: List[str]) -> None:
    st.session_state["selection_comparaison"] = identifiants
    etat.definir_panier(identifiants)


def _selection(entrees: List[Dict[str, object]]) -> Tuple[List[Dict[str, object]], Optional[float]]:
    """Sélection des projets à comparer et choix des hypothèses de taux."""
    with st.container(border=True):
        st.markdown("#### 1 · Projets à comparer")
        if not entrees:
            st.info(
                "Aucun projet enregistré pour le moment. Enregistrez des projets depuis "
                "le calculateur, ou chargez les exemples de démonstration ci-dessous."
            )
            colonne_exemple, _ = st.columns([1.6, 2.4])
            with colonne_exemple:
                st.button(
                    "Charger les 3 exemples de démonstration",
                    icon="📥",
                    width="stretch",
                    on_click=_ajouter_exemples,
                    help="Ajoute les projets fictifs A, B et C puis les sélectionne.",
                )
            return [], None

        identifiants = [str(e.get("identifiant", "")) for e in entrees]
        libelles = {str(e.get("identifiant", "")): _libelle_entree(e) for e in entrees}
        par_defaut = [identifiant for identifiant in etat.panier() if identifiant in identifiants]

        selection = st.multiselect(
            "Sélectionnez au moins deux projets",
            options=identifiants,
            default=par_defaut,
            format_func=lambda identifiant: libelles.get(identifiant, identifiant),
            key="selection_comparaison",
            placeholder="Choisissez des projets dans la liste…",
            help="Les projets proviennent de l'historique. Cochez ceux à mettre en regard.",
        )
        etat.definir_panier(selection)

        taux_commun: Optional[float] = None
        colonne_toggle, colonne_taux, colonne_info = st.columns([2.3, 1.0, 2.0])
        with colonne_toggle:
            appliquer = st.toggle(
                "Imposer un taux d'actualisation commun",
                key=etat.CLE_TAUX_COMMUN,
                help=(
                    "Indispensable pour comparer des projets de façon cohérente : "
                    "tous les projets doivent être jugés au même taux exigé."
                ),
            )
        with colonne_taux:
            if appliquer:
                taux_pourcentage = st.number_input(
                    "Taux commun (%)",
                    key=etat.CLE_TAUX_COMMUN_VALEUR,
                    step=0.5,
                    format="%.2f",
                    min_value=-99.0,
                    max_value=1000.0,
                )
                taux_commun = float(taux_pourcentage) / 100.0
        with colonne_info:
            if appliquer:
                st.caption(
                    "Tous les projets sont réévalués au même taux : seul leur "
                    "échelonnement de flux les distingue encore."
                )
            else:
                st.caption(
                    "Chaque projet conserve le taux qui lui a été affecté. "
                    "La comparaison reste possible, mais des taux différents "
                    "faussent le classement."
                )

        colonnes_boutons = st.columns([1.15, 1.55, 2.3])
        with colonnes_boutons[0]:
            st.button(
                "Tout sélectionner",
                width="stretch",
                on_click=_tout_selectionner,
            )
        with colonnes_boutons[1]:
            st.button(
                "Tout désélectionner",
                width="stretch",
                on_click=_tout_deselectionner,
            )
        with colonnes_boutons[2]:
            # Reste disponible même lorsque l'historique contient déjà des
            # projets : l'utilisateur peut ainsi essayer la page à tout moment.
            st.button(
                "Ajouter les exemples de démonstration",
                icon="📥",
                width="stretch",
                on_click=_ajouter_exemples,
                help=(
                    "Ajoute les trois projets fictifs (A, B et C) à l'historique, "
                    "s'ils n'y figurent pas déjà, puis les sélectionne."
                ),
            )

    selection_entrees = [
        e for e in entrees if str(e.get("identifiant", "")) in set(selection)
    ]
    return selection_entrees, taux_commun


def _tableau_comparatif(resultats: List[finance.Resultat]) -> None:
    symbole = pres.devise()
    entetes = [
        ("Projet", ""),
        ("Investissement initial", "nombre"),
        ("Taux retenu", "nombre"),
        ("VAN", "nombre"),
        ("TRI", "nombre"),
        ("Indice de rentabilité", "nombre"),
        ("Délai de récupération", "nombre"),
    ]

    lignes = []
    for rang, resultat in enumerate(resultats, start=1):
        couleur_van = pres.couleur_van(resultat.van)
        lignes.append(
            (
                [
                    f'<b>{rang}. {pres.echapper(resultat.projet.nom)}</b>'
                    + (
                        " " + pres.etiquette("Exemple", "exemple")
                        if resultat.projet.est_exemple
                        else ""
                    ),
                    pres.formater_montant(resultat.projet.investissement_initial, symbole=symbole),
                    pres.formater_pourcentage(resultat.projet.taux_actualisation),
                    f'<span style="color:{couleur_van};font-weight:700">'
                    f"{pres.formater_montant_signe(resultat.van, symbole=symbole)}</span>",
                    pres.formater_pourcentage(resultat.tri)
                    if resultat.tri is not None
                    else "aucun TRI",
                    pres.formater_nombre(resultat.indice_rentabilite, 2)
                    if resultat.indice_rentabilite is not None
                    else "—",
                    pres.formater_duree(resultat.delai_recuperation),
                ],
                ["", "nombre", "nombre", "nombre", "nombre", "nombre", "nombre"],
                "",
            )
        )

    st.markdown(pres.tableau_html(entetes, lignes), unsafe_allow_html=True)
    st.caption(
        "Classement par VAN décroissante. Le TRI indique le taux maximal que le "
        "projet peut supporter ; le délai de récupération mesure le risque de "
        "liquidité. Aucun de ces trois indicateurs ne résume à lui seul la décision."
    )


def _synthese(resultats: List[finance.Resultat], taux_commun: Optional[float]) -> None:
    """Message d'arbitrage : qui gagne, et selon quel critère."""
    meilleur_van = max(resultats, key=lambda r: r.van)
    van_max = meilleur_van.van

    if van_max <= 0:
        pres.encadre(
            "Aucun projet ne crée de valeur",
            "Tous les projets sélectionnés ont une VAN négative ou nulle au taux "
            "retenu. Au regard du critère de la VAN, aucun ne mérite d'être retenu : "
            "il vaut mieux conserver les fonds ou différer l'investissement. "
            "Vérifiez le taux exigé : un taux trop élevé peut à lui seul expliquer "
            "ce résultat.",
            ton="negatif",
        )
        return

    retenus = [r for r in resultats if r.est_positive]
    autres = [r for r in resultats if not r.est_positive]

    message = (
        f"Au taux retenu, le projet « {meilleur_van.projet.nom} » présente la VAN la "
        f"plus élevée : {pres.formater_montant_signe(van_max)}. "
        f"{len(retenus)} projet(s) sur {len(resultats)} créent de la valeur."
    )
    if autres:
        noms = ", ".join(r.projet.nom for r in autres)
        message += f" Projet(s) à écarter sur ce critère : {noms}."

    if taux_commun is None:
        message += (
            " Attention : les projets n'ont pas été évalués au même taux, le "
            "classement peut donc être trompeur. Activez le taux commun pour un "
            "arbitrage rigoureux."
        )

    avec_tri = [r for r in resultats if r.tri is not None]
    if len(avec_tri) >= 2:
        meilleur_tri = max(avec_tri, key=lambda r: r.tri or float("-inf"))
        if meilleur_tri.projet.nom != meilleur_van.projet.nom:
            message += (
                f" Le TRI le plus élevé est celui de « {meilleur_tri.projet.nom} » "
                f"({pres.formater_pourcentage(meilleur_tri.tri)}), ce qui contredit le "
                "classement par la VAN : cela signifie que ce projet est plus "
                "rentable par unité de temps, mais de taille plus modeste. La VAN "
                "reste le critère de référence pour maximiser la valeur créée."
            )

    pres.encadre("Arbitrage proposé", message, ton="positif")


def _detail_projet(resultat: finance.Resultat) -> None:
    symbole = pres.devise()
    entetes = [
        ("Année", ""),
        (f"Flux ({symbole})", "nombre"),
        ("Coefficient", "nombre"),
        (f"Flux actualisé ({symbole})", "nombre"),
        (f"Cumul ({symbole})", "nombre"),
    ]
    lignes = []
    for ligne in resultat.lignes:
        libelle = "0" if ligne.annee == 0 else str(ligne.annee)
        lignes.append(
            (
                [
                    libelle,
                    pres.formater_montant_signe(ligne.flux, symbole=symbole),
                    pres.formater_facteur(ligne.facteur),
                    pres.formater_montant_signe(ligne.flux_actualise, symbole=symbole),
                    pres.formater_montant_signe(ligne.cumul_actualise, symbole=symbole),
                ],
                ["", "nombre", "nombre", "nombre", "nombre"],
                "",
            )
        )
    st.markdown(pres.tableau_html(entetes, lignes), unsafe_allow_html=True)


def rendre() -> None:
    pres.bandeau(
        "Comparaison des projets",
        "Mettez plusieurs projets en regard, à hypothèses comparables, et appuyez "
        "votre décision sur des indicateurs calculés.",
        etiquette="VAN Project Analyzer",
    )
    st.write("")

    entrees = etat.historique()
    selection, taux_commun = _selection(entrees)

    if len(selection) < 2:
        st.write("")
        pres.encadre(
            "Sélectionnez au moins deux projets",
            "La comparaison nécessite au moins deux projets. Sélectionnez-les "
            "ci-dessus, ou enregistrez de nouveaux calculs depuis le calculateur "
            "VAN. Vous pouvez aussi charger les trois exemples de démonstration "
            "pour découvrir la page.",
            ton="neutre",
        )
        return

    resultats: List[finance.Resultat] = []
    for entree in selection:
        resultat = etat.resultat_depuis_entree(entree, taux_force=taux_commun)
        if resultat is not None:
            resultats.append(resultat)

    if len(resultats) < 2:
        pres.encadre(
            "Données insuffisantes",
            "Certains enregistrements sélectionnés sont incomplets et n'ont pas pu "
            "être analysés. Réenregistrez les projets concernés depuis le calculateur.",
            ton="attention",
        )
        return

    resultats.sort(key=lambda r: r.van, reverse=True)

    st.write("")
    pres.titre_section("Tableau comparatif", "classement par VAN décroissante")
    _tableau_comparatif(resultats)

    st.write("")
    _synthese(resultats, taux_commun)

    st.write("")
    pres.titre_section("VAN de chaque projet")
    st.plotly_chart(
        graphiques.graphique_comparaison_van(resultats),
        use_container_width=True,
        key="graphique_comparaison_van",
    )

    st.write("")
    pres.titre_section(
        "Profil de VAN : à quel taux le classement s'inverse-t-il ?",
        "chaque courbe atteint zéro au TRI du projet",
    )
    st.plotly_chart(
        graphiques.graphique_comparaison_profils(resultats),
        use_container_width=True,
        key="graphique_comparaison_profils",
    )
    st.caption(
        "Lorsque deux courbes se croisent, le classement des projets dépend du taux "
        "d'actualisation retenu. C'est pourquoi le taux exigé doit être fixé avant "
        "toute comparaison."
    )

    st.write("")
    pres.titre_section("Détail des calculs par projet")
    for resultat in resultats:
        with st.expander(
            f"{resultat.projet.nom} — VAN {pres.formater_montant_signe(resultat.van)}",
            expanded=False,
        ):
            st.caption(
                f"Investissement initial : "
                f"{pres.formater_montant(resultat.projet.investissement_initial)} · "
                f"Taux retenu : {pres.formater_pourcentage(resultat.projet.taux_actualisation)} · "
                f"Durée : {resultat.projet.duree} an(s)"
            )
            _detail_projet(resultat)
