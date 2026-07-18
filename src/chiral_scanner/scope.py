import re

STRONG_TOPIC_PHRASES = (
    "chiral phonon",
    "phonon chirality",
    "phononic chirality",
    "phonon angular momentum",
    "phonon pseudoangular momentum",
    "phonon pseudo-angular momentum",
    "phonon helicity",
    "phonon handedness",
    "phonomagnetism",
    "phono-magnetism",
    "dynamical multiferroicity",
    "dynamic multiferroicity",
    "nonlinear phononics",
    "magnetophononics",
    "magno-phononics",
    "phonon magnetic moment",
    "phonon inverse faraday",
    "phonon barnett",
    "phonon einstein-de haas",
    "circularly polarized phonon",
    "circularly polarised phonon",
    "helical phonon",
    "axial phonon",
    "topological phonon",
    "weyl phonon",
    "phonon hall effect",
    "phonon hall viscosity",
    "phonon berry curvature",
)

PHONON_TOKEN = r"(?:phonons?|lattice vibrations?|ionic motions?|vibrational modes?)"
CHIRAL_TOKEN = (
    r"(?:chiral(?:ity)?|helicity|handedness|angular momentum|circular(?:ly)?(?: polarized)?|"
    r"magnetic moment)"
)


def has_chiral_phonon_scope(title: str, abstract: str) -> bool:
    """Conservative guard against electronic, photonic, QFT and acoustic false positives."""
    text = re.sub(r"\s+", " ", f"{title} {abstract}".casefold())
    if "competing proposals based on chiral phonons" in text:
        return False
    if any(phrase in text for phrase in STRONG_TOPIC_PHRASES):
        return True
    text = re.sub(r"chiral (?:edge|fermion|electron|photon|pair)(?:s| states| modes)?", "", text)
    return bool(
        re.search(rf"{PHONON_TOKEN}.{{0,55}}{CHIRAL_TOKEN}", text)
        or re.search(rf"{CHIRAL_TOKEN}.{{0,55}}{PHONON_TOKEN}", text)
    )
