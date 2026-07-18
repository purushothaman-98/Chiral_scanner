from chiral_scanner.arxiv_client import normalize_arxiv_id, parse_atom_feed

ATOM = b"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2401.01234v2</id>
    <updated>2024-01-05T00:00:00Z</updated>
    <published>2024-01-02T00:00:00Z</published>
    <title>  Chiral phonons in a test material </title>
    <summary> We observe a circular lattice mode. </summary>
    <author><name>A. Researcher</name></author>
    <category term="cond-mat.mtrl-sci"/>
    <link href="https://arxiv.org/abs/2401.01234v2" rel="alternate" type="text/html"/>
    <link href="https://arxiv.org/pdf/2401.01234v2" rel="related" type="application/pdf"/>
  </entry>
</feed>"""


def test_normalize_arxiv_id():
    assert normalize_arxiv_id("https://arxiv.org/abs/2401.01234v3") == (
        "2401.01234",
        "2401.01234v3",
        3,
    )


def test_parse_atom_feed():
    papers = parse_atom_feed(ATOM)
    assert len(papers) == 1
    assert papers[0]["base_arxiv_id"] == "2401.01234"
    assert papers[0]["current_version"] == 2
    assert papers[0]["authors"] == ["A. Researcher"]
