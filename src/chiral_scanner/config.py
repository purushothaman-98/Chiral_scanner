from __future__ import annotations

TOPIC_NAME = "Chiral phonons"
TOPIC_DESCRIPTION = (
    "Chiral phonons, phonon angular momentum, dynamical multiferroicity, "
    "phonomagnetism, nonlinear phononics, and related angular-momentum phononics."
)
PROMPT_VERSION = "chiral-phonons-v1.0"
DEFAULT_INITIAL_DATE = "2017-01-01"
DEFAULT_SCAN_OVERLAP_DAYS = 14
DEFAULT_AI_MODEL = "openai/gpt-4.1-mini"

ARXIV_CATEGORIES = [
    "cond-mat.mtrl-sci",
    "cond-mat.mes-hall",
    "cond-mat.str-el",
    "physics.optics",
    "physics.app-ph",
    "cond-mat.supr-con",
    "cond-mat.stat-mech",
    "physics.comp-ph",
    "physics.atm-clus",
    "physics.chem-ph",
    "cond-mat.soft",
    "quant-ph",
]

PRIMARY_TERMS = [
    "chiral phonon",
    "chiral phonons",
    "phonon chirality",
    "phononic chirality",
    "chiral lattice vibration",
    "circularly polarized phonon",
    "circularly polarised phonon",
    "elliptically polarized phonon",
    "helical phonon",
    "axial phonon",
    "rotational phonon mode",
    "phonon angular momentum",
    "lattice angular momentum",
    "vibrational angular momentum",
    "phonon pseudoangular momentum",
    "phonon pseudo-angular momentum",
    "phonon helicity",
    "phonon handedness",
    "phonon circular polarization",
]

RELATED_PHENOMENA = [
    "dynamical multiferroicity",
    "dynamic multiferroicity",
    "phonomagnetism",
    "phono-magnetism",
    "phonon-induced magnetization",
    "phonon magnetization",
    "phonon magnetic moment",
    "phonon inverse Faraday effect",
    "phonon Barnett effect",
    "phonon Einstein-de Haas effect",
    "phonon Zeeman effect",
    "phonon Faraday effect",
    "magnon-phonon hybridization",
    "spin-phonon angular momentum transfer",
    "spin-lattice angular momentum transfer",
    "magnetophononics",
    "magno-phononics",
    "nonlinear phononics",
    "helical nonlinear phononics",
    "phonon-phonon angular momentum transfer",
    "ionic Raman scattering",
    "topological phonon",
    "Weyl phonon",
    "phonon Berry curvature",
    "phonon Hall effect",
    "phonon thermal Hall effect",
    "chiral phonon polariton",
    "phonon polariton angular momentum",
]

EXPERIMENTAL_TERMS = [
    "terahertz",
    "THz",
    "mid-infrared",
    "pump-probe",
    "time-resolved",
    "Raman spectroscopy",
    "RIXS",
    "resonant inelastic X-ray scattering",
    "X-ray diffraction",
    "electron diffraction",
    "neutron scattering",
    "Kerr rotation",
    "Faraday rotation",
    "electro-optic sampling",
    "transient reflectivity",
    "transient transmission",
    "thermal transport",
    "magnetometry",
]

THEORY_TERMS = [
    "density functional theory",
    "DFT",
    "density functional perturbation theory",
    "DFPT",
    "first-principles",
    "ab initio",
    "molecular dynamics",
    "real-time TDDFT",
    "time-dependent density functional theory",
    "Boltzmann transport",
    "model Hamiltonian",
    "tight-binding",
    "group theory",
    "symmetry analysis",
    "Berry curvature",
    "Bethe-Salpeter equation",
    "many-body perturbation theory",
    "machine learning",
]

MATERIAL_TERMS = [
    "SrTiO3",
    "strontium titanate",
    "KTaO3",
    "potassium tantalate",
    "BaTiO3",
    "barium titanate",
    "LiNbO3",
    "lithium niobate",
    "alpha-quartz",
    "quartz",
    "alpha-HgS",
    "cinnabar",
    "tellurium",
    "selenium",
    "Bi2Se3",
    "MoS2",
    "MoSe2",
    "WS2",
    "WSe2",
    "transition metal dichalcogenide",
    "van der Waals magnet",
    "CrI3",
    "CrBr3",
    "FePS3",
    "NiPS3",
    "alpha-RuCl3",
    "ferroelectric",
    "multiferroic",
    "quantum paraelectric",
    "perovskite oxide",
    "chiral crystal",
    "enantiomorphic crystal",
    "noncentrosymmetric crystal",
    "Weyl semimetal",
    "topological insulator",
]

APPLICATION_TERMS = [
    "ultrafast magnetization",
    "magnetic switching",
    "spintronics",
    "angular momentum transfer",
    "thermal Hall transport",
    "valleytronics",
    "topological control",
    "ferroelectric control",
    "nonreciprocal transport",
    "quantum materials control",
    "cavity control",
]

FALSE_POSITIVE_TERMS = [
    "chiral molecule",
    "chiral fermion",
    "chiral magnon",
    "chiral spin texture",
    "chiral plasmon",
    "chiral photon",
    "chiral metamaterial",
    "acoustic metamaterial",
    "mechanical phononic crystal",
    "phononic waveguide",
    "topological acoustics",
    "chiral chemistry",
    "circularly polarized luminescence",
]

LATTICE_ANCHORS = [
    "phonon",
    "lattice vibration",
    "ionic motion",
    "vibrational mode",
    "Raman mode",
    "infrared-active mode",
    "atomic displacement",
]

MATERIAL_FAMILIES = [
    "Perovskite oxides",
    "Two-dimensional materials",
    "Van der Waals magnets",
    "Chiral/enantiomorphic crystals",
    "Ferroelectrics and polar crystals",
    "Magnetic insulators",
    "Topological materials",
    "Molecular crystals",
    "Other / unspecified",
]

EXPERIMENTAL_METHOD_GROUPS = [
    "THz pump-probe",
    "Optical pump-probe",
    "Raman spectroscopy",
    "RIXS / inelastic X-ray scattering",
    "X-ray diffraction/scattering",
    "Electron diffraction",
    "Neutron scattering",
    "Kerr/Faraday polarimetry",
    "Thermal transport",
    "Magnetometry",
    "Other experimental method",
]

COMPUTATIONAL_METHOD_GROUPS = [
    "DFT / DFPT",
    "Many-body perturbation theory / BSE",
    "Real-time TDDFT",
    "Molecular dynamics",
    "Model Hamiltonian / tight binding",
    "Boltzmann transport",
    "Group theory / symmetry analysis",
    "Machine learning",
    "Other theory/computation",
]

PHYSICAL_PROPERTIES = [
    "Phonon angular momentum",
    "Phonon chirality/helicity",
    "Pseudo-angular momentum",
    "Transient magnetization",
    "Phonon magnetic moment",
    "Spin-lattice angular-momentum transfer",
    "Magnon-phonon hybridization",
    "Nonlinear phonon coupling",
    "Thermal Hall response",
    "Berry curvature/topology",
    "Valley scattering",
    "Magneto-optical response",
    "Coherent lattice dynamics",
    "Polarization/ferroelectric response",
]

# Split into several manageable broad-recall API queries. The rule/AI layers decide final relevance.
QUERY_EXPRESSIONS = [
    "("
    + " OR ".join(
        [
            'all:\"chiral phonon\"',
            'all:\"phonon chirality\"',
            'all:\"phonon angular momentum\"',
            'all:\"phonon pseudoangular momentum\"',
            'all:\"phonon helicity\"',
            'all:\"helical phonon\"',
            'all:\"circularly polarized phonon\"',
        ]
    )
    + ")",
    "(all:phonon OR all:lattice) AND "
    "(all:chiral OR all:chirality OR all:helicity OR all:\"angular momentum\" "
    "OR all:handedness OR all:\"circular polarization\")",
    "(all:phonon OR all:lattice) AND "
    "(all:terahertz OR all:THz OR all:Raman OR all:RIXS OR all:\"pump probe\") AND "
    "(all:magnetization OR all:\"angular momentum\" OR all:circular OR all:helicity)",
    "(all:\"spin phonon\" OR all:\"magnon phonon\" OR all:\"spin lattice\") AND "
    "(all:chirality OR all:\"angular momentum\" OR all:helicity OR all:circular)",
    "(all:\"nonlinear phononics\" OR all:\"phonon polariton\" OR "
    "all:\"thermal Hall\" OR all:\"topological phonon\" OR all:phonomagnetism OR "
    "all:\"dynamical multiferroicity\") AND "
    "(all:chiral OR all:phonon OR all:lattice OR all:\"angular momentum\")",
]

AUTHOR_ACTION_PATTERNS = {
    "experimental": [
        r"\bwe (?:measure|measured|observe|observed|demonstrate experimentally|fabricate|probe|detect|record|perform .*spectroscopy)\b",
        r"\bour (?:measurements|experiment|experiments|spectra|sample|samples)\b",
        r"\bwe report (?:the )?(?:observation|measurement|experimental demonstration)\b",
    ],
    "computational": [
        r"\bwe (?:calculate|computed|compute|simulate|derive|model|predict|solve|evaluate)\b",
        r"\bour (?:calculations|simulations|theory|model|first-principles results)\b",
        r"\bwe perform (?:density functional|first-principles|ab initio|DFT|DFPT|molecular dynamics)\b",
    ],
}
