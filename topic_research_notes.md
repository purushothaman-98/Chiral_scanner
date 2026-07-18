# Chiral Phonon Scanner — Scientific Scope and Taxonomy

This document records the scientific design decisions used by the scanner. The automated literature source in version 1 is the official arXiv API. Final inclusion is based on title-and-complete-abstract analysis rather than a single exact keyword.

## 1. Scope levels

The scanner separates the field into three relevance levels:

1. **Core chiral-phonon research** — chiral phonons, phonon chirality/helicity, circular or elliptical ionic motion, phonon angular momentum and pseudo-angular momentum.
2. **Closely related mechanisms** — dynamical multiferroicity, phonomagnetism, phonon magnetic moments, spin–phonon or magnon–phonon angular-momentum transfer, and nonlinear/helical phononics.
3. **Adjacent frontier research** — topological phonons, phonon Hall effects, cavity or polariton phononics, ultrafast lattice control and exciton/valley coupling where the phonon-angular-momentum connection is scientifically substantive.

A mode is not classified as a core chiral phonon merely because an abstract mentions a degenerate mode, pseudo-angular momentum or helicity. The abstract must support a real connection to handed/circular lattice motion or its angular-momentum consequences.

## 2. Core search language

### Direct terms

- chiral phonon / chiral phonons
- phonon chirality / phononic chirality
- chiral lattice vibration
- circularly or elliptically polarized phonon
- helical or axial phonon
- rotational phonon mode
- angular-momentum-carrying phonon
- phonon, lattice or vibrational angular momentum
- phonon pseudo-angular momentum / PAM
- phonon helicity or handedness
- phonon circular polarization

### Driven phonomagnetism

- dynamical or dynamic multiferroicity
- phonon-induced or lattice-induced magnetization
- phonon magnetization or phonon magnetic moment
- ionic loop current
- phonon inverse Faraday effect
- phonon Barnett or Einstein–de Haas effect
- phonon Zeeman or Faraday effect
- effective magnetic field from chiral phonons

### Spin–lattice coupling

- chiral magnon–phonon coupling
- chirality-selective magnon–phonon hybridization
- spin–phonon or spin–lattice angular-momentum transfer
- magnetophononics / magno-phononics
- phonon-mediated spin switching
- phonon-driven magnetization switching

### Nonlinear phononics

- nonlinear, chiral nonlinear or helical nonlinear phononics
- nonlinear phonon coupling
- phonon–phonon angular-momentum transfer
- rotational phonon–phonon scattering
- sum-frequency or difference-frequency phonon excitation
- anharmonic or three-phonon coupling
- ionic Raman scattering

## 3. Experimental evidence

Experimental classification requires author-action evidence such as “we measure”, “we observe”, “we fabricate”, “we detect” or equivalent language tied to the reported work. A paper is not experimental merely because it compares a prediction with previous measurements.

Canonical experimental method groups are:

- THz pump–probe and THz time-domain spectroscopy
- optical pump–probe and transient reflectivity/transmission
- Raman, helicity-resolved Raman and Raman circular dichroism
- resonant inelastic X-ray scattering (RIXS)
- time-resolved X-ray diffraction or diffuse scattering
- ultrafast electron diffraction
- neutron scattering
- Kerr or Faraday polarimetry
- magnetometry
- thermal and Hall transport

Useful excitation phrases include circular or elliptical THz pulses, polarization-shaped THz fields, resonant infrared-active phonon driving, mid-infrared excitation, impulsive stimulated Raman scattering, coherent phonon excitation and helicity/valley-selective excitation.

## 4. Theory and computation

Computational classification likewise requires author-action evidence such as “we calculate”, “we simulate”, “we derive”, “we model” or equivalent language. Casual mention of DFT in the introduction is not sufficient.

Canonical theory/computation groups are:

- DFT and density-functional perturbation theory
- many-body perturbation theory and Bethe–Salpeter calculations
- real-time TDDFT
- molecular dynamics
- model Hamiltonians and tight binding
- Boltzmann transport
- group theory and symmetry analysis
- machine learning or high-throughput screening

**Theory + Experiment** requires independent evidence that the same paper reports original work of both kinds.

## 5. Materials and systems

Material names improve extraction and filtering but are not mandatory query gates. Important systems include:

- SrTiO3, KTaO3 and BaTiO3
- LiNbO3, quartz and other polar or enantiomorphic crystals
- alpha-HgS, tellurium and selenium
- transition-metal dichalcogenides such as MoS2, MoSe2, WS2 and WSe2
- van der Waals magnets including CrI3, CrBr3, FePS3, NiPS3 and alpha-RuCl3
- ferroelectrics, multiferroics and quantum paraelectrics
- magnetic insulators
- Weyl, Dirac and other topological materials
- molecular crystals where vibrational chirality is central

Canonical families are kept deliberately short: perovskite oxides; two-dimensional materials; van der Waals magnets; chiral/enantiomorphic crystals; ferroelectric and polar crystals; magnetic insulators; topological materials; molecular crystals; other/unspecified.

## 6. Physical properties and applications

The classifier extracts only properties supported by the supplied title and abstract:

- phonon angular momentum
- phonon chirality/helicity
- pseudo-angular momentum
- transient magnetization
- phonon magnetic moment
- spin–lattice angular-momentum transfer
- magnon–phonon hybridization
- nonlinear phonon coupling
- thermal Hall response
- phonon Berry curvature or topology
- valley scattering
- magneto-optical response
- coherent lattice dynamics
- polarization or ferroelectric response

Application areas include ultrafast magnetization control, magnetic switching, spintronics, valleytronics, thermal transport, topological-state control, nonreciprocal transport, ferroelectric control and cavity quantum-material engineering.

## 7. False-positive control

Potential false positives include chiral molecules, fermions, magnons, spin textures, plasmons, photons, metamaterials, acoustic/phononic structures, topological acoustics and circularly polarized luminescence. They enter the feed only when the supplied metadata also establishes a substantive atomic-lattice vibration or phonon-angular-momentum connection.

“Chiral phononic crystal” is treated cautiously because it commonly denotes a patterned acoustic or mechanical structure rather than an atomic-scale chiral phonon.

## 8. arXiv categories

Primary coverage:

- cond-mat.mtrl-sci
- cond-mat.mes-hall
- cond-mat.str-el
- physics.optics
- physics.app-ph

Secondary coverage:

- cond-mat.supr-con
- cond-mat.stat-mech
- physics.comp-ph
- physics.atm-clus
- physics.chem-ph
- cond-mat.soft
- quant-ph

The API uses several broad-recall queries rather than one restrictive conjunction. Transparent rules extract immediate metadata, but borderline records remain available for AI and human review.

## 9. Feed dimensions

Each paper can be filtered by:

- AI relevance
- research type
- paper nature
- material/system and family
- experimental methods
- computational methods
- physical properties

The preferred scientific sections are:

1. Direct experimental chiral phonons
2. Driven phonomagnetism and dynamical multiferroicity
3. Spin–phonon and magnon–phonon coupling
4. Nonlinear, topological and polariton phononics
5. Reviews, theory and candidate materials
6. Events, COST Actions, schools and opportunities

## 10. Opportunities and tools

The initial official-source watchlist prioritizes:

- COST Action CA23136 CHIROMAG, especially spin–lattice chirality and phonomagnetism activities
- CECAM workshops and quantum-materials dynamics programmes
- SPICE workshops and SPIN+X seminars
- APS and MRS programmes
- ultrafast-phenomena, magnetism, THz and nonlinear-phononics meetings

For each future event record, store event type, topic, organiser/network, location and format, event dates, abstract and registration deadlines, early-career eligibility, poster opportunities, travel/COST support, official URL, last-checked date and status.

The tools directory begins with the official arXiv API, Phonopy/Phono3py, Quantum ESPRESSO PHonon, EPW, ABINIT, Yambo and the Bilbao Crystallographic Server.

## 11. Version-1 boundaries

Version 1 deliberately excludes PDF chat, accounts, comments, citation networks, automatic PDF summarization and embeddings. Older papers are never removed during ordinary scans. New arXiv versions update a stable base-ID record while preserving every version identifier seen.
