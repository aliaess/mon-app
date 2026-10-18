"""Page « Historique » : consultation, recherche et gestion des calculs conservés."""

from __future__ import annotations

from typing import Dict, List

import streamlit as st

from . import donnees, etat, finance, graphiques, presentation as pres

CLE_SUPPRESSION = "suppression_en_attente"
CLE_VIDAGE = "vidage_en_attente"


def _barre_outils(entrees: List[Dict[str, object]]) -> List[Dict[str, object]]:
    """Recherche, tri et gestion globale de l'historique."""
    with st.container(border=True):
        st.markdown("#### Rechercher et trier")
        colonne_recherche, colonne_tri, colonne_ordre = st.columns([2.2, 1.3, 1.2])
        with colonne_recherche:
            terme = st.text_input(
                "Rechercher un projet",
                placeholder="Saisissez tout ou partie du nom…",
                key="recherche_historique",
            )
        with colonne_tri:
            critere = st.selectbox(
                "Trier par",
                ["Date d'enregistrement", "Nom", "VAN", "Investissement initial"],
                key="tri_historique",
            )
        with colonne_ordre:
            ordre = st.selectbox(
                "Ordre",
                ["Décroissant", "Croissant"],
                key="ordre_historique",
            )

    resultats = donnees.rechercher(entrees, terme)

    def valeur_van(entree: Dict[str, object]) -> float:
        resultat = etat.resultat_depuis_entree(entree)
        if resultat is not None:
            return resultat.van
        valeur = entree.get("van_enregistree")
        return float(valeur) if isinstance(valeur, (int, float)) else 0.0

    inverse = ordre == "Décroissant"
    if critere == "Nom":
        resultats = sorted(resultats, key=lambda e: str(e.get("nom", "")).lower(), reverse=inverse)
    elif critere == "VAN":
        resultats = sorted(resultats, key=valeur_van, reverse=inverse)
    elif critere == "Investissement initial":
        resultats = sorted(
            resultats,
            key=lambda e: float(e.get("investissement_initial", 0.0)),
            reverse=inverse,
        )
    else:
        resultats = sorted(
            resultats, key=lambda e: str(e.get("date_creation", "")), reverse=inverse
        )
    return resultats


def _statistiques(entrees: List[Dict[str, object]]) -> None:
    resultats = [etat.resultat_depuis_entree(e) for e in entrees]
    resultats = [r for r in resultats if r is not None]
    if not resultats:
        return

    van_max = max(r.van for r in resultats)
    positifs = sum(1 for r in resultats if r.est_positive)
    taux_moyen = sum(r.projet.taux_actualisation for r in resultats) / len(resultats)

    colonne_total, colonne_meilleure, colonne_positifs, colonne_taux = st.columns(4)
    colonne_total.metric("Calculs enregistrés", len(entrees))
    colonne_meilleure.metric(
        "Meilleure VAN",
        pres.formater_montant_signe(van_max)
        if van_max > 0
        else pres.formater_montant(van_max),
        help="VAN la plus élevée parmi tous les calculs conservés.",
    )
    colonne_positifs.metric(
        "Projets à VAN positive",
        f"{positifs} / {len(resultats)}",
        help="Nombre de projets qui créent de la valeur au taux qui leur est affecté.",
    )
    colonne_taux.metric("Taux moyen retenu", pres.formater_pourcentage(taux_moyen))


def _detail_entree(entree: Dict[str, object]) -> None:
    identifiant = str(entree.get("identifiant", ""))
    resultat = etat.resultat_depuis_entree(entree)
    if resultat is None:
        st.warning("Cet enregistrement est incomplet et ne peut pas être analysé.")
        return

    symbole = pres.devise()
    projet = resultat.projet

    colonnes = st.columns(4)
    colonnes[0].metric("Investissement initial", pres.formater_montant(projet.investissement_initial, symbole=symbole))
    colonnes[1].metric("Taux retenu", pres.formater_pourcentage(projet.taux_actualisation))
    colonnes[2].metric("VAN", pres.formater_montant_signe(resultat.van, symbole=symbole))
    colonnes[3].metric(
        "TRI",
        pres.formater_pourcentage(resultat.tri) if resultat.tri is not None else "Non calculable",
    )

    commentaire = str(entree.get("commentaire", "")).strip()
    if commentaire:
        st.caption(f"Commentaire : {commentaire}")

    entetes = [
        ("Année", ""),
        (f"Flux ({symbole})", "nombre"),
        ("Coefficient", "nombre"),
        (f"Flux actualisé ({symbole})", "nombre"),
        (f"Cumul ({symbole})", "nombre"),
    ]
    lignes = []
    for ligne in resultat.lignes:
        lignes.append(
            (
                [
                    "0" if ligne.annee == 0 else str(ligne.annee),
                    pres.formater_montant_signe(ligne.flux, symbole=symbole),
                    pres.formater_facteur(ligne.facteur),
                    pres.formater_montant_signe(ligne.flux_actualise, symbole=symbole),
                    pres.formater_montant_signe(ligne.cumul_actualise, symbole=symbole),
                ],
                ["", "nombre", "nombre", "nombre", "nombre"],
                "",
            )
        )
    st.markdown(
        pres.tableau_html(entetes, lignes, hauteur_max=340), unsafe_allow_html=True
    )

    st.write("")
    colonne_recharger, colonne_comparer, colonne_supprimer = st.columns([1.3, 1.3, 1.0])

    with colonne_recharger:
        if st.button(
            "Recharger dans le calculateur",
            key=f"recharger_{identifiant}",
            icon="🧮",
            width="stretch",
        ):
            etat.charger_dans_calculateur(projet)
            etat.aller_vers("calculateur")

    with colonne_comparer:
        dans_panier = identifiant in etat.panier()
        if st.button(
            "Retirer du comparateur" if dans_panier else "Ajouter au comparateur",
            key=f"comparer_{identifiant}",
            icon="⚖️",
            width="stretch",
        ):
            ajoute = etat.basculer_panier(identifiant)
            st.toast(
                "Projet ajouté au comparateur." if ajoute else "Projet retiré du comparateur.",
                icon="⚖️",
            )
            st.rerun()

    with colonne_supprimer:
        if st.button(
            "Supprimer",
            key=f"supprimer_{identifiant}",
            icon="🗑️",
            width="stretch",
        ):
            st.session_state[CLE_SUPPRESSION] = identifiant

    if st.session_state.get(CLE_SUPPRESSION) == identifiant:
        st.warning(f"Confirmer la suppression définitive de « {projet.nom} » ?")
        colonne_oui, colonne_non, _ = st.columns([1.0, 1.0, 2.0])
        with colonne_oui:
            if st.button(
                "Oui, supprimer",
                key=f"confirmer_{identifiant}",
                type="primary",
                width="stretch",
            ):
                donnees.supprimer_entree(identifiant)
                if identifiant in etat.panier():
                    etat.basculer_panier(identifiant)
                st.session_state[CLE_SUPPRESSION] = None
                st.toast("Enregistrement supprimé.", icon="🗑️")
                st.rerun()
        with colonne_non:
            if st.button(
                "Annuler", key=f"annuler_{identifiant}", width="stretch"
            ):
                st.session_state[CLE_SUPPRESSION] = None
                st.rerun()


def _gestion_fichier(entrees: List[Dict[str, object]]) -> None:
    with st.container(border=True):
        st.markdown("#### Sauvegarde et transfert")
        st.caption(
            f"Les calculs sont enregistrés dans le fichier "
            f"« {donnees.chemin_historique()} ». Vous pouvez l'exporter pour "
            f"l'archiver ou le transmettre, puis le réimporter plus tard."
        )

        colonne_export, colonne_import = st.columns(2)

        with colonne_export:
            st.download_button(
                "Exporter tout l'historique (JSON)",
                data=donnees.exporter_texte(list(entrees)),
                file_name="van-historique.json",
                mime="application/json",
                icon="⬇️",
                width="stretch",
                disabled=not entrees,
            )

        with colonne_import:
            fichier = st.file_uploader(
                "Importer un fichier JSON",
                type=["json"],
                key="import_historique",
                help="Les projets importés sont ajoutés à l'historique existant.",
            )
            if fichier is not None:
                try:
                    texte = fichier.getvalue().decode("utf-8")
                except UnicodeDecodeError:
                    texte = ""
                    st.error("Le fichier doit être encodé en UTF-8.")

                if texte:
                    valides, erreurs = donnees.importer_texte(texte)
                    for erreur in erreurs:
                        st.warning(erreur)
                    if valides:
                        st.info(f"{len(valides)} projet(s) prêt(s) à être importé(s).")
                        if st.button("Confirmer l'import", type="primary", width="stretch"):
                            existants = {e.get("identifiant") for e in entrees}
                            nouveaux = [
                                e for e in valides if e.get("identifiant") not in existants
                            ]
                            _, succes, message = donnees.sauvegarder_historique(
                                nouveaux + list(entrees)
                            )
                            if succes:
                                st.success(f"{len(nouveaux)} projet(s) importé(s).")
                                st.rerun()
                            else:
                                st.error(message)

        if entrees:
            st.write("")
            if st.button("Vider entièrement l'historique", icon="🧹"):
                st.session_state[CLE_VIDAGE] = True

            if st.session_state.get(CLE_VIDAGE):
                st.warning(
                    "Cette action supprime définitivement tous les calculs enregistrés."
                )
                colonne_oui, colonne_non, _ = st.columns([1.2, 1.2, 2.0])
                with colonne_oui:
                    if st.button(
                        "Oui, tout supprimer", type="primary", width="stretch"
                    ):
                        donnees.vider_historique()
                        etat.vider_panier()
                        st.session_state[CLE_VIDAGE] = False
                        st.session_state["selection_comparaison"] = []
                        st.toast("Historique vidé.", icon="🧹")
                        st.rerun()
                with colonne_non:
                    if st.button("Annuler", width="stretch"):
                        st.session_state[CLE_VIDAGE] = False
                        st.rerun()


def rendre() -> None:
    pres.bandeau(
        "Historique des calculs",
        "Retrouvez tous les projets analysés, rechargez-les dans le calculateur ou "
        "comparez-les entre eux.",
        etiquette="VAN Project Analyzer",
    )
    st.write("")

    entrees = etat.historique()

    if not entrees:
        pres.encadre(
            "Aucun calcul enregistré pour l'instant",
            "Rendez-vous dans le calculateur, saisissez les hypothèses d'un projet "
            "puis cliquez sur « Enregistrer dans l'historique ». Vous pouvez aussi "
            "charger les exemples de démonstration pour explorer cette page "
            "immédiatement.",
            ton="neutre",
        )
        st.write("")
        colonne_exemple, _ = st.columns([1.6, 2.4])
        with colonne_exemple:
            if st.button(
                "Charger les 3 exemples de démonstration", icon="📥", width="stretch"
            ):
                ajoutes = donnees.charger_exemples_dans_historique()
                st.success(
                    f"{ajoutes} projet(s) de démonstration ajouté(s)."
                    if ajoutes
                    else "Les exemples sont déjà présents dans l'historique."
                )
                st.rerun()
        st.stop()
        return

    _statistiques(entrees)

    st.write("")
    pres.titre_section(
        "Répartition des VAN enregistrées",
        "vert : création de valeur · rouge : destruction de valeur",
    )
    entrees_pour_graphique = []
    for entree in entrees:
        resultat = etat.resultat_depuis_entree(entree)
        if resultat is not None:
            entrees_pour_graphique.append(
                {"nom": resultat.projet.nom, "van_enregistree": resultat.van}
            )
    if entrees_pour_graphique:
        st.plotly_chart(
            graphiques.graphique_historique_van(entrees_pour_graphique),
            use_container_width=True,
            key="graphique_historique",
        )

    st.write("")
    pres.titre_section("Calculs conservés")
    resultats = _barre_outils(entrees)

    if not resultats:
        st.info("Aucun projet ne correspond à votre recherche.")
    else:
        st.caption(f"{len(resultats)} projet(s) affiché(s) sur {len(entrees)}.")
        for entree in resultats:
            identifiant = str(entree.get("identifiant", ""))
            resultat = etat.resultat_depuis_entree(entree)
            nom = str(entree.get("nom", "Projet sans nom"))
            date = str(entree.get("date_creation", ""))
            etiquette = ""
            if str(entree.get("origine", "")) == donnees.ORIGINE_EXEMPLE:
                etiquette = pres.etiquette("Exemple", "exemple")
            if resultat is not None:
                couleur = pres.couleur_van(resultat.van)
                titre = (
                    f"{nom}  ·  {date}  ·  VAN "
                    f"{pres.formater_montant_signe(resultat.van)}"
                )
            else:
                titre = f"{nom}  ·  {date}"

            with st.expander(titre, expanded=False):
                if etiquette:
                    st.markdown(etiquette, unsafe_allow_html=True)
                    st.caption(
                        "Enregistrement initialisé depuis l'exemple de démonstration "
                        "de l'application."
                    )
                _detail_entree(entree)

    st.write("")
    _gestion_fichier(entrees)
