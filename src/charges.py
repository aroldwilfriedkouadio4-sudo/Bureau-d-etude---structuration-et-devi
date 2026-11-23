"""Descente de charges sur les poteaux (surfaces tributaires, ELU / ELS)."""

GAMMA_G = 1.35  # coefficient ELU sur charges permanentes
GAMMA_Q = 1.5   # coefficient ELU sur charges d'exploitation

TYPES = ("Angle", "Rive", "Central")


def g_plancher(projet):
    """Charge permanente d'un plancher en kN/m² : poids de la dalle + g complémentaire."""
    p = projet.plancher
    return p.epaisseur_dalle_m * projet.beton.poids_volumique_kn_m3 + p.g_complementaire_kn_m2


def poids_poteau_par_niveau(projet):
    """Poids propre d'un poteau sur un étage (kN), avec la section initiale b × h."""
    p = projet.poteaux
    return p.b_m * p.h_m * projet.niveaux.hauteur_etage_m * projet.beton.poids_volumique_kn_m3


def type_poteau(grille, i, j):
    """Renvoie 'Angle', 'Rive' ou 'Central' pour le poteau (i, j) de la grille."""
    bord_x = i in (0, grille.nb_files_x - 1)
    bord_y = j in (0, grille.nb_files_y - 1)
    if bord_x and bord_y:
        return "Angle"
    if bord_x or bord_y:
        return "Rive"
    return "Central"


def _demi_travees(travees, indice):
    """Somme des demi-travées de part et d'autre de la file ``indice``."""
    gauche = travees[indice - 1] / 2 if indice > 0 else 0.0
    droite = travees[indice] / 2 if indice < len(travees) else 0.0
    return gauche + droite


def surface_tributaire(grille, i, j):
    """Surface de plancher reprise par le poteau (i, j), en m²."""
    return _demi_travees(grille.travees_x_m, i) * _demi_travees(grille.travees_y_m, j)


def descente_poteau(projet, surface):
    """Descente de charges d'un poteau de surface tributaire donnée.

    Renvoie un dict avec G, Q, N_ELU, N_ELS en pied (kN) et le détail cumulé
    niveau par niveau, du haut vers le bas.
    """
    g_m2 = g_plancher(projet)
    pp = poids_poteau_par_niveau(projet)
    g_cumul = q_cumul = 0.0
    detail = []
    for numero, q_m2 in enumerate(projet.niveaux.q_exploitation_kn_m2, start=1):
        g_cumul += g_m2 * surface + pp
        q_cumul += q_m2 * surface
        detail.append({
            "niveau": numero,
            "G": g_cumul,
            "Q": q_cumul,
            "N_ELU": GAMMA_G * g_cumul + GAMMA_Q * q_cumul,
        })
    return {
        "surface": surface,
        "G": g_cumul,
        "Q": q_cumul,
        "N_ELU": GAMMA_G * g_cumul + GAMMA_Q * q_cumul,
        "N_ELS": g_cumul + q_cumul,
        "detail": detail,
    }


def descente_par_type(projet):
    """Descente de charges pour chaque type de poteau.

    Pour chaque type, on garde le poteau le plus chargé (utile si les travées
    sont inégales) et on compte le nombre de poteaux de ce type.
    """
    grille = projet.grille
    resultats = {}
    for i in range(grille.nb_files_x):
        for j in range(grille.nb_files_y):
            t = type_poteau(grille, i, j)
            d = descente_poteau(projet, surface_tributaire(grille, i, j))
            if t not in resultats:
                resultats[t] = dict(d, nombre=1)
            else:
                resultats[t]["nombre"] += 1
                if d["N_ELU"] > resultats[t]["N_ELU"]:
                    resultats[t].update(d)
    return {t: resultats[t] for t in TYPES if t in resultats}
