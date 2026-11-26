"""Métré (volumes de béton, masses d'acier, surfaces second œuvre), devis et rapport."""

import csv
from pathlib import Path

import openpyxl
from charges import g_plancher


def metre(projet, predim):
    """Calcule les volumes de béton (m³), masses d'acier (kg) et surfaces de second œuvre (m²)."""
    n = projet.niveaux
    g = projet.grille

    # 1. Gros œuvre (Béton et Acier)
    v_dalles = g.surface * projet.plancher.epaisseur_dalle_m * n.nombre
    v_poteaux = sum(
        r["nombre"] * r["cote_poteau"] ** 2 * n.hauteur_etage_m * n.nombre
        for r in predim.values()
    )
    v_semelles = sum(
        r["nombre"] * r["B_semelle"] ** 2 * projet.semelles.hauteur_m
        for r in predim.values()
    )
    a = projet.acier

    # 2. Second œuvre (Surfaces en m²)
    perimetre = 2 * (g.longueur_x + g.longueur_y)
    # Murs extérieurs (périmètre x hauteur totale, moins 15% pour les ouvertures)
    s_maconnerie = (perimetre * n.hauteur_etage_m * n.nombre) * 0.85
    # Enduit et peinture sur les 2 faces (intérieure + extérieure)
    s_enduit = s_maconnerie * 2.0
    s_peinture = s_maconnerie * 2.0
    # Carrelage sur tous les niveaux et étanchéité sur la toiture-terrasse
    s_carrelage = g.surface * n.nombre
    s_etancheite = g.surface

    return {
        "dalles": {"beton_m3": v_dalles, "acier_kg": v_dalles * a.dalles},
        "poteaux": {"beton_m3": v_poteaux, "acier_kg": v_poteaux * a.poteaux},
        "semelles": {
            "beton_m3": v_semelles,
            "acier_kg": v_semelles * a.semelles,
        },
        "second_oeuvre": {
            "SO-MACONNERIE": s_maconnerie,
            "SO-ENDUIT": s_enduit,
            "SO-PEINTURE": s_peinture,
            "SO-CARRELAGE": s_carrelage,
            "SO-ETANCHEITE": s_etancheite,
        },
    }


def charger_bordereau(chemin):
    """Lit le bordereau des prix (CSV) et renvoie {code: {designation, unite, prix}}."""
    chemin = Path(chemin)
    if not chemin.exists():
        raise FileNotFoundError(f"bordereau introuvable : {chemin}")
    prix = {}
    with chemin.open(encoding="utf-8", newline="") as f:
        for numero, ligne in enumerate(csv.DictReader(f), start=2):
            try:
                prix[ligne["code"]] = {
                    "designation": ligne["designation"],
                    "unite": ligne["unite"],
                    "prix": float(ligne["prix_unitaire_fcfa"]),
                }
            except (KeyError, ValueError) as err:
                raise ValueError(
                    f"ligne {numero} du bordereau invalide : {err}"
                ) from err
    return prix


def generer_devis(m, bordereau):
    """Construit les lignes du devis et le total (FCFA)."""
    total_acier = sum(
        v["acier_kg"] for v in m.values() if isinstance(v, dict) and "acier_kg" in v
    )

    quantites = {
        "BET_DAL": m["dalles"]["beton_m3"],
        "BET_POT": m["poteaux"]["beton_m3"],
        "BET_SEM": m["semelles"]["beton_m3"],
        "ACIER": total_acier,
        "SO-MACONNERIE": m["second_oeuvre"]["SO-MACONNERIE"],
        "SO-ENDUIT": m["second_oeuvre"]["SO-ENDUIT"],
        "SO-PEINTURE": m["second_oeuvre"]["SO-PEINTURE"],
        "SO-CARRELAGE": m["second_oeuvre"]["SO-CARRELAGE"],
        "SO-ETANCHEITE": m["second_oeuvre"]["SO-ETANCHEITE"],
    }
    lignes = []
    for code, qte in quantites.items():
        if code not in bordereau:
            raise KeyError(f"prix manquant dans le bordereau pour {code}")
        p = bordereau[code]
        lignes.append(
            {
                "code": code,
                "designation": p["designation"],
                "unite": p["unite"],
                "quantite": qte,
                "prix": p["prix"],
                "montant": qte * p["prix"],
            }
        )
    return lignes, sum(l["montant"] for l in lignes)


def _fcfa(montant):
    """Formate un montant avec des espaces : 13212075 → '13 212 075'."""
    return f"{montant:,.0f}".replace(",", " ")


def texte_rapport(projet, descente, predim, m, lignes, total):
    """Assemble le rapport complet sous forme de texte."""
    out = [
        f"RAPPORT — {projet.nom} ({projet.ville})",
        f"Dossier : {projet.dossier}",
        "=" * 60,
        f"Grille : {projet.grille.longueur_x} × {projet.grille.longueur_y} m, "
        f"{projet.grille.nb_poteaux} poteaux, {projet.niveaux.nombre} niveaux",
        f"G plancher : {g_plancher(projet):.2f} kN/m²   "
        f"Q (haut → bas) : {projet.niveaux.q_exploitation_kn_m2} kN/m²",
        "",
        "DESCENTE DE CHARGES ET PRÉDIMENSIONNEMENT",
        f"{'Type':<8}{'Nb':>4}{'S (m²)':>8}{'N_ELU':>10}{'A_min':>9}{'Poteau':>9}{'G+Q':>9}{'Semelle':>9}",
    ]
    for t, r in predim.items():
        out.append(
            f"{t:<8}{r['nombre']:>4}{descente[t]['surface']:>8.1f}{r['N_ELU']:>10.1f}"
            f"{r['A_min']:>9.3f}{r['cote_poteau'] * 100:>7.0f}cm{r['G_plus_Q']:>9.1f}"
            f"{r['B_semelle']:>8.2f}m"
        )
    out += ["", "MÉTRÉ"]
    for ouvrage, v in m.items():
        if "beton_m3" in v:
            out.append(
                f"  {ouvrage:<10} béton {v['beton_m3']:8.2f} m³   acier {v['acier_kg']:9.1f} kg"
            )
        else:
            for code_so, surf in v.items():
                out.append(f"  {code_so:<15} surface {surf:8.2f} m²")

    out += ["", "DEVIS (FCFA)"]
    for l in lignes:
        out.append(
            f"  {l['designation']:<32}{l['quantite']:>10.2f} {l['unite']:<3}"
            f" × {_fcfa(l['prix']):>8} = {_fcfa(l['montant']):>14}"
        )
    out.append(f"  {'TOTAL HT':<59}{_fcfa(total):>14}")
    return "\n".join(out)


def exporter_rapport(texte, chemin):
    """Écrit le rapport dans un fichier texte et renvoie son chemin."""
    chemin = Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(texte, encoding="utf-8")
    return chemin


def exporter_excel(projet, descente, predim, lignes, total, chemin="sorties/dossier_genie_civil.xlsx"):
    """Génère un classeur Excel structuré (Descente de charges + Devis en FCFA)."""
    chemin = Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)

    wb = openpyxl.Workbook()

    # Onglet 1 : Descente de charges & Prédimensionnement
    ws1 = wb.active
    ws1.title = "Structure"
    ws1.append(["PROJET :", projet.nom, "VILLE :", projet.ville])
    ws1.append([])
    ws1.append(["Type Poteau", "Nombre", "Surface (m²)", "N_ELU (kN)", "Poteau retenu (cm)", "G+Q (kN)", "Semelle retenue (m)"])
    for t, r in predim.items():
        ws1.append([
            t.capitalize(),
            r["nombre"],
            descente[t]["surface"],
            round(r["N_ELU"], 1),
            round(r["cote_poteau"] * 100, 0),
            round(r["G_plus_Q"], 1),
            round(r["B_semelle"], 2),
        ])

    # Onglet 2 : Devis Estimatif (DQE)
    ws2 = wb.create_sheet(title="Devis_FCFA")
    ws2.append(["Code", "Désignation", "Unité", "Quantité", "Prix Unitaire (FCFA)", "Montant Total (FCFA)"])
    for l in lignes:
        ws2.append([
            l["code"],
            l["designation"],
            l["unite"],
            round(l["quantite"], 2),
            l["prix"],
            round(l["montant"], 0),
        ])
    ws2.append(["", "", "", "", "TOTAL GÉNÉRAL HT", round(total, 0)])

    wb.save(chemin)
    return chemin
