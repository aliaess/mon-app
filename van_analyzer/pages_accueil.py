"""Page « Accueil » : présentation de l'application et démarrage rapide."""

from __future__ import annotations

import streamlit as st

from . import donnees, etat, finance, presentation as pres


def _indicateurs() -> None:
    entrees = etat.historique()
    resultats = [etat.resultat_depuis_entree(e) for e in entrees]
    resultats = [r for r in resultats if r is not None]

    # Conteneur à clé : la feuille de style s'en sert pour autoriser le passage
    # à la ligne des cartes sur un écran étroit (sinon les libellés sont tronqués).
    with st.container(key="cartes_accueil"):
        colonne_projets, colonne_meilleure, colonne_positifs, colonne_panier = st.columns(4)

        colonne_projets.metric(
            "Projets enregistrés",
            len(entrees),
            help="Nombre de calculs conservés dans l'historique.",
        )

        if resultats:
            meilleur = max(resultats, key=lambda r: r.van)
            colonne_meilleure.metric(
                "Meilleure VAN",
                pres.formater_montant_signe(meilleur.van),
                help=f"Projet : {meilleur.projet.nom}",
            )
            positifs = sum(1 for r in resultats if r.est_positive)
            colonne_positifs.metric(
                "Projets à VAN positive",
                f"{positifs} / {len(resultats)}",
                help="Projets qui créent de la valeur au taux qui leur est affecté.",
            )
        else:
            colonne_meilleure.metric(
                "Meilleure VAN", "—", help="Aucun projet enregistré."
            )
            colonne_positifs.metric(
                "Projets à VAN positive", "—", help="Aucun projet enregistré."
            )

        colonne_panier.metric(
            "Projets dans le comparateur",
            len(etat.panier()),
            help="Projets sélectionnés pour la comparaison.",
        )


def _demarrage() -> None:
    pres.titre_section("Démarrage rapide")
    colonne_1, colonne_2, colonne_3 = st.columns(3)
    with colonne_1:
        pres.carte(
            "1️⃣",
            "Saisir le projet",
            "Ouvrez le calculateur et renseignez l'investissement initial, le taux "
            "d'actualisation exigé, la durée puis les flux de trésorerie de chaque année.",
        )
    with colonne_2:
        pres.carte(
            "2️⃣",
            "Lire les résultats",
            "La VAN, le TRI, l'indice de rentabilité et le délai de récupération sont "
            "recalculés à chaque modification, avec le détail année par année.",
        )
    with colonne_3:
        pres.carte(
            "3️⃣",
            "Comparer et conserver",
            "Enregistrez le calcul dans l'historique, puis confrontez plusieurs projets "
            "au même taux pour appuyer votre recommandation.",
        )


def _fonctionnalites() -> None:
    pres.titre_section("Ce que fait l'application")
    colonne_1, colonne_2, colonne_3 = st.columns(3)

    with colonne_1:
        pres.carte(
            "🧮",
            "Calculateur VAN",
            "Saisie guidée, contrôle des données et recalcul automatique selon la "
            "formule VAN = −I₀ + Σ [ CFₜ / (1 + r)ᵗ ].",
        )
    with colonne_2:
        pres.carte(
            "⚖️",
            "Comparaison des projets",
            "Classement par VAN, profils de VAN superposés et détection automatique "
            "des contradictions entre VAN et TRI.",
        )
    with colonne_3:
        pres.carte(
            "🗂️",
            "Historique local",
            "Chaque calcul enregistré est conservé sur votre machine et reste "
            "disponible après actualisation ou redémarrage.",
        )

    st.write("")
    colonne_4, colonne_5, colonne_6 = st.columns(3)

    with colonne_4:
        pres.carte(
            "📘",
            "Guide pédagogique",
            "Définition, formule, variables, méthode en six étapes et exemple "
            "numérique entièrement corrigé.",
        )
    with colonne_5:
        pres.carte(
            "📈",
            "Graphiques détaillés",
            "Flux saisis et actualisés, cumul actualisé, profil de VAN selon le taux "
            "et courbes comparatives.",
        )
    with colonne_6:
        pres.carte(
            "⚠️",
            "Contrôle des saisies",
            "Messages d'erreur explicites, gestion des flux négatifs et des taux "
            "inhabituels, aucune valeur inventée.",
        )


def _avertissement_honnetete() -> None:
    pres.encadre(
        "Sur l'origine des chiffres affichés",
        "Cette application n'invente aucun résultat. Toutes les valeurs présentées "
        "proviennent soit de vos propres saisies, soit de l'exemple de démonstration "
        "intégré, qui est systématiquement signalé par une étiquette « Exemple ». "
        "Les formules utilisées sont la VAN = −I₀ + Σ [ CFₜ / (1 + r)ᵗ ], le TRI "
        "(taux annulant la VAN) et l'indice de rentabilité.",
        ton="neutre",
    )


def _exemple_demonstration() -> None:
    pres.titre_section(
        "Exemple de démonstration",
        "jeu de données fictif, signalé comme tel dans toute l'application",
    )

    colonne_texte, colonne_actions = st.columns([1.9, 1.1])

    lignes = []
    for exemple in donnees.PROJETS_DEMONSTRATION:
        projet = donnees.exemple_en_projet(exemple, horodatage=False)
        resultat = finance.analyser(projet)
        lignes.append(
            (
                [
                    pres.echapper(exemple["nom"]),
                    pres.formater_montant(projet.investissement_initial),
                    pres.formater_pourcentage(projet.taux_actualisation),
                    ", ".join(pres.formater_nombre(f, 0) for f in projet.flux),
                    f'<span style="color:{pres.couleur_van(resultat.van)};font-weight:700">'
                    f"{pres.formater_montant_signe(resultat.van)}</span>",
                ],
                ["", "nombre", "nombre", "nombre", "nombre"],
                "",
            )
        )

    with colonne_texte:
        st.markdown(
            pres.tableau_html(
                [
                    ("Projet", ""),
                    ("Investissement", "nombre"),
                    ("Taux exigé", "nombre"),
                    ("Flux annuels", "nombre"),
                    ("VAN", "nombre"),
                ],
                lignes,
            ),
            unsafe_allow_html=True,
        )
        st.caption(
            "Ces trois projets fictifs illustrent trois situations : un projet "
            "rentable, un projet rentable mais à flux tardifs, et un projet qui ne "
            "récupère pas le capital investi."
        )

    with colonne_actions:
        if st.button(
            "Charger l'exemple dans le calculateur",
            icon="📥",
            type="primary",
            width="stretch",
        ):
            etat.charger_exemple(donnees.EXEMPLE_PEDAGOGIQUE)
            etat.aller_vers("calculateur")

        if st.button(
            "Ajouter les trois exemples à l'historique",
            icon="🗂️",
            width="stretch",
        ):
            ajoutes = donnees.charger_exemples_dans_historique()
            st.success(
                f"{ajoutes} projet(s) ajouté(s) à l'historique."
                if ajoutes
                else "Ces exemples sont déjà enregistrés."
            )

        if st.button(
            "Voir la comparaison des exemples",
            icon="⚖️",
            width="stretch",
        ):
            donnees.charger_exemples_dans_historique()
            entrees = etat.historique()
            identifiants = [
                str(e.get("identifiant", ""))
                for e in entrees
                if str(e.get("nom", "")) in {x["nom"] for x in donnees.PROJETS_DEMONSTRATION}
            ]
            etat.definir_panier(identifiants)
            st.session_state["selection_comparaison"] = identifiants
            etat.aller_vers("comparaison")


def rendre() -> None:
    pres.bandeau(
        "VAN Project Analyzer",
        "Calculez, analysez et comparez la valeur actuelle nette de vos projets "
        "d'investissement — un outil d'apprentissage pour les étudiants en finance "
        "et en gestion.",
        etiquette="Analyse d'investissement",
    )
    st.write("")

    _indicateurs()

    st.write("")
    _demarrage()

    st.write("")
    _fonctionnalites()

    st.write("")
    _exemple_demonstration()

    st.write("")
    _avertissement_honnetete()
