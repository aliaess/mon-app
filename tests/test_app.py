"""Tests d'intégration de l'application Streamlit (parcours utilisateur complets).

Ces tests utilisent ``streamlit.testing.v1.AppTest`` : ils exécutent réellement
l'application, page par page, et vérifient les valeurs produites.

Exécution depuis la racine du projet :

    .venv/bin/python -m unittest tests.test_app -v

Les tests écrivent dans un dossier temporaire : l'historique réel de
l'utilisateur n'est jamais modifié.
"""

import html
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from streamlit.testing.v1 import AppTest  # noqa: E402

from van_analyzer import donnees  # noqa: E402

DELAI = 60.0

#: Amorçage utilisé pour tester une page isolément. ``AppTest`` exécute ce code
#: comme un script : il prépare l'état de session puis rend la page demandée.
AMORCAGE_PAGE = """
import sys
sys.path.insert(0, {racine!r})
from van_analyzer import etat, {module}
etat.initialiser()
{module}.rendre()
"""


def _textes(elements) -> str:
    """Concatène le contenu textuel d'une collection d'éléments."""
    return "\n".join(str(getattr(element, "value", "")) for element in elements)


def _contenu(at: AppTest) -> str:
    """Rassemble tout le texte affiché par une page.

    Les espaces fines insécables utilisées pour séparer les milliers sont
    remplacées par des espaces ordinaires, et les entités HTML sont décodées :
    les assertions restent ainsi lisibles.
    """
    morceaux = []
    for collection in (
        at.markdown,
        at.caption,
        at.warning,
        at.info,
        at.success,
        at.error,
    ):
        morceaux.append(_textes(collection))
    morceaux.append("\n".join(str(getattr(e, "label", "")) for e in at.expander))
    morceaux.append(
        "\n".join(f"{m.label} {m.value}" for m in at.metric)
    )
    brut = "\n".join(morceaux)
    return html.unescape(brut).replace("\u202f", " ")


class BaseApplication(unittest.TestCase):
    """Isole le fichier d'historique avant chaque test."""

    def setUp(self):
        self.dossier = Path(tempfile.mkdtemp(prefix="van-test-"))
        self.fichier_origine = donnees.FICHIER_HISTORIQUE
        self.dossier_origine = donnees.DOSSIER_DONNEES
        donnees.DOSSIER_DONNEES = self.dossier
        donnees.FICHIER_HISTORIQUE = self.dossier / "historique.json"

    def tearDown(self):
        donnees.FICHIER_HISTORIQUE = self.fichier_origine
        donnees.DOSSIER_DONNEES = self.dossier_origine
        shutil.rmtree(self.dossier, ignore_errors=True)

    def application(self) -> AppTest:
        """Lance le véritable point d'entrée de l'application."""
        return AppTest.from_file(str(RACINE / "app.py"), default_timeout=DELAI).run()

    def page(self, module: str) -> AppTest:
        """Lance une page isolément (sans la navigation latérale)."""
        code = AMORCAGE_PAGE.format(racine=str(RACINE), module=module)
        return AppTest.from_string(code, default_timeout=DELAI).run()

    @staticmethod
    def bouton(at: AppTest, libelle: str):
        for bouton in at.button:
            if libelle.lower() in str(bouton.label).lower():
                return bouton
        raise AssertionError(
            f"Bouton « {libelle} » introuvable. Boutons disponibles : "
            f"{[str(b.label) for b in at.button]}"
        )


class TestPointEntree(BaseApplication):
    def test_l_application_demarre_sans_exception(self):
        at = self.application()
        self.assertEqual(list(at.exception), [])
        contenu = _contenu(at)
        self.assertIn("VAN Project Analyzer", contenu)
        self.assertIn("Démarrage rapide", contenu)

    def test_les_cinq_pages_sont_declarees_dans_la_navigation(self):
        at = self.application()
        # Les intitulés du menu latéral proviennent de st.navigation.
        html_sidebar = _textes(at.sidebar.markdown)
        html_sidebar += _textes(at.sidebar.caption)
        self.assertIn("Rappel de la formule", html_sidebar)
        self.assertIn("historique.json", html_sidebar)


class TestParcoursGeneral(BaseApplication):
    def test_toutes_les_pages_se_chargent_sans_exception(self):
        for module in [
            "pages_accueil",
            "pages_calculateur",
            "pages_comparaison",
            "pages_historique",
            "pages_guide",
        ]:
            with self.subTest(page=module):
                at = self.page(module)
                self.assertEqual(
                    list(at.exception), [], f"Exception sur la page {module}"
                )

    def test_accueil_affiche_l_exemple_sans_resultat_invente(self):
        at = self.page("pages_accueil")
        self.assertEqual(list(at.exception), [])
        contenu = _contenu(at)
        self.assertIn("Exemple de démonstration", contenu)
        # Aucun historique : la page doit l'annoncer, pas inventer un chiffre.
        valeurs = [str(m.value) for m in at.metric]
        self.assertIn("0", valeurs)
        self.assertIn("—", valeurs)

    def test_calculateur_refuse_un_nom_vide(self):
        at = self.page("pages_calculateur")
        self.assertEqual(list(at.exception), [])
        contenu = _contenu(at)
        self.assertIn("Le calcul ne peut pas être effectué", contenu)
        self.assertIn("Le nom du projet est obligatoire", contenu)

    def test_chargement_de_l_exemple_puis_calcul_de_la_van(self):
        at = self.page("pages_calculateur")
        self.bouton(at, "Charger l'exemple de démonstration").click().run()
        self.assertEqual(list(at.exception), [])

        # Les hypothèses sont bien préremplies.
        champs = {champ.label: champ.value for champ in at.number_input}
        self.assertAlmostEqual(
            float(champs["Investissement initial I₀ (€)"]), 1000.0, places=6
        )
        self.assertAlmostEqual(
            float(champs["Taux d'actualisation (%)"]), 10.0, places=6
        )

        # La VAN affichée doit être exactement celle de la formule.
        contenu = _contenu(at)
        self.assertIn("+243,43 €", contenu)
        self.assertIn("Valeur actuelle nette", contenu)
        # Les indicateurs complémentaires sont affichés en cartes de résultat.
        self.assertIn("23,38 %", contenu)
        self.assertIn("2,35 ans", contenu)

        self.assertIn("VAN positive", contenu)

    def test_enregistrement_dans_l_historique(self):
        at = self.page("pages_calculateur")
        self.bouton(at, "Charger l'exemple de démonstration").click().run()
        self.bouton(at, "Enregistrer dans l'historique").click().run()
        self.assertEqual(list(at.exception), [])

        entrees = donnees.charger_historique()
        self.assertEqual(len(entrees), 1)
        self.assertAlmostEqual(entrees[0]["van_enregistree"], 243.43, places=2)

    def test_projet_a_van_negative_est_signale(self):
        at = self.page("pages_calculateur")
        # Nom saisi, investissement important, aucun flux positif.
        at.text_input(key="nom_projet").set_value("Projet déficitaire")
        at.number_input(key="investissement_initial").set_value(5000.0)
        at.run()
        self.assertEqual(list(at.exception), [])
        contenu = _contenu(at)
        self.assertIn("Aucun flux de trésorerie positif", contenu)

    def test_montant_uniforme_est_applique_a_toutes_les_annees(self):
        at = self.page("pages_calculateur")
        at.text_input(key="nom_projet").set_value("Projet uniforme")
        at.number_input(key="montant_uniforme").set_value(400.0)
        self.bouton(at, "Appliquer ce montant à toutes les années").click().run()
        self.assertEqual(list(at.exception), [])

        # 400 par an pendant 3 ans à 10 % : 994,74 − 1000 = VAN légèrement négative.
        contenu = _contenu(at)
        self.assertIn("−5,26 €", contenu)


class TestHistoriqueEtPersistance(BaseApplication):
    def _creer_entree(self, nom="Projet test", i0=1000.0, taux=0.10, flux=(500, 500, 500)):
        from van_analyzer import finance

        projet = finance.Projet(nom, i0, taux, list(flux))
        resultat = finance.analyser(projet)
        entrees, succes, message = donnees.ajouter_entree(
            donnees.creer_entree(projet, resultat)
        )
        self.assertTrue(succes, message)
        return entrees

    def test_historique_conserve_les_donnees_apres_relecture(self):
        self._creer_entree(nom="Projet persistant")
        # Relecture depuis le disque, comme après une actualisation de page.
        entrees = donnees.charger_historique()
        self.assertEqual(len(entrees), 1)
        self.assertEqual(entrees[0]["nom"], "Projet persistant")

        at = self.page("pages_historique")
        self.assertEqual(list(at.exception), [])
        contenu = _contenu(at)
        self.assertIn("Projet persistant", contenu)
        self.assertIn("243,43", contenu)

    def test_historique_vide_est_signale(self):
        at = self.page("pages_historique")
        self.assertEqual(list(at.exception), [])
        self.assertIn("Aucun calcul enregistré", _contenu(at))

    def test_chargement_des_exemples_depuis_l_historique(self):
        at = self.page("pages_historique")
        self.bouton(at, "Charger les 3 exemples de démonstration").click().run()
        self.assertEqual(list(at.exception), [])
        self.assertEqual(len(donnees.charger_historique()), 3)

    def test_import_refuse_un_fichier_invalide(self):
        valides, erreurs = donnees.importer_texte("ceci n'est pas du json")
        self.assertEqual(valides, [])
        self.assertTrue(erreurs)

    def test_import_et_export_aller_retour(self):
        self._creer_entree(nom="Projet exporté")
        texte = donnees.exporter_texte(donnees.charger_historique())
        valides, erreurs = donnees.importer_texte(texte)
        self.assertEqual(erreurs, [])
        self.assertEqual(len(valides), 1)
        self.assertEqual(valides[0]["nom"], "Projet exporté")


class TestComparaison(BaseApplication):
    def test_comparaison_necessite_deux_projets(self):
        donnees.charger_exemples_dans_historique()
        at = self.page("pages_comparaison")
        self.assertEqual(list(at.exception), [])
        self.assertIn("Sélectionnez au moins deux projets", _contenu(at))

    def test_comparaison_des_trois_exemples(self):
        donnees.charger_exemples_dans_historique()
        identifiants = [
            e["identifiant"] for e in donnees.charger_historique()
        ]

        at = self.page("pages_comparaison")
        at.multiselect(key="selection_comparaison").set_value(identifiants)
        at.run()
        self.assertEqual(list(at.exception), [])

        contenu = _contenu(at)
        # Les trois VAN attendues.
        self.assertIn("262,96", contenu)
        self.assertIn("243,43", contenu)
        self.assertIn("253,94", contenu)
        self.assertIn("Arbitrage proposé", contenu)
        # Le projet B a la meilleure VAN mais un TRI plus faible que A :
        # l'application doit signaler cette contradiction.
        self.assertIn("contredit le classement", contenu)

    def test_taux_commun_recalcule_toutes_les_van(self):
        donnees.charger_exemples_dans_historique()
        identifiants = [e["identifiant"] for e in donnees.charger_historique()]

        at = self.page("pages_comparaison")
        at.multiselect(key="selection_comparaison").set_value(identifiants)
        at.run()
        # Le champ de taux n'apparaît qu'une fois l'option activée.
        at.toggle(key="taux_commun_actif").set_value(True)
        at.run()
        at.number_input(key="taux_commun_valeur").set_value(0.0)
        at.run()
        self.assertEqual(list(at.exception), [])

        # À 0 %, la VAN de chaque projet vaut simplement −I₀ + somme des flux.
        contenu = _contenu(at)
        self.assertIn("500,00", contenu)   # projet A : 1500 − 1000
        self.assertIn("600,00", contenu)   # projet B : 1600 − 1000
        self.assertIn("100,00", contenu)   # projet C : 1100 − 1000
        # Le message confirme que tous les projets ont été réévalués au taux commun.
        self.assertIn("réévalués au même taux", contenu)
        self.assertIn("seul leur échelonnement de flux", contenu)

    def test_boutons_de_selection_rapide(self):
        """Les trois boutons d'aide à la sélection passent par des callbacks.

        Écrire directement dans ``st.session_state["selection_comparaison"]``
        après la création du multiselect lève une StreamlitAPIException : c'est
        le callback (exécuté avant le script) qui doit faire le travail.
        """
        donnees.charger_exemples_dans_historique()
        at = self.page("pages_comparaison")

        # « Tout sélectionner » : les trois projets et leurs VAN apparaissent.
        self.bouton(at, "Tout sélectionner").click().run()
        self.assertEqual(list(at.exception), [])
        contenu = _contenu(at)
        self.assertIn("Tableau comparatif", contenu)
        self.assertIn("Arbitrage proposé", contenu)

        # « Tout désélectionner » : retour à l'avertissement.
        self.bouton(at, "Tout désélectionner").click().run()
        self.assertEqual(list(at.exception), [])
        self.assertIn("Sélectionnez au moins deux projets", _contenu(at))

    def test_bouton_ajouter_les_exemples_avec_historique_deja_rempli(self):
        """Les exemples restent accessibles même si l'historique n'est pas vide."""
        donnees.charger_exemples_dans_historique()
        at = self.page("pages_comparaison")
        self.assertNotIn(
            "Aucun projet enregistré",
            _contenu(at),
            "L'historique contient déjà les exemples : la page ne doit pas "
            "afficher l'état vide.",
        )

        self.bouton(at, "Ajouter les exemples de démonstration").click().run()
        self.assertEqual(list(at.exception), [])
        contenu = _contenu(at)
        # Les projets sont ajoutés puis sélectionnés : la comparaison s'affiche.
        self.assertIn("Tableau comparatif", contenu)
        self.assertIn("Arbitrage proposé", contenu)

    def test_bouton_ajouter_les_exemples_depuis_etat_vide(self):
        at = self.page("pages_comparaison")
        self.assertIn("Aucun projet enregistré", _contenu(at))

        self.bouton(at, "Charger les 3 exemples de démonstration").click().run()
        self.assertEqual(list(at.exception), [])
        self.assertIn("Tableau comparatif", _contenu(at))


class TestGuidePedagogique(BaseApplication):
    def test_exemple_corrige_est_calcule(self):
        at = self.page("pages_guide")
        self.assertEqual(list(at.exception), [])
        contenu = _contenu(at)
        self.assertIn("454,55", contenu)
        self.assertIn("413,22", contenu)
        self.assertIn("375,66", contenu)
        self.assertIn("1 243,43", contenu)

    def test_guide_contient_toutes_les_sections(self):
        at = self.page("pages_guide")
        contenu = _contenu(at)
        for section in [
            "Qu'est-ce que la valeur actuelle nette",
            "La formule mathématique",
            "Les variables utilisées",
            "Méthode de calcul, étape par étape",
            "Exemple numérique entièrement corrigé",
            "Les erreurs les plus fréquentes",
        ]:
            self.assertIn(section, contenu, f"Section manquante : {section}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
