from chiral_scanner.storage import merge_papers


def paper(version: int, abstract: str = "A") -> dict:
    return {
        "base_arxiv_id": "2401.00001",
        "current_version": version,
        "versioned_arxiv_id": f"2401.00001v{version}",
        "abstract": abstract,
        "latest_update_date": f"2024-01-0{version}T00:00:00Z",
        "versions_seen": [f"2401.00001v{version}"],
    }


def test_deduplicate_and_track_versions():
    merged, added, updated = merge_papers([], [paper(1)])
    assert added == 1 and updated == 0
    merged[0]["ai_decision"] = {"include_in_feed": True}
    merged[0]["ai_fingerprint"] = "old"
    merged, added, updated = merge_papers(merged, [paper(2, "Changed")])
    assert added == 0 and updated == 1
    assert merged[0]["versions_seen"] == ["2401.00001v1", "2401.00001v2"]
    assert merged[0]["ai_decision"] is None


def test_same_version_does_not_duplicate():
    merged, _, _ = merge_papers([], [paper(1)])
    merged, added, updated = merge_papers(merged, [paper(1)])
    assert len(merged) == 1
    assert added == 0 and updated == 0
