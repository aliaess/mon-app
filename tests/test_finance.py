"""Tests unitaires du moteur de calcul (``van_analyzer.finance``).

Exécution depuis la racine du projet :

    .venv/bin/python -m unittest discover -s tests -t . -v
"""

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from van_analyzer import finance  # noqa: E402


class TestUtilitaireNombre(unittest.TestCase):
    def test_conversions_valides(self):
        self.assertEqual(finance.en_nombre(1500), 1500.0)
        self.assertEqual(finance.en_nombre("1500.5"), 1500.5)
        self.assertEqual(finance.en_nombre("1 500,50"), 1500.5)
        self.assertEqual(finance.en_nombre("-2 500"), -2500.0)
        self.assertEqual(finance.en_nombre("0"), 0.0)

    def test_conversions_invalides(self):
        self.assertIsNone(finance.en_nombre(None))
        self.assertIsNone(finance.en_nombre(""))
        self.assertIsNone(finance.en_nombre("abc"))
        self.assertIsNone(finance.en_nombre(float("nan")))
        self.assertIsNone(finance.en_nombre(float("inf")))
        self.assertIsNone(finance.en_nombre(True))


class TestFormuleVAN(unittest.TestCase):
    """VAN = -I0 + somme( CF_t / (1 + r)^t )."""

    def test_valeur_de_reference(self):
        # 500/1,10 + 500/1,21 + 500/1,331 - 1000 = 243,425995...
        van = finance.calculer_van(1000, 0.10, [500, 500, 500])
        attendu = 500 / 1.10 + 500 / 1.21 + 500 / 1.331 - 1000
        self.assertAlmostEqual(van, attendu, places=10)
        self.assertAlmostEqual(van, 243.4259954921113, places=6)

    def test_taux_nul_egale_somme_des_flux(self):
        van = finance.calculer_van(1000, 0.0, [400, 400, 400])
        self.assertAlmostEqual(van, 200.0, places=10)

    def test_van_exactement_nulle(self):
        van = finance.calculer_van(1000, 0.0, [500, 500])
        self.assertAlmostEqual(van, 0.0, places=10)

    def test_van_negative(self):
        van = finance.calculer_van(1000, 0.10, [300, 300, 300])
        self.assertLess(van, 0)
        # 300/1,10 + 300/1,21 + 300/1,331 - 1000 = -253,9444027...
        attendu = 300 / 1.10 + 300 / 1.21 + 300 / 1.331 - 1000
        self.assertAlmostEqual(van, attendu, places=10)
        self.assertAlmostEqual(van, -253.94440270473333, places=6)

    def test_flux_negatifs_acceptes(self):
        # Une année déficitaire doit être traitée correctement (signe conservé).
        van = finance.calculer_van(1000, 0.10, [800, -100, 600])
        attendu = -1000 + 800 / 1.10 - 100 / 1.21 + 600 / 1.331
        self.assertAlmostEqual(van, attendu, places=10)

    def test_taux_negatif(self):
        # Déflation : le taux négatif augmente la valeur actuelle des flux.
        van = finance.calculer_van(1000, -0.10, [500, 500, 500])
        attendu = -1000 + 500 / 0.9 + 500 / 0.81 + 500 / 0.729
        self.assertAlmostEqual(van, attendu, places=10)
        self.assertGreater(van, finance.calculer_van(1000, 0.10, [500, 500, 500]))


class TestTableauDeCalcul(unittest.TestCase):
    def setUp(self):
        self.projet = finance.Projet(
            nom="Test",
            investissement_initial=1000.0,
            taux_actualisation=0.10,
            flux=[500.0, 500.0, 500.0],
        )
        self.lignes = finance.construire_lignes(self.projet)

    def test_nombre_de_lignes(self):
        # Année 0 (investissement) + 3 années de flux.
        self.assertEqual(len(self.lignes), 4)
        self.assertEqual([l.annee for l in self.lignes], [0, 1, 2, 3])

    def test_annee_zero(self):
        annee0 = self.lignes[0]
        self.assertEqual(annee0.flux, -1000.0)
        self.assertEqual(annee0.facteur, 1.0)
        self.assertEqual(annee0.cumul_actualise, -1000.0)

    def test_cumul_actualise_derniere_ligne_egale_van(self):
        van = finance.calculer_van(1000, 0.10, [500, 500, 500])
        self.assertAlmostEqual(self.lignes[-1].cumul_actualise, van, places=10)

    def test_cumul_progresse_correctement(self):
        cumuls = [round(l.cumul_actualise, 6) for l in self.lignes]
        self.assertEqual(
            cumuls,
            [
                -1000.0,
                round(-1000 + 500 / 1.10, 6),
                round(-1000 + 500 / 1.10 + 500 / 1.21, 6),
                round(-1000 + 500 / 1.10 + 500 / 1.21 + 500 / 1.331, 6),
            ],
        )

    def test_facteurs_dactualisation(self):
        self.assertAlmostEqual(self.lignes[1].facteur, 1 / 1.10, places=12)
        self.assertAlmostEqual(self.lignes[2].facteur, 1 / 1.21, places=12)
        self.assertAlmostEqual(self.lignes[3].facteur, 1 / 1.331, places=12)


class TestTRI(unittest.TestCase):
    def test_tri_annule_la_van(self):
        tri = finance.taux_rentabilite_interne(1000, [500, 500, 500])
        self.assertIsNotNone(tri)
        self.assertAlmostEqual(finance.calculer_van(1000, tri, [500, 500, 500]), 0.0, places=6)

    def test_tri_valeur_attendue(self):
        tri = finance.taux_rentabilite_interne(1000, [500, 500, 500])
        self.assertAlmostEqual(tri, 0.23375, places=4)

    def test_tri_absent_si_aucun_flux_positif(self):
        self.assertIsNone(finance.taux_rentabilite_interne(1000, [-100, -100]))

    def test_tri_au_dela_du_plafond_de_recherche(self):
        # TRI ≈ 99 940 %, donc au-delà de la plage [-99,99 % ; +1 000 %] :
        # l'application signale l'absence de solution plutôt qu'un chiffre faux.
        self.assertIsNone(finance.taux_rentabilite_interne(1, [1000, 1000]))

    def test_tri_negatif_sur_un_projet_peu_rentable(self):
        # Un projet à flux positifs possède toujours un TRI, même très négatif.
        tri = finance.taux_rentabilite_interne(10000, [100, 100, 100])
        self.assertIsNotNone(tri)
        self.assertAlmostEqual(tri, -0.76550, places=4)
        self.assertAlmostEqual(
            finance.calculer_van(10000, tri, [100, 100, 100]), 0.0, places=4
        )


class TestIndicateursComplementaires(unittest.TestCase):
    def setUp(self):
        self.projet = finance.Projet(
            nom="Test",
            investissement_initial=1000.0,
            taux_actualisation=0.10,
            flux=[500.0, 500.0, 500.0],
        )
        self.resultat = finance.analyser(self.projet)

    def test_coherence_analyser_et_calculer_van(self):
        self.assertAlmostEqual(
            self.resultat.van,
            finance.calculer_van(1000, 0.10, [500, 500, 500]),
            places=10,
        )

    def test_somme_flux(self):
        self.assertAlmostEqual(self.resultat.somme_flux, 1500.0, places=10)
        self.assertAlmostEqual(self.resultat.van_taux_nul, 500.0, places=10)

    def test_indice_de_rentabilite(self):
        self.assertIsNotNone(self.resultat.indice_rentabilite)
        self.assertAlmostEqual(
            self.resultat.indice_rentabilite,
            self.resultat.somme_flux_actualises / 1000.0,
            places=12,
        )
        self.assertGreater(self.resultat.indice_rentabilite, 1.0)

    def test_indice_de_rentabilite_indefini_sans_investissement(self):
        self.assertIsNone(finance.indice_rentabilite(0.0, 500.0))

    def test_delai_de_recuperation_actualise(self):
        # Cumul ramené à zéro pendant l'année 3 : 2 + 132,231 / 375,657 = 2,352
        self.assertIsNotNone(self.resultat.delai_recuperation)
        self.assertAlmostEqual(self.resultat.delai_recuperation, 2.3520, places=3)

    def test_delai_de_recuperation_absent_si_jamais_recupere(self):
        projet = finance.Projet("Test", 10000.0, 0.10, [100.0, 100.0])
        self.assertIsNone(finance.analyser(projet).delai_recuperation)

    def test_statut_du_resultat(self):
        self.assertTrue(self.resultat.est_positive)
        self.assertFalse(self.resultat.est_nulle)
        negatif = finance.analyser(
            finance.Projet("Test", 1000.0, 0.10, [100.0, 100.0, 100.0])
        )
        self.assertTrue(negatif.est_negative)
        nulle = finance.analyser(
            finance.Projet("Test", 1000.0, 0.0, [500.0, 500.0])
        )
        self.assertTrue(nulle.est_nulle)


class TestInterpretation(unittest.TestCase):
    def test_positive(self):
        texte = finance.interpreter(150.0)
        self.assertEqual(texte["statut"], "positive")
        self.assertIn("valeur", texte["message"].lower())

    def test_negative(self):
        self.assertEqual(finance.interpreter(-150.0)["statut"], "negative")

    def test_nulle(self):
        self.assertEqual(finance.interpreter(0.0)["statut"], "nulle")
        self.assertEqual(finance.interpreter(0.001)["statut"], "nulle")


class TestValidation(unittest.TestCase):
    def test_saisie_valide(self):
        erreurs, avertissements = finance.valider_saisie("Projet", 1000, 10, [500, 500])
        self.assertEqual(erreurs, [])
        self.assertEqual(avertissements, [])

    def test_nom_obligatoire(self):
        erreurs, _ = finance.valider_saisie("   ", 1000, 10, [500])
        self.assertTrue(any("nom" in e.lower() for e in erreurs))

    def test_flux_non_numerique(self):
        erreurs, _ = finance.valider_saisie("Projet", 1000, 10, [500, "abc"])
        self.assertTrue(any("Année 2" in e for e in erreurs))

    def test_taux_inferieur_a_moins_100(self):
        erreurs, _ = finance.valider_saisie("Projet", 1000, -150, [500])
        self.assertTrue(any("supérieur à -100" in e for e in erreurs))

    def test_flux_negatifs_sans_erreur(self):
        erreurs, avertissements = finance.valider_saisie(
            "Projet", 1000, 10, [500, -200, 800]
        )
        self.assertEqual(erreurs, [])
        self.assertEqual(avertissements, [])

    def test_avertissement_si_aucun_flux_positif(self):
        erreurs, avertissements = finance.valider_saisie("Projet", 1000, 10, [-5, -5])
        self.assertEqual(erreurs, [])
        self.assertTrue(any("positif" in a for a in avertissements))

    def test_avertissement_investissement_initial_negatif(self):
        erreurs, avertissements = finance.valider_saisie("Projet", -1000, 10, [500])
        self.assertEqual(erreurs, [])
        self.assertTrue(any("négatif" in a for a in avertissements))

    def test_duree_maximale(self):
        erreurs, _ = finance.valider_saisie("Projet", 1000, 10, [1] * 51)
        self.assertTrue(any("50" in e for e in erreurs))

    def test_taux_trop_eleve_produit_un_avertissement(self):
        erreurs, avertissements = finance.valider_saisie("Projet", 1000, 150, [500])
        self.assertEqual(erreurs, [])
        self.assertTrue(avertissements)


class TestProfilVAN(unittest.TestCase):
    def test_profil_decroissant_avec_le_taux(self):
        taux, valeurs = finance.profil_van(1000, [500, 500, 500], taux_max=0.5, nb_points=20)
        self.assertEqual(len(taux), len(valeurs))
        self.assertEqual(len(taux), 20)
        self.assertGreater(valeurs[0], valeurs[-1])
        self.assertAlmostEqual(valeurs[0], finance.calculer_van(1000, 0.0, [500, 500, 500]))

    def test_profil_contient_le_point_du_taux_choisi(self):
        taux, valeurs = finance.profil_van(1000, [500, 500, 500], taux_max=0.2, nb_points=21)
        self.assertAlmostEqual(taux[10], 0.10, places=10)
        self.assertAlmostEqual(valeurs[10], finance.calculer_van(1000, 0.10, [500, 500, 500]))


class TestSerialisation(unittest.TestCase):
    def test_aller_retour(self):
        projet = finance.Projet("Test", 1234.5, 0.0875, [100.0, -50.0, 900.0], "abc", "2026-01-01")
        reconstruit = finance.projet_depuis_dict(finance.projet_vers_dict(projet))
        self.assertIsNotNone(reconstruit)
        self.assertEqual(reconstruit.nom, projet.nom)
        self.assertEqual(reconstruit.flux, projet.flux)
        self.assertAlmostEqual(reconstruit.taux_actualisation, 0.0875, places=12)
        self.assertEqual(reconstruit.identifiant, "abc")
        self.assertEqual(reconstruit.date_creation, "2026-01-01")

    def test_donnees_invalides(self):
        self.assertIsNone(finance.projet_depuis_dict({"nom": "x"}))
        self.assertIsNone(finance.projet_depuis_dict({"investissement_initial": "a", "taux_actualisation": 0.1, "flux": [1]}))
        self.assertIsNone(finance.projet_depuis_dict("pas un dictionnaire"))
        self.assertIsNone(finance.projet_depuis_dict({"investissement_initial": 1, "taux_actualisation": -1.0, "flux": [1]}))


if __name__ == "__main__":
    unittest.main(verbosity=2)
