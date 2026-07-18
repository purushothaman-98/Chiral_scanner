from __future__ import annotations

TOPIC_NAME = "Chiral phonons"
TOPIC_DESCRIPTION = (
    "Chiral phonons, phonon angular momentum, dynamical multiferroicity, "
    "phonomagnetism, nonlinear phononics, and related angular-momentum phononics."
)
PROMPT_VERSION = "chiral-phonons-v3.0"
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
    "Transition-metal dichalcogenides",
    "Other two-dimensional materials",
    "Van der Waals magnets",
    "Chiral/enantiomorphic crystals",
    "Ferroelectrics and polar crystals",
    "Magnetic insulators",
    "Topological materials",
    "Elemental chalcogens",
    "Semiconductors",
    "Molecular crystals",
    "Other / unspecified",
]

# Scientific axes are deliberately orthogonal.  A paper can concern phonon angular
# momentum without establishing true eigenmode chirality, and a driven circular
# lattice trajectory is not automatically a chiral normal mode.
RESEARCH_FOCUS_AREAS = [
    "Intrinsic/symmetry-defined chiral phonons",
    "Coherently driven circular phonons",
    "Dynamical multiferroicity / phonomagnetism",
    "Nonlinear / helical phononics",
    "Magnon-phonon or spin-phonon angular-momentum transfer",
    "Phonon magnetic moment / Zeeman physics",
    "Topological / valley phonons",
    "Thermal or mechanical angular-momentum transport",
    "Chiral phonon-electron / exciton coupling",
    "Cavity / polariton / photon-phonon coupling",
    "Methods or materials discovery",
]

CHIRALITY_CLASSES = [
    "True structural/eigenmode chirality",
    "Circular/elliptical phonon polarization",
    "Phonon angular momentum",
    "Pseudo-angular momentum / valley chirality",
    "Dynamically induced chirality",
    "Chirality transferred by magnon/spin coupling",
    "Claimed or ambiguous chirality",
    "Not established",
]

PHONON_CHARACTERISTICS = [
    "Zone-centre (Gamma)",
    "Finite-momentum / valley",
    "Optical",
    "Acoustic",
    "Infrared-active",
    "Raman-active",
    "Polar / ferroelectric soft mode",
    "Degenerate E mode",
    "Nondegenerate circular mode",
    "Surface / interface / polariton mode",
    "Not specified",
]

GENERATION_MECHANISMS = [
    "Intrinsic crystal symmetry",
    "Circular/elliptical THz resonant drive",
    "Mid-infrared resonant drive",
    "Raman / impulsive coherent excitation",
    "Valley-selective optical excitation or scattering",
    "Magnetic-order / magnon hybridization",
    "Nonlinear phonon-phonon coupling",
    "Thermal gradient / population imbalance",
    "Static magnetic field / Zeeman selection",
    "Cavity / phonon-polariton coupling",
    "Theoretical eigenmode construction",
    "Direct observation without generation",
]

EXPERIMENTAL_METHOD_GROUPS = [
    "Ultrafast THz pump-probe",
    "THz time- or frequency-domain spectroscopy",
    "Transient optical spectroscopy",
    "Time-resolved Kerr/Faraday polarimetry",
    "Circular/polarization-resolved Raman spectroscopy",
    "Raman optical activity / vibrational circular dichroism",
    "RIXS / inelastic X-ray spectroscopy",
    "X-ray diffraction/scattering",
    "Electron diffraction",
    "Neutron scattering",
    "Kerr/Faraday polarimetry",
    "Thermal transport",
    "Torque / cantilever / mechanical detection",
    "Magnetometry",
    "Photoemission / electron spectroscopy",
    "Other experimental method",
]

EXCITATION_METHOD_GROUPS = [
    "Circular/elliptical THz excitation",
    "Linear THz excitation",
    "Mid-infrared phonon excitation",
    "Impulsive/coherent Raman excitation",
    "Optical pump excitation",
    "Raman/infrared optical excitation",
    "Thermal excitation",
    "Other / unspecified excitation",
]

DETECTION_METHOD_GROUPS = [
    "Kerr/Faraday polarimetry",
    "Transient optical spectroscopy",
    "THz time-domain spectroscopy",
    "Raman spectroscopy",
    "RIXS / inelastic X-ray scattering",
    "X-ray diffraction/scattering",
    "Electron diffraction",
    "Neutron scattering",
    "Thermal transport",
    "Magnetometry",
    "Other / unspecified detection",
]

COMPUTATIONAL_METHOD_GROUPS = [
    "DFT / DFPT phonons",
    "Frozen phonon / finite displacement",
    "First-principles electron-phonon coupling",
    "Anharmonic / self-consistent phonons",
    "Many-body perturbation theory / BSE",
    "Real-time TDDFT / electron-ion dynamics",
    "Molecular or spin-lattice dynamics",
    "Model Hamiltonian / tight binding",
    "Magnon-phonon / spin-wave theory",
    "Boltzmann transport",
    "Group theory / symmetry analysis",
    "Berry-phase / topological phonon analysis",
    "Electrodynamics / cavity / polariton modelling",
    "Machine learning",
    "Other theory/computation",
]

PHYSICAL_PROPERTIES = [
    "Real-space circular/elliptical ionic motion",
    "Phonon angular momentum",
    "Phonon pseudo-angular momentum",
    "Phonon magnetic moment",
    "Effective / transient magnetic field",
    "Transient magnetization",
    "Phonon Zeeman splitting",
    "Magneto-optical Kerr/Faraday response",
    "Circular dichroism / helicity selection",
    "Angular-momentum transfer",
    "Magnon-phonon hybridization",
    "Spin polarization / spin current / switching",
    "Nonlinear phonon coupling",
    "Berry curvature / Chern topology",
    "Valley polarization / selection rules",
    "Thermal Hall response",
    "Mechanical torque / Einstein-de Haas response",
    "Structural / ferroelectric order control",
    "Nonreciprocity / directional transport",
    "Phonon-electron / exciton coupling",
    "Strong coupling / polariton formation",
]

EVIDENCE_LEVELS = [
    "Direct observation of circular ionic motion / chirality",
    "Direct phonon angular-momentum measurement",
    "Direct magnetic or magneto-optical consequence",
    "Spectroscopic selection-rule evidence",
    "Indirect experimental inference plus modelling",
    "First-principles prediction",
    "Model / theory proposal",
    "Review / perspective synthesis",
    "Insufficient abstract evidence",
]

APPLICATION_DIRECTIONS = [
    "Ultrafast magnetic control",
    "Spintronics / orbitronics",
    "Valleytronics",
    "Thermal management / caloritronics",
    "Topological phononics",
    "Quantum sensing / metrology",
    "Cavity control / hybrid quantum systems",
    "Ferroelectric / structural switching",
    "Nonreciprocal devices",
    "Materials discovery / design",
    "Fundamental symmetry / selection rules",
]

# Split into several manageable broad-recall API queries. The rule/AI layers decide final relevance.
QUERY_EXPRESSIONS = [
    "("
    + " OR ".join(
        [
            'all:"chiral phonon"',
            'all:"phonon chirality"',
            'all:"phonon angular momentum"',
            'all:"phonon pseudoangular momentum"',
            'all:"phonon helicity"',
            'all:"helical phonon"',
            'all:"circularly polarized phonon"',
        ]
    )
    + ")",
    "(all:phonon OR all:lattice) AND "
    '(all:chiral OR all:chirality OR all:helicity OR all:"angular momentum" '
    'OR all:handedness OR all:"circular polarization")',
    "(all:phonon OR all:lattice) AND "
    '(all:terahertz OR all:THz OR all:Raman OR all:RIXS OR all:"pump probe") AND '
    '(all:magnetization OR all:"angular momentum" OR all:circular OR all:helicity)',
    '(all:"spin phonon" OR all:"magnon phonon" OR all:"spin lattice") AND '
    '(all:chirality OR all:"angular momentum" OR all:helicity OR all:circular)',
    '(all:"nonlinear phononics" OR all:"phonon polariton" OR '
    'all:"thermal Hall" OR all:"topological phonon" OR all:phonomagnetism OR '
    'all:"dynamical multiferroicity") AND '
    '(all:chiral OR all:phonon OR all:lattice OR all:"angular momentum")',
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
