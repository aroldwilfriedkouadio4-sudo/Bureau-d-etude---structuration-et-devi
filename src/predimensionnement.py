

import math


def arrondi_sup(valeur, pas):
    """Arrondit ``valeur`` au multiple de ``pas`` supérieur (ex. 0.807 → 0.85 pour 0.05)."""
    if pas <= 0:
        raise ValueError                                            #le pas doit être strictement positif
    return round(math.ceil(valeur / pas - 1e-9) * pas, 4)


def section_poteau(n_elu_kn, contrainte_mpa, cote_min_m, pas_m):
    """Section minimale d'un poteau carré : A_min = N_ELU / σ.

    Renvoie (A_min en m², côté calculé en m, côté retenu en m).
    """
    if contrainte_mpa <= 0:
        raise ValueError("la contrainte limite doit être positive")
    a_min = (n_elu_kn / 1000) / contrainte_mpa  # kN → MN, MN / MPa = m²
    cote_calc = math.sqrt(a_min)
    cote_retenu = max(arrondi_sup(cote_calc, pas_m), cote_min_m)
    return a_min, cote_calc, cote_retenu


def cote_semelle(n_ser_kn, sigma_sol_kpa, hauteur_m, gamma_beton, pas_m):
    """Côté minimal d'une semelle carrée.

    Condition : (G + Q + γ·h·B²) / B² ≤ σ_sol, soit B ≥ √((G + Q) / (σ_sol − γ·h)).
    Renvoie (B calculé en m, B retenu en m).
    """
    contrainte_utile = sigma_sol_kpa - gamma_beton * hauteur_m
    if contrainte_utile <= 0:
        raise ValueError("le poids propre de la semelle dépasse la capacité du sol")
    b_calc = math.sqrt(n_ser_kn / contrainte_utile)
    return b_calc, arrondi_sup(b_calc, pas_m)


def predimensionner(projet, descente):
    """Prédimensionne poteaux et semelles pour chaque type de poteau."""
    pot, sem = projet.poteaux, projet.semelles
    gamma = projet.beton.poids_volumique_kn_m3
    resultats = {}
    for t, d in descente.items():
        a_min, cote_calc, cote = section_poteau(
            d["N_ELU"], pot.contrainte_limite_mpa, pot.cote_minimal_m, pot.pas_m
        )
        b_calc, b = cote_semelle(d["N_ELS"], sem.contrainte_sol_kpa, sem.hauteur_m, gamma, sem.pas_m)
        resultats[t] = {
            "nombre": d["nombre"],
            "N_ELU": d["N_ELU"],
            "A_min": a_min,
            "cote_calcule": cote_calc,
            "cote_poteau": cote,
            "G_plus_Q": d["N_ELS"],
            "B_calcule": b_calc,
            "B_semelle": b,
        }
    return resultats
