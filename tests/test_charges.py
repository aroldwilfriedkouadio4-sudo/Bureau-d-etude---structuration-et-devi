

import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))

from charges import descente_par_type, g_plancher, surface_tributaire  
from elements import DonneesInvalides, Projet  
from predimensionnement import arrondi_sup, cote_semelle, predimensionner  


def projet_test():
    return Projet.charger(RACINE / "donnees" / "projet.json", RACINE / "donnees" / "materiaux.json")


class TestDescente(unittest.TestCase):
    def setUp(self):
        self.projet = projet_test()
        self.descente = descente_par_type(self.projet)

    def test_g_plancher(self):
        self.assertAlmostEqual(g_plancher(self.projet), 7.0)

    def test_surfaces_tributaires(self):
        g = self.projet.grille
        self.assertAlmostEqual(surface_tributaire(g, 0, 0), 4.0)    #angle
        self.assertAlmostEqual(surface_tributaire(g, 1, 0), 8.0)    #rive
        self.assertAlmostEqual(surface_tributaire(g, 1, 1), 16.0)  #central

    def test_nombre_poteaux(self):
        nombres = {t: d["nombre"] for t, d in self.descente.items()}
        self.assertEqual(nombres, {"Angle": 4, "Rive": 6, "Central": 2})

    def test_n_elu_valeurs_de_controle(self):
        for t, attendu in {"Angle": 168.4, "Rive": 317.8, "Central": 616.6}.items():
            self.assertAlmostEqual(self.descente[t]["N_ELU"], attendu, places=1)

    def test_g_plus_q_en_pied(self):
        for t, attendu in {"Angle": 122.1, "Rive": 230.1, "Central": 446.1}.items():
            self.assertAlmostEqual(self.descente[t]["N_ELS"], attendu, places=1)


class TestPredimensionnement(unittest.TestCase):
    def setUp(self):
        projet = projet_test()
        self.predim = predimensionner(projet, descente_par_type(projet))

    def test_a_min(self):
        for t, attendu in {"Angle": 0.017, "Rive": 0.032, "Central": 0.062}.items():
            self.assertAlmostEqual(self.predim[t]["A_min"], attendu, places=3)

    def test_cote_poteaux(self):
        for t, attendu in {"Angle": 0.20, "Rive": 0.20, "Central": 0.25}.items():
            self.assertAlmostEqual(self.predim[t]["cote_poteau"], attendu)

    def test_cote_semelles(self):
        for t, attendu in {"Angle": 0.85, "Rive": 1.15, "Central": 1.55}.items():
            self.assertAlmostEqual(self.predim[t]["B_semelle"], attendu)

    def test_arrondi_valeur_deja_ronde(self):
        self.assertAlmostEqual(arrondi_sup(0.85, 0.05), 0.85)


class TestErreurs(unittest.TestCase):
    def test_fichier_absent(self):
        with self.assertRaises(DonneesInvalides):
            Projet.charger("absent.json", "absent.json")

    def test_nombre_q_incoherent(self):
        projet = projet_test().vers_dict_projet()
        projet["niveaux"]["q_exploitation_kn_m2"] = [1.0, 2.5]
        materiaux = {"beton": {"nom": "C25/30", "module_young_mpa": 30000, "poids_volumique_kn_m3": 25},
                     "ratios_acier_kg_m3": {"dalles": 90, "poteaux": 120, "semelles": 50}}
        with self.assertRaises(DonneesInvalides):
            Projet.depuis_dicts(projet, materiaux)

    def test_sol_trop_faible(self):
        with self.assertRaises(ValueError):
            cote_semelle(100, 10, 0.5, 25, 0.05)


if __name__ == "__main__":
    unittest.main()
