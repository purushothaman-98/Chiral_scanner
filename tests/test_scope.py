from chiral_scanner.scope import has_chiral_phonon_scope


def test_rejects_nonphonon_chiral_quantum_field_paper() -> None:
    assert not has_chiral_phonon_scope(
        "Fermion doubling in chiral discretizations",
        "We study a Dirac quantum cellular automaton and lattice gauge theory.",
    )


def test_rejects_electronic_chiral_edges_without_phonons() -> None:
    assert not has_chiral_phonon_scope(
        "Retarded interaction between opposite chiral edges",
        "We investigate electronic edge states in an anomalous Hall crystal.",
    )


def test_rejects_phonons_mediating_electronic_chiral_edges() -> None:
    assert not has_chiral_phonon_scope(
        "Retarded interaction between opposite chiral edges",
        "Transverse bulk phonons mediate an interaction between electronic chiral edge modes.",
    )


def test_rejects_chiral_phonons_mentioned_only_as_competing_background() -> None:
    assert not has_chiral_phonon_scope(
        "Parity anomaly governs the thermal Hall effect",
        "Competing proposals based on chiral phonons require undetermined constants. We instead derive a fermion determinant.",
    )


def test_accepts_phonon_angular_momentum() -> None:
    assert has_chiral_phonon_scope(
        "Curvature converts phonon Hall viscosity into phonon angular momentum",
        "We calculate angular momentum carried by lattice vibrations.",
    )


def test_accepts_dynamical_multiferroicity() -> None:
    assert has_chiral_phonon_scope(
        "Terahertz-driven dynamical multiferroicity",
        "Circular ionic motion produces transient magnetization.",
    )
