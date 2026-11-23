"""Éléments du projet : matériaux, grille, niveaux, poteaux, semelles.

Ce module lit et valide les fichiers JSON du dossier ``donnees/`` et
expose une classe :class:`Projet` utilisée par tous les autres modules.
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path


class DonneesInvalides(ValueError):
    """Levée quand une donnée du projet est absente ou incohérente."""


def _positif(valeur, nom):
    """Vérifie qu'une valeur est un nombre strictement positif et la renvoie en float."""
    try:
        valeur = float(valeur)
    except (TypeError, ValueError):
        raise DonneesInvalides(f"{nom} doit être un nombre (reçu : {valeur!r})")
    if valeur <= 0:
        raise DonneesInvalides(f"{nom} doit être strictement positif (reçu : {valeur})")
    return valeur


@dataclass
class Beton:
    """Caractéristiques du béton."""
    nom: str
    module_young_mpa: float
    poids_volumique_kn_m3: float

    def __post_init__(self):
        self.module_young_mpa = _positif(self.module_young_mpa, "module de Young")
        self.poids_volumique_kn_m3 = _positif(self.poids_volumique_kn_m3, "poids volumique")


@dataclass
class RatiosAcier:
    """Ratios d'acier en kg par m³ de béton."""
    dalles: float
    poteaux: float
    semelles: float

    def __post_init__(self):
        for nom in ("dalles", "poteaux", "semelles"):
            setattr(self, nom, _positif(getattr(self, nom), f"ratio acier {nom}"))


@dataclass
class Grille:
    """Grille de poteaux définie par ses travées en x et en y (m)."""
    travees_x_m: list
    travees_y_m: list

    def __post_init__(self):
        if not self.travees_x_m or not self.travees_y_m:
            raise DonneesInvalides("la grille doit avoir au moins une travée en x et en y")
        self.travees_x_m = [_positif(t, "travée x") for t in self.travees_x_m]
        self.travees_y_m = [_positif(t, "travée y") for t in self.travees_y_m]

    @property
    def longueur_x(self):
        """Longueur totale du bâtiment en x (m)."""
        return sum(self.travees_x_m)

    @property
    def longueur_y(self):
        """Longueur totale du bâtiment en y (m)."""
        return sum(self.travees_y_m)

    @property
    def surface(self):
        """Surface d'un plancher (m²)."""
        return self.longueur_x * self.longueur_y

    @property
    def nb_files_x(self):
        """Nombre de files de poteaux le long de x."""
        return len(self.travees_x_m) + 1

    @property
    def nb_files_y(self):
        """Nombre de files de poteaux le long de y."""
        return len(self.travees_y_m) + 1

    @property
    def nb_poteaux(self):
        """Nombre total de poteaux."""
        return self.nb_files_x * self.nb_files_y


@dataclass
class Niveaux:
    """Niveaux du bâtiment. Les charges q sont listées du haut vers le bas."""
    nombre: int
    hauteur_etage_m: float
    q_exploitation_kn_m2: list
    commentaire_q: str = ""

    def __post_init__(self):
        self.nombre = int(_positif(self.nombre, "nombre de niveaux"))
        self.hauteur_etage_m = _positif(self.hauteur_etage_m, "hauteur d'étage")
        if len(self.q_exploitation_kn_m2) != self.nombre:
            raise DonneesInvalides(
                f"{len(self.q_exploitation_kn_m2)} charges q pour {self.nombre} niveaux"
            )
        self.q_exploitation_kn_m2 = [_positif(q, "charge q") for q in self.q_exploitation_kn_m2]


@dataclass
class Plancher:
    """Dalle pleine et charges permanentes complémentaires."""
    epaisseur_dalle_m: float
    g_complementaire_kn_m2: float

    def __post_init__(self):
        self.epaisseur_dalle_m = _positif(self.epaisseur_dalle_m, "épaisseur de dalle")
        self.g_complementaire_kn_m2 = float(self.g_complementaire_kn_m2)
        if self.g_complementaire_kn_m2 < 0:
            raise DonneesInvalides("g complémentaire ne peut pas être négatif")


@dataclass
class ConfigPoteaux:
    """Section initiale et règles de prédimensionnement des poteaux."""
    b_m: float
    h_m: float
    contrainte_limite_mpa: float
    cote_minimal_m: float
    pas_m: float

    def __post_init__(self):
        for nom in ("b_m", "h_m", "contrainte_limite_mpa", "cote_minimal_m", "pas_m"):
            setattr(self, nom, _positif(getattr(self, nom), f"poteaux.{nom}"))


@dataclass
class ConfigSemelles:
    """Règles de prédimensionnement des semelles isolées carrées."""
    hauteur_m: float
    contrainte_sol_kpa: float
    pas_m: float

    def __post_init__(self):
        for nom in ("hauteur_m", "contrainte_sol_kpa", "pas_m"):
            setattr(self, nom, _positif(getattr(self, nom), f"semelles.{nom}"))


@dataclass
class Projet:
    """Toutes les données d'entrée d'un projet."""
    nom: str
    dossier: str
    ville: str
    grille: Grille
    niveaux: Niveaux
    plancher: Plancher
    poteaux: ConfigPoteaux
    semelles: ConfigSemelles
    beton: Beton
    acier: RatiosAcier

    @classmethod
    def depuis_dicts(cls, projet, materiaux):
        """Construit un projet à partir des deux dictionnaires JSON."""
        try:
            chantier = projet["chantier"]
            return cls(
                nom=chantier["nom"],
                dossier=chantier.get("dossier", ""),
                ville=chantier.get("ville", ""),
                grille=Grille(**projet["grille"]),
                niveaux=Niveaux(**projet["niveaux"]),
                plancher=Plancher(**projet["plancher"]),
                poteaux=ConfigPoteaux(**projet["poteaux"]),
                semelles=ConfigSemelles(**projet["semelles"]),
                beton=Beton(**materiaux["beton"]),
                acier=RatiosAcier(**materiaux["ratios_acier_kg_m3"]),
            )
        except KeyError as err:
            raise DonneesInvalides(f"clé manquante dans les données : {err}") from err
        except TypeError as err:
            raise DonneesInvalides(f"champ inattendu ou manquant : {err}") from err

    @classmethod
    def charger(cls, chemin_projet, chemin_materiaux):
        """Charge un projet depuis ``projet.json`` et ``materiaux.json``."""
        return cls.depuis_dicts(_lire_json(chemin_projet), _lire_json(chemin_materiaux))

    def vers_dict_projet(self):
        """Renvoie le contenu de ``projet.json`` (sans les matériaux)."""
        return {
            "chantier": {"nom": self.nom, "dossier": self.dossier, "ville": self.ville},
            "grille": asdict(self.grille),
            "niveaux": asdict(self.niveaux),
            "plancher": asdict(self.plancher),
            "poteaux": asdict(self.poteaux),
            "semelles": asdict(self.semelles),
        }

    def sauvegarder(self, chemin_projet):
        """Écrit ``projet.json``."""
        Path(chemin_projet).write_text(
            json.dumps(self.vers_dict_projet(), indent=2, ensure_ascii=False), encoding="utf-8"
        )


def _lire_json(chemin):
    """Lit un fichier JSON avec des messages d'erreur clairs."""
    chemin = Path(chemin)
    if not chemin.exists():
        raise DonneesInvalides(f"fichier introuvable : {chemin}")
    try:
        return json.loads(chemin.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        raise DonneesInvalides(f"JSON invalide dans {chemin.name} (ligne {err.lineno})") from err
