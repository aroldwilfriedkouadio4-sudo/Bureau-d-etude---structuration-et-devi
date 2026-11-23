# Bureau d'études — Projet 1 : Immeuble de bureaux R+2 (Abidjan)

Programme console en Python qui réalise, pour un bâtiment en béton armé :
la descente de charges, le prédimensionnement des poteaux et des semelles,
le métré, le devis et un rapport. Il réutilise les séances 1 à 5.

## Lancer le programme

```bash
python src/main.py
```

Aucune bibliothèque externe n'est nécessaire (Python 3.8+).

| # | Fonctionnalité | Module |
|---|----------------|--------|
| 1 | Saisir ou charger le projet (JSON) | `elements.py` |
| 2 | Calculer le métré | `devis.py` |
| 3 | Descente de charges | `charges.py` |
| 4 | Prédimensionner poteaux et semelles | `predimensionnement.py` |
| 5 | Générer le devis | `devis.py` |
| 6 | Exporter un rapport (`sorties/rapport.txt`) | `devis.py` |

## Lancer les tests

```bash
python -m unittest discover -s tests -v    # ou : pytest
```

Les tests vérifient les valeurs de contrôle de la séance 6.

## Données (`donnees/`)

- `projet.json` : chantier, grille (3 × 4 m en x, 2 × 4 m en y), 3 niveaux de 3 m,
  Q = [1.0 ; 2.5 ; 2.5] kN/m² du haut vers le bas, dalle 20 cm, g complémentaire 2 kN/m²,
  poteaux 25 × 25 cm (σ = 10 MPa, côté mini 20 cm, pas 5 cm), semelles h = 0,50 m (σ sol = 200 kPa, pas 5 cm).
- `materiaux.json` : béton C25/30 (E = 30 000 MPa, γ = 25 kN/m³), ratios d'acier
  90 / 120 / 50 kg/m³ (dalles / poteaux / semelles).
- `bordereau.csv` : prix unitaires en FCFA. **Ce sont des prix d'exemple, à remplacer par ceux du cours.**

## Méthode de calcul

- G plancher = e × γ + g complémentaire = 0,20 × 25 + 2 = 7 kN/m²
- Surface tributaire = demi-travées de chaque côté (angle 4 m², rive 8 m², central 16 m²)
- Poids propre poteau par étage = b × h × hauteur × γ (section initiale 25 × 25)
- N_ELU = 1,35 G + 1,5 Q ; A_min = N_ELU / σ ; côté = max(√A_min arrondi au pas, côté mini)
- Semelle : (G + Q + 12,5 B²) / B² ≤ 200, soit B ≥ √((G + Q) / 187,5), arrondi au pas
- Métré : dalles = surface × épaisseur × niveaux ; poteaux = côté² × hauteur d'étage × niveaux ;
  semelles = B² × h. Acier = volume × ratio.

## Résultats

| Poteau | N_ELU | A_min | Côté retenu | G + Q en pied | Semelle |
|--------|------:|------:|------------:|--------------:|--------:|
| Angle (×4) | 168,4 kN | 0,017 m² | 13 → 20 cm | 122,1 kN | 0,81 → 0,85 m |
| Rive (×6) | 317,8 kN | 0,032 m² | 18 → 20 cm | 230,1 kN | 1,11 → 1,15 m |
| Central (×2) | 616,6 kN | 0,062 m² | 25 cm | 446,1 kN | 1,54 → 1,55 m |

## Organisation de l'équipe (un module par membre)

| Membre | Module | Exemples de commits |
|--------|--------|---------------------|
| Membre 1 | `elements.py` + `donnees/` | classes, lecture JSON, validation |
| Membre 2 | `charges.py` | G plancher, surfaces tributaires, descente par niveau |
| Membre 3 | `predimensionnement.py` | arrondi au pas, poteaux, semelles |
| Membre 4 | `devis.py` | métré, bordereau CSV, devis, rapport |
| Membre 5 | `main.py` + `tests/` + README | menu, gestion des erreurs, tests |

Chaque membre travaille sur sa branche (`git checkout -b feature/charges`), fait au moins
5 commits, puis ouvre une pull request vers `main`.
