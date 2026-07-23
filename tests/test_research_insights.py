from datetime import datetime, timezone

from chiral_scanner.research_insights import field_brief, signal_tier


def paper(title: str, abstract: str, **decision):
    return {
        "title": title,
        "abstract": abstract,
        "initial_submission_date": "2026-07-20T00:00:00Z",
        "ai_decision": {
            "include_in_feed": True,
            "relevance": "Core chiral-phonon paper",
            "research_type": "Computational / theoretical",
            "evidence_level": "Model / theory proposal",
            "physical_properties": [],
            "chirality_class": [],
            **decision,
        },
    }


def test_phonon_blockade_false_friend_needs_interpretation():
    item = paper(
        "Nonreciprocal phonon blockade",
        "A spinning optomechanical resonator enables a directional chiral network.",
        physical_properties=["Phonon angular momentum"],
        chirality_class=["Claimed or ambiguous chirality"],
    )
    assert signal_tier(item) == "Needs interpretation"


def test_explicit_phonon_angular_momentum_is_a_strong_signal():
    item = paper(
        "Direct measurement of phonon angular momentum",
        "We resolve circular ionic motion and its handedness.",
        research_type="Experimental",
        evidence_level="Direct mode-resolved measurement",
    )
    assert signal_tier(item) == "Strong field signal"
    brief = field_brief([item], now=datetime(2026, 7, 23, tzinfo=timezone.utc))
    assert brief["strong"] == 1
    assert brief["experimental"] == 1
    assert brief["direct"] == 1
