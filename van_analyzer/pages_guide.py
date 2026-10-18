"""Page « Guide pédagogique » : cours complet sur la VAN, avec exemple corrigé."""

from __future__ import annotations

import streamlit as st

from . import donnees, etat, finance, graphiques, presentation as pres


def _definition() -> None:
    pres.titre_section("1 · Qu'est-ce que la valeur actuelle nette ?")

    st.markdown(
        """
La **valeur actuelle nette** (VAN, ou *Net Present Value* en anglais) mesure la
richesse créée par un projet d'investissement, exprimée en monnaie d'aujourd'hui.

Un projet se résume à deux choses : de l'argent que l'on dépense au départ
(l'investissement initial, noté I₀) et de l'argent que l'on encaisse ensuite,
année après année (les flux de trésorerie, notés CFₜ).

Comparer directement ces montants n'aurait aucun sens : **1 000 € encaissés dans
cinq ans valent moins que 1 000 € encaissés aujourd'hui**. La VAN applique donc
l'**actualisation** : chaque flux futur est ramené à sa valeur d'aujourd'hui, en
utilisant le taux de rendement exigé par l'entreprise (noté r).

La VAN répond à une question simple : *une fois le capital remboursé et rémunéré
au taux exigé, reste-t-il de la valeur ?*

- VAN **supérieure à 0** : oui, le projet crée de la valeur → projet acceptable ;
- VAN **égale à 0** : le projet rembourse et rémunère, mais sans surplus → décision indifférente ;
- VAN **inférieure à 0** : non, le projet détruit de la valeur → projet à rejeter.
        """
    )


def _formule() -> None:
    pres.titre_section("2 · La formule mathématique")

    st.latex(
        r"\mathrm{VAN} \;=\; -I_0 \;+\; \sum_{t=1}^{n} "
        r"\frac{CF_t}{(1+r)^{t}}"
    )

    st.markdown(
        """
Le premier terme, −I₀, est le décaissement initial. La somme porte sur les *n*
années du projet : chaque flux CFₜ est divisé par (1 + r)ᵗ, ce qui le « ramène »
à sa valeur d'aujourd'hui. Plus le flux est lointain (t grand) et plus le taux
exigé est élevé (r grand), plus la division réduit sa valeur.
        """
    )

    st.markdown(
        """
<div class="formule">VAN = -I₀ + [ CF₁/(1+r)¹ + CF₂/(1+r)² + … + CFₙ/(1+r)ⁿ ]</div>
        """,
        unsafe_allow_html=True,
    )


def _variables() -> None:
    pres.titre_section("3 · Les variables utilisées")

    entetes = [
        ("Symbole", ""),
        ("Nom", ""),
        ("Unité", ""),
        ("Signification", ""),
    ]
    lignes = [
        (
            ["I₀", "Investissement initial", "Monnaie", "Capital décaissé au démarrage (année 0). Toujours compté en négatif dans la formule."],
            ["", "", "", ""],
            "",
        ),
        (
            ["CFₜ", "Flux de trésorerie de l'année t", "Monnaie", "Encaissements nets de l'année t : recettes moins dépenses. Peut être négatif (année déficitaire)."],
            ["", "", "", ""],
            "",
        ),
        (
            ["r", "Taux d'actualisation", "Décimal", "Rendement minimal exigé par l'entreprise, compte tenu du risque. Saisi en pourcentage, utilisé en décimal (10 % → 0,10)."],
            ["", "", "", ""],
            "",
        ),
        (
            ["t", "Indice d'année", "Année", "De 1 à n. L'année 0 correspond à l'investissement initial."],
            ["", "", "", ""],
            "",
        ),
        (
            ["n", "Durée du projet", "Année", "Nombre d'années pendant lesquelles le projet génère des flux."],
            ["", "", "", ""],
            "",
        ),
    ]
    st.markdown(pres.tableau_html(entetes, lignes), unsafe_allow_html=True)

    pres.encadre(
        "Le piège classique : le taux d'actualisation",
        "Le taux r est le seul terme de la formule qui dépend d'un jugement. Il "
        "représente ce que l'entreprise exige comme rendement pour accepter un "
        "risque comparable. Un taux trop élevé fait mécaniquement chuter la VAN ; "
        "un taux trop faible la gonfle artificiellement. Justifiez toujours le "
        "taux retenu (coût moyen pondéré du capital, taux du secteur, taux d'un "
        "placement sans risque majoré d'une prime de risque).",
        ton="attention",
    )


def _methode() -> None:
    pres.titre_section("4 · Méthode de calcul, étape par étape")

    etapes = [
        ("Recenser l'investissement initial", "Rassembler toutes les dépenses de démarrage : achat du matériel, installation, formation, besoin en fonds de roulement. Soit I₀."),
        ("Estimer les flux de trésorerie annuels", "Pour chaque année, lister les encaissements et les décaissements d'exploitation. Un flux de trésorerie n'est pas un résultat comptable : les amortissements ne sont pas des décaissements et ne figurent donc pas dans les flux."),
        ("Déterminer le taux d'actualisation", "Retenir le taux de rendement exigé pour ce niveau de risque, puis le convertir en décimal : 8 % devient 0,08."),
        ("Calculer le coefficient d'actualisation", "Pour chaque année t, calculer 1 / (1 + r)ᵗ. Ce coefficient est toujours inférieur à 1 et décroît avec le temps."),
        ("Actualiser chaque flux", "Multiplier chaque flux CFₜ par son coefficient pour obtenir sa valeur d'aujourd'hui."),
        ("Sommer et conclure", "Additionner les flux actualisés, puis retrancher I₀ : on obtient la VAN. Conclure selon son signe : accepter si elle est positive."),
    ]

    for numero, (titre, texte) in enumerate(etapes, start=1):
        st.markdown(f"**Étape {numero} — {titre}**")
        st.caption(texte)


def _exemple_corrige() -> None:
    pres.titre_section("5 · Exemple numérique entièrement corrigé")

    projet = donnees.exemple_en_projet(donnees.EXEMPLE_PEDAGOGIQUE, horodatage=False)
    resultat = finance.analyser(projet)
    symbole = pres.devise()

    st.markdown(
        pres.etiquette("Jeu de données de démonstration", "exemple"),
        unsafe_allow_html=True,
    )
    st.write("")

    pres.encadre(
        "Énoncé",
        "Une entreprise étudie l'acquisition d'un équipement. L'investissement "
        "initial s'élève à 1 000 €. L'équipement générerait un flux de trésorerie "
        "net de 500 € par an pendant 3 ans. Le taux de rendement exigé par "
        "l'entreprise est de 10 %. Question : le projet est-il acceptable ? "
        "Toutes les valeurs ci-dessous sont recalculées par le moteur de calcul de "
        "l'application.",
        ton="neutre",
    )
    st.write("")

    st.markdown(
        f"**Étape 1 — Données du problème.** "
        f"I₀ = {pres.formater_montant(projet.investissement_initial, symbole=symbole)} · "
        f"r = {pres.formater_pourcentage(projet.taux_actualisation)} soit "
        f"{pres.formater_nombre(projet.taux_actualisation, 2)} en décimal · "
        f"n = {projet.duree} ans · "
        f"CF₁ = CF₂ = CF₃ = "
        f"{pres.formater_montant(projet.flux[0], symbole=symbole)}."
    )

    st.markdown("**Étape 2 — Coefficients d'actualisation.**")
    coefficients = " · ".join(
        f"1/(1,10)^{ligne.annee} = {pres.formater_facteur(ligne.facteur)}"
        for ligne in resultat.lignes[1:]
    )
    st.markdown(f"<div class='formule'>{coefficients}</div>", unsafe_allow_html=True)

    st.markdown("**Étape 3 — Flux actualisés.**")
    details = " · ".join(
        f"Année {ligne.annee} : "
        f"{pres.formater_nombre(ligne.flux, 2)} × {pres.formater_facteur(ligne.facteur)} = "
        f"{pres.formater_montant(ligne.flux_actualise, symbole=symbole)}"
        for ligne in resultat.lignes[1:]
    )
    st.markdown(f"<div class='formule'>{details}</div>", unsafe_allow_html=True)

    st.markdown("**Étape 4 — Somme des flux actualisés.**")
    somme = " + ".join(
        pres.formater_nombre(ligne.flux_actualise, 2) for ligne in resultat.lignes[1:]
    )
    st.markdown(
        f"<div class='formule'>{somme} = "
        f"<b>{pres.formater_montant(resultat.somme_flux_actualises, symbole=symbole)}</b></div>",
        unsafe_allow_html=True,
    )

    st.markdown("**Étape 5 — Calcul de la VAN.**")
    st.markdown(
        f"<div class='formule'>VAN = "
        f"{pres.formater_montant(resultat.somme_flux_actualises, symbole=symbole)} − "
        f"{pres.formater_montant(projet.investissement_initial, symbole=symbole)} = "
        f"<b>{pres.formater_montant_signe(resultat.van, symbole=symbole)}</b></div>",
        unsafe_allow_html=True,
    )

    st.markdown("**Étape 6 — Conclusion.**")
    pres.encadre(
        "Verdict",
        f"La VAN est positive ({pres.formater_montant_signe(resultat.van, symbole=symbole)}). "
        f"Cela signifie qu'après avoir récupéré les "
        f"{pres.formater_montant(projet.investissement_initial, symbole=symbole)} investis "
        f"et rémunéré ce capital à {pres.formater_pourcentage(projet.taux_actualisation)}, "
        f"le projet laisse un surplus de "
        f"{pres.formater_montant(resultat.van, symbole=symbole)} de valeur d'aujourd'hui. "
        f"Le projet est donc acceptable au regard du critère de la VAN. "
        + (
            f"Vérification : son TRI est de {pres.formater_pourcentage(resultat.tri)}, "
            f"nettement supérieur au taux exigé de "
            f"{pres.formater_pourcentage(projet.taux_actualisation)} : les deux critères "
            f"concordent."
            if resultat.tri is not None
            else ""
        ),
        ton="positif",
    )

    st.write("")
    pres.titre_section("Tableau de calcul complet", "celui présenté par le calculateur")
    entetes = [
        ("Année", ""),
        (f"Flux ({symbole})", "nombre"),
        ("Coefficient d'actualisation", "nombre"),
        (f"Flux actualisé ({symbole})", "nombre"),
        (f"Cumul actualisé ({symbole})", "nombre"),
    ]
    lignes = []
    for ligne in resultat.lignes:
        libelle = "0 (investissement)" if ligne.annee == 0 else str(ligne.annee)
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
    st.markdown(pres.tableau_html(entetes, lignes), unsafe_allow_html=True)

    st.write("")
    st.markdown("**Visualisation de l'effet d'actualisation**")
    st.caption(
        "Chaque année, la barre claire (flux actualisé) est plus courte que la barre "
        "bleue (flux brut) : c'est l'effet de l'actualisation."
    )
    st.plotly_chart(
        graphiques.graphique_actualisation(
            [ligne.flux for ligne in resultat.lignes[1:]],
            [ligne.flux_actualise for ligne in resultat.lignes[1:]],
        ),
        use_container_width=True,
        key="graphique_guide",
    )

    st.write("")
    colonne_bouton, _ = st.columns([1.8, 2.2])
    with colonne_bouton:
        if st.button(
            "Ouvrir cet exemple dans le calculateur",
            icon="🧮",
            type="primary",
            width="stretch",
        ):
            etat.charger_exemple(donnees.EXEMPLE_PEDAGOGIQUE)
            etat.aller_vers("calculateur")


def _erreurs_frequentes() -> None:
    pres.titre_section("6 · Les erreurs les plus fréquentes")

    erreurs = [
        (
            "Oublier de passer le taux en décimal",
            "Un taux de 10 % doit être utilisé comme 0,10 et non comme 10. Diviser "
            "un flux par (1 + 10)⁵ donne un résultat absurde : le coefficient doit "
            "rester proche de 1.",
        ),
        (
            "Confondre flux de trésorerie et résultat comptable",
            "L'amortissement réduit le bénéfice mais ne sort pas de la trésorerie. "
            "Dans un calcul de VAN, on raisonne en encaissements et décaissements "
            "réels, donc hors amortissement (mais après impôt).",
        ),
        (
            "Utiliser des taux différents pour comparer deux projets",
            "Comparer une VAN calculée à 8 % avec une autre calculée à 12 % n'a "
            "aucun sens : le taux doit être identique pour tous les projets d'un "
            "même arbitrage.",
        ),
        (
            "Ignorer le besoin en fonds de roulement",
            "Stocks et créances immobilisent de la trésorerie dès la première "
            "année. Oublier ce décaissement surestime systématiquement la VAN. Il "
            "doit être récupéré en fin de projet.",
        ),
        (
            "Additionner des flux de trésorerie sans les actualiser",
            "Sommer les flux bruts revient à supposer un taux d'actualisation nul. "
            "C'est le piège le plus courant : le total des flux ne doit jamais être "
            "comparé directement à l'investissement.",
        ),
    ]

    for titre, texte in erreurs:
        st.markdown(f"**{titre}**")
        st.caption(texte)


def _van_et_tri() -> None:
    pres.titre_section("7 · VAN, TRI et indice de rentabilité")

    entetes = [("Critère", ""), ("Ce qu'il mesure", ""), ("Règle de décision", ""), ("Limite principale", "")]
    lignes = [
        (
            ["VAN", "La valeur créée, en monnaie d'aujourd'hui", "Accepter si VAN > 0 ; classer par VAN décroissante", "Sensible au taux retenu ; résultat exprimé en valeur absolue"],
            ["", "", "", ""],
            "",
        ),
        (
            ["TRI", "Le taux de rendement propre au projet", "Accepter si TRI > taux exigé", "Peut ne pas exister ou être multiple si les flux changent plusieurs fois de signe"],
            ["", "", "", ""],
            "",
        ),
        (
            ["Indice de rentabilité", "Le rendement par unité investie", "Accepter si IP > 1", "Favorise les petits projets ; ignore la taille du projet"],
            ["", "", "", ""],
            "",
        ),
    ]
    st.markdown(pres.tableau_html(entetes, lignes), unsafe_allow_html=True)

    pres.encadre(
        "En cas de contradiction entre la VAN et le TRI",
        "Privilégiez toujours la VAN : elle mesure la valeur réellement créée pour "
        "l'entreprise. Un petit projet au TRI spectaculaire peut créer moins de "
        "valeur qu'un projet plus modeste en pourcentage mais plus ambitieux en "
        "montant. La page « Comparaison des projets » illustre cette situation et "
        "signale automatiquement les contradictions.",
        ton="neutre",
    )


def rendre() -> None:
    pres.bandeau(
        "Guide pédagogique de la VAN",
        "Définition, formule, variables, méthode pas à pas et exemple numérique "
        "entièrement corrigé.",
        etiquette="VAN Project Analyzer",
    )
    st.write("")

    _definition()
    st.write("")
    _formule()
    st.write("")
    _variables()
    st.write("")
    _methode()
    st.write("")
    _exemple_corrige()
    st.write("")
    _erreurs_frequentes()
    st.write("")
    _van_et_tri()
