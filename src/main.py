from pathlib import Path

import charges
import devis
import predimensionnement
from elements import DonneesInvalides, Projet

RACINE = Path(__file__).resolve().parent.parent
DONNEES = RACINE / "donnees"
SORTIES = RACINE / "sorties"

MENU = """
===== BUREAU D'ÉTUDES =====
1. Saisir ou charger le projet
2. Calculer le métré
3. Descente de charges
4. Prédimensionner poteaux et semelles
5. Générer le devis
6. Exporter un rapport
0. Quitter"""


def demander(message, defaut, convertir=float):
                                                                                  
    while True:
        rep = input(f"{message} [{defaut}] : ").strip()
        if not rep:
            return defaut
        try:
            return convertir(rep.replace(",", "."))
        except ValueError:
            print("  Valeur invalide, recommencez.")


def liste_nombres(texte):
    """Convertit '4; 4; 4' ou '4 4 4' en [4.0, 4.0, 4.0]."""
    return [float(x) for x in texte.replace(";", " ").split()]


def saisir_projet(projet):
    """Modifie les principales données du projet au clavier puis l'enregistre."""
    d = projet.vers_dict_projet()
    d["chantier"]["nom"] = demander("Nom du chantier", d["chantier"]["nom"], str)
    d["grille"]["travees_x_m"] = demander("Travées x (m)", d["grille"]["travees_x_m"], liste_nombres)
    d["grille"]["travees_y_m"] = demander("Travées y (m)", d["grille"]["travees_y_m"], liste_nombres)
    d["niveaux"]["nombre"] = demander("Nombre de niveaux", d["niveaux"]["nombre"], int)
    d["niveaux"]["q_exploitation_kn_m2"] = demander(
        "Q par niveau, du haut vers le bas (kN/m²)", d["niveaux"]["q_exploitation_kn_m2"], liste_nombres
    )
    d["plancher"]["epaisseur_dalle_m"] = demander("Épaisseur dalle (m)", d["plancher"]["epaisseur_dalle_m"])
    d["semelles"]["contrainte_sol_kpa"] = demander("Contrainte du sol (kPa)", d["semelles"]["contrainte_sol_kpa"])
    materiaux = {
        "beton": vars(projet.beton).copy(),
        "ratios_acier_kg_m3": vars(projet.acier).copy(),
    }
    nouveau = Projet.depuis_dicts(d, materiaux)  # valide avant d'écrire
    nouveau.sauvegarder(DONNEES / "projet.json")
    print("Projet enregistré dans donnees/projet.json")
    return nouveau


def afficher_descente(descente):
    for t, d in descente.items():
        print(f"\n{t} ({d['nombre']} poteaux) — surface tributaire {d['surface']:.1f} m²")
        for n in d["detail"]:
            print(f"  après niveau {n['niveau']} : G = {n['G']:7.1f}  Q = {n['Q']:6.1f}  N_ELU = {n['N_ELU']:7.1f} kN")


def afficher_predim(predim):
    print(f"\n{'Poteau':<8}{'N_ELU':>9}{'A_min':>9}  Côté retenu")
    for t, r in predim.items():
        print(f"{t:<8}{r['N_ELU']:>9.1f}{r['A_min']:>9.3f}  {r['cote_calcule'] * 100:.0f} cm → {r['cote_poteau'] * 100:.0f} cm")
    print(f"\n{'Semelle':<8}{'G+Q':>9}  Côté minimal")
    for t, r in predim.items():
        print(f"{t:<8}{r['G_plus_Q']:>9.1f}  {r['B_calcule']:.2f} m → {r['B_semelle']:.2f} m")


def main():
    projet = None
    while True:
        print(MENU)
        choix = input("Votre choix : ").strip()
        if choix == "0":
            print("Au revoir.")
            return
        try:
            if choix == "1":
                projet = Projet.charger(DONNEES / "projet.json", DONNEES / "materiaux.json")
                print(f"Projet chargé : {projet.nom}")
                if input("Modifier les données ? (o/N) : ").strip().lower() == "o":
                    projet = saisir_projet(projet)
                continue
            if choix not in {"2", "3", "4", "5", "6"}:
                print("Choix inconnu.")
                continue
            if projet is None:
                print("Chargez d'abord le projet (option 1).")
                continue

            descente = charges.descente_par_type(projet)
            predim = predimensionnement.predimensionner(projet, descente)
            m = devis.metre(projet, predim)

            if choix == "2":
                for ouvrage, v in m.items():
                    print(f"{ouvrage:<10} béton {v['beton_m3']:7.2f} m³   acier {v['acier_kg']:8.1f} kg")
            elif choix == "3":
                afficher_descente(descente)
            elif choix == "4":
                afficher_predim(predim)
            else:
                lignes, total = devis.generer_devis(m, devis.charger_bordereau(DONNEES / "bordereau.csv"))
                if choix == "5":
                    for l in lignes:
                        print(f"{l['designation']:<28}{l['quantite']:>9.2f} {l['unite']:<3} {l['montant']:>14,.0f} FCFA")
                    print(f"{'TOTAL HT':<42}{total:>14,.0f} FCFA")
                else:
                    texte = devis.texte_rapport(projet, descente, predim, m, lignes, total)
                    chemin = devis.exporter_rapport(texte, SORTIES / "rapport.txt")
                    print(f"Rapport exporté : {chemin}")
        except (DonneesInvalides, ValueError, KeyError, FileNotFoundError) as err:
            print(f"Erreur : {err}")


if __name__ == "__main__":
    main()
