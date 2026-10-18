"""Page « Calculateur VAN » : saisie des hypothèses et analyse complète du projet."""

from __future__ import annotations

from typing import List, Optional

import pandas as pd
import streamlit as st

from . import donnees, etat, finance, graphiques, presentation as pres


# --------------------------------------------------------------------------
# Blocs d'interface
# --------------------------------------------------------------------------


def _entete() -> None:
    pres.bandeau(
        "Calculateur VAN",
        "Renseignez les hypothèses du projet : la valeur actuelle nette se recalcule "
        "automatiquement, à chaque modification.",
        etiquette="VAN Project Analyzer",
    )
    st.write("")
    if st.session_state.get(etat.CLE_ORIGINE_CHARGEE) == donnees.ORIGINE_EXEMPLE:
        st.markdown(
            pres.etiquette("Valeurs initialisées depuis l'exemple de démonstration", "exemple"),
            unsafe_allow_html=True,
        )
        st.write("")


def _hypotheses() -> None:
    with st.container(border=True):
        st.markdown("#### 1 · Hypothèses du projet")
        st.caption(
            "Les quatre hypothèses ci-dessous définissent entièrement le projet. "
            "Utilisez le point ou la virgule comme séparateur décimal."
        )
        with st.container(key="hypotheses_projet"):
            colonne_nom, colonne_i0, colonne_taux, colonne_duree = st.columns(
                [2.3, 1.5, 1.3, 1.0]
            )
            with colonne_nom:
                st.text_input(
                    "Nom du projet",
                    key=etat.CLE_NOM,
                    placeholder="Ex. : Ouverture d'un second atelier",
                    help="Ce nom sera utilisé dans l'historique et dans les comparaisons.",
                )
            with colonne_i0:
                st.number_input(
                    f"Investissement initial I₀ ({pres.devise()})",
                    key=etat.CLE_INVESTISSEMENT,
                    step=100.0,
                    format="%.2f",
                    help=(
                        "Montant décaissé au démarrage (année 0). Un montant négatif "
                        "correspond à un encaissement initial (subvention, cession)."
                    ),
                )
            with colonne_taux:
                st.number_input(
                    "Taux d'actualisation (%)",
                    key=etat.CLE_TAUX,
                    step=0.5,
                    format="%.2f",
                    min_value=-99.0,
                    max_value=1000.0,
                    help=(
                        "Taux exigé par l'entreprise, exprimé en pourcentage. "
                        "Exemple : 10 pour 10 %."
                    ),
                )
            with colonne_duree:
                st.number_input(
                    "Durée (années)",
                    key=etat.CLE_DUREE,
                    min_value=finance.DUREE_MIN,
                    max_value=finance.DUREE_MAX,
                    step=1,
                    format="%d",
                    help=f"De {finance.DUREE_MIN} à {finance.DUREE_MAX} années.",
                )


def _editeur_flux() -> pd.DataFrame:
    with st.container(border=True):
        st.markdown("#### 2 · Flux de trésorerie de chaque année")
        st.caption(
            "Cliquez sur une cellule pour modifier un montant. Les montants négatifs "
            "(décaissements) sont acceptés, par exemple -2 500."
        )

        duree = int(st.session_state[etat.CLE_DUREE])
        cle = etat.cle_editeur(duree)

        tableau = st.data_editor(
            etat.dataframe_flux(etat.flux_source(duree)),
            key=cle,
            hide_index=True,
            width="stretch",
            num_rows="fixed",
            column_config={
                "Année": st.column_config.TextColumn("Année", disabled=True),
                "Flux de trésorerie": st.column_config.NumberColumn(
                    f"Flux de trésorerie ({pres.devise()})",
                    format="%.2f",
                    help="Encaissement net de l'année : recettes moins dépenses.",
                ),
            },
        )

        with st.expander("Outils de saisie rapide", expanded=False):
            colonne_montant, colonne_bouton = st.columns([1.2, 1.6])
            with colonne_montant:
                montant = st.number_input(
                    f"Montant à appliquer ({pres.devise()})",
                    value=0.0,
                    step=100.0,
                    format="%.2f",
                    key=etat.CLE_MONTANT_UNIFORME,
                )
            with colonne_bouton:
                st.write("")
                st.button(
                    "Appliquer ce montant à toutes les années",
                    width="stretch",
                    on_click=etat.appliquer_montant_uniforme,
                    help="Remplit la colonne des flux avec le montant saisi.",
                )

        colonne_exemple, colonne_reset, _ = st.columns([1.7, 1.2, 2.0])
        with colonne_exemple:
            st.button(
                "Charger l'exemple de démonstration",
                icon="📥",
                width="stretch",
                on_click=etat.charger_exemple,
                args=(donnees.EXEMPLE_PEDAGOGIQUE,),
                help=(
                    "Charge un projet fictif à but pédagogique : investissement de "
                    "1 000, taux de 10 %, flux de 500 par an pendant 3 ans."
                ),
            )
        with colonne_reset:
            st.button(
                "Réinitialiser",
                icon="♻️",
                width="stretch",
                on_click=etat.reinitialiser_calculateur,
                help="Efface la saisie en cours et remet les valeurs par défaut.",
            )
        st.caption(
            "L'exemple de démonstration est un jeu de données fictif, signalé comme "
            "tel : il ne provient pas d'un calcul réel."
        )
    return tableau


def _indicateurs(resultat: finance.Resultat) -> None:
    symbole = pres.devise()
    # Le conteneur porte une clé : la feuille de style s'en sert pour autoriser
    # le passage à la ligne des cartes lorsque la fenêtre est étroite.
    with st.container(key="cartes_resultats"):
        colonne_van, colonne_tri, colonne_ip, colonne_drci = st.columns(
            [1.55, 1.15, 1, 1.1], gap="small"
        )

        with colonne_van:
            if resultat.est_positive:
                ton = "positif"
            elif resultat.est_negative:
                ton = "negatif"
            else:
                ton = "neutre"
            pres.carte_van(
                pres.formater_montant_signe(resultat.van, symbole=symbole),
                pres.libelle_van(resultat.van),
                ton=ton,
            )

        with colonne_tri:
            st.metric(
                "Taux de rentabilité interne",
                pres.formater_pourcentage(resultat.tri)
                if resultat.tri is not None
                else "Non calculable",
                help=(
                    "Taux qui annule la VAN. Comparé au taux d'actualisation "
                    "exigé : si le TRI lui est supérieur, le projet est rentable."
                ),
            )
        with colonne_ip:
            st.metric(
                "Indice de rentabilité",
                pres.formater_nombre(resultat.indice_rentabilite, 2)
                if resultat.indice_rentabilite is not None
                else "—",
                help=(
                    "Flux actualisés divisés par l'investissement initial. "
                    "Supérieur à 1 : chaque unité investie rapporte plus qu'elle "
                    "ne coûte."
                ),
            )
        with colonne_drci:
            st.metric(
                "Délai de récupération",
                pres.formater_duree(resultat.delai_recuperation),
                help=(
                    "Durée au bout de laquelle le cumul des flux actualisés "
                    "devient positif (interpolation linéaire dans l'année)."
                ),
            )

    if resultat.tri is None:
        st.caption(
            "Le TRI n'existe pas dans l'intervalle analysé (-99,99 % à +1 000 %) : "
            "aucun taux ne permet d'annuler la VAN de ce projet. Aucune valeur n'est "
            "affichée plutôt qu'un résultat approximatif."
        )
    elif resultat.tri > 10.0:
        st.caption(
            "Le TRI dépasse 1 000 % : cette valeur extrême est à interpréter avec "
            "prudence (montants faibles ou horizon très court)."
        )


def _tableau_calculs(resultat: finance.Resultat) -> None:
    symbole = pres.devise()
    entetes = [
        ("Année", ""),
        (f"Flux de trésorerie ({symbole})", "nombre"),
        ("Coefficient d'actualisation", "nombre"),
        (f"Flux actualisé ({symbole})", "nombre"),
        (f"Cumul actualisé ({symbole})", "nombre"),
    ]

    lignes = []
    for ligne in resultat.lignes:
        libelle = "0 (investissement)" if ligne.annee == 0 else str(ligne.annee)
        couleur = pres.couleur_pour_van(ligne.cumul_actualise)
        lignes.append(
            (
                [
                    pres.echapper(libelle),
                    pres.formater_montant_signe(ligne.flux, symbole=symbole),
                    pres.formater_facteur(ligne.facteur),
                    pres.formater_montant_signe(ligne.flux_actualise, symbole=symbole),
                    f'<span style="color:{couleur};font-weight:600">'
                    f"{pres.formater_montant_signe(ligne.cumul_actualise, symbole=symbole)}</span>",
                ],
                ["", "nombre", "nombre", "nombre", "nombre"],
                "",
            )
        )

    lignes.append(
        (
            [
                "<b>Total</b>",
                f"<b>{pres.formater_montant_signe(resultat.somme_flux, symbole=symbole)}</b>",
                "",
                f"<b>{pres.formater_montant_signe(resultat.somme_flux_actualises, symbole=symbole)}</b>",
                f"<b>{pres.formater_montant_signe(resultat.van, symbole=symbole)}</b>",
            ],
            ["", "nombre", "nombre", "nombre", "nombre"],
            "total",
        )
    )

    st.markdown(
        pres.tableau_html(entetes, lignes, hauteur_max=460),
        unsafe_allow_html=True,
    )
    st.caption(
        "Le coefficient d'actualisation de l'année t vaut 1 / (1 + r)^t. "
        "La ligne « Total » du cumul actualisé correspond à la VAN."
    )


def _detail_calcul(resultat: finance.Resultat) -> None:
    """Déroule l'arithmétique de la VAN, étape par étape."""
    symbole = pres.devise()
    termes = [
        pres.formater_montant_signe(ligne.flux_actualise, symbole=symbole)
        for ligne in resultat.lignes[1:]
    ]
    if len(termes) > 8:
        affiches = termes[:4] + ["…"] + termes[-2:]
    else:
        affiches = termes

    st.markdown(
        f'<div class="formule">VAN = -I₀ + Σ [ CF<sub>t</sub> / (1 + r)<sup>t</sup> ]'
        f"<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;= -{pres.formater_montant(resultat.projet.investissement_initial, symbole=symbole)}"
        f" + {' + '.join(affiches)}"
        f"<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;= <b>{pres.formater_montant_signe(resultat.van, symbole=symbole)}</b></div>",
        unsafe_allow_html=True,
    )


def _bloc_enregistrement(projet: finance.Projet, resultat: finance.Resultat) -> None:
    with st.container(border=True):
        st.markdown("#### 4 · Conserver et exporter le calcul")
        st.caption(
            "Les calculs enregistrés sont conservés dans un fichier local sur votre "
            "machine et restent disponibles après actualisation de la page."
        )
        commentaire = st.text_input(
            "Commentaire (facultatif)",
            key="commentaire_projet",
            placeholder="Ex. : scénario pessimiste, taux relevé de 2 points",
        )

        colonne_enregistrer, colonne_comparer, colonne_export = st.columns([1.25, 1.25, 1.25])

        with colonne_enregistrer:
            if st.button(
                "Enregistrer dans l'historique",
                type="primary",
                icon="💾",
                width="stretch",
            ):
                entree = donnees.creer_entree(projet, resultat)
                entree["commentaire"] = (commentaire or "").strip()
                _, succes, message = donnees.ajouter_entree(entree)
                if succes:
                    st.success(
                        f"Projet « {projet.nom} » enregistré dans l'historique."
                    )
                else:
                    st.error(message)

        with colonne_comparer:
            if st.button(
                "Enregistrer et comparer",
                icon="⚖️",
                width="stretch",
                help=(
                    "Enregistre le projet puis ouvre la page de comparaison en le "
                    "présélectionnant."
                ),
            ):
                entree = donnees.creer_entree(projet, resultat)
                entree["commentaire"] = (commentaire or "").strip()
                entrees, succes, message = donnees.ajouter_entree(entree)
                if succes:
                    if entree["identifiant"] not in etat.panier():
                        etat.basculer_panier(entree["identifiant"])
                    etat.aller_vers("comparaison")
                else:
                    st.error(message)

        with colonne_export:
            st.download_button(
                "Exporter le tableau (CSV)",
                data=_tableau_vers_csv(projet, resultat),
                file_name=_nom_fichier(projet.nom),
                mime="text/csv",
                icon="⬇️",
                width="stretch",
                help=(
                    "Fichier CSV séparé par des points-virgules et utilisant la virgule "
                    "décimale : il s'ouvre directement dans Excel."
                ),
            )


def _nom_fichier(nom: str) -> str:
    propre = "".join(
        caractere if caractere.isalnum() else "-" for caractere in nom.lower().strip()
    )
    propre = "-".join(filtre for filtre in propre.split("-") if filtre) or "projet"
    return f"van-{propre}.csv"


def _tableau_vers_csv(projet: finance.Projet, resultat: finance.Resultat) -> str:
    lignes = [
        {
            "Année": ligne.annee,
            "Flux de trésorerie": round(ligne.flux, 6),
            "Coefficient d'actualisation": round(ligne.facteur, 8),
            "Flux actualisé": round(ligne.flux_actualise, 6),
            "Cumul actualisé": round(ligne.cumul_actualise, 6),
        }
        for ligne in resultat.lignes
    ]
    cadre = pd.DataFrame(lignes)
    entete = (
        f"Projet;{projet.nom}\n"
        f"Investissement initial;{projet.investissement_initial:.2f}\n"
        f"Taux d'actualisation (%);{projet.taux_pourcentage:.4f}\n"
        f"VAN;{resultat.van:.2f}\n"
    )
    return entete + cadre.to_csv(index=False, sep=";", decimal=",")


# --------------------------------------------------------------------------
# Rendu de la page
# --------------------------------------------------------------------------


def rendre() -> None:
    _entete()
    _hypotheses()
    tableau = _editeur_flux()

    nom = str(st.session_state.get(etat.CLE_NOM, ""))
    investissement = st.session_state.get(etat.CLE_INVESTISSEMENT, 0.0)
    taux = st.session_state.get(etat.CLE_TAUX, 0.0)
    flux = etat.flux_depuis_dataframe(tableau)

    erreurs, avertissements = finance.valider_saisie(
        nom, investissement, taux, flux
    )

    if erreurs:
        st.write("")
        pres.liste_encadre(
            "Le calcul ne peut pas être effectué",
            erreurs,
            ton="negatif",
        )
        if avertissements:
            pres.liste_encadre("Points à vérifier", avertissements, ton="attention")
        return

    projet = finance.Projet(
        nom=nom.strip(),
        investissement_initial=float(investissement),
        taux_actualisation=float(taux) / 100.0,
        flux=[float(valeur) for valeur in flux],
        origine=str(st.session_state.get(etat.CLE_ORIGINE_CHARGEE, "")),
    )
    resultat = finance.analyser(projet)

    if avertissements:
        pres.liste_encadre("Points à vérifier", avertissements, ton="attention")
        st.write("")

    st.markdown("#### 3 · Résultats de l'analyse")
    _indicateurs(resultat)

    st.write("")
    interpretation = finance.interpreter(resultat.van)
    correspondance = {"positive": "positif", "negative": "negatif", "nulle": "neutre"}
    pres.encadre(
        interpretation["titre"],
        interpretation["message"],
        ton=correspondance[interpretation["statut"]],
    )

    st.write("")
    pres.titre_section(
        "Flux de trésorerie et cumul actualisé",
        "barres : flux ; ligne : cumul des flux actualisés",
    )
    st.plotly_chart(
        graphiques.graphique_flux(resultat),
        use_container_width=True,
        key="graphique_flux_calculateur",
    )

    st.write("")
    pres.titre_section("Tableau détaillé des calculs")
    _tableau_calculs(resultat)

    st.write("")
    pres.titre_section("Déroulé du calcul de la VAN")
    _detail_calcul(resultat)

    st.write("")
    pres.titre_section(
        "Sensibilité au taux d'actualisation",
        "la VAN diminue lorsque le taux exigé augmente",
    )
    st.plotly_chart(
        graphiques.graphique_profil(resultat),
        use_container_width=True,
        key="graphique_profil_calculateur",
    )

    st.write("")
    _bloc_enregistrement(projet, resultat)
