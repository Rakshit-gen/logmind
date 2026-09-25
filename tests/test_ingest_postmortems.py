def test_ingest_postmortems_chunks_and_stores(tmp_path, monkeypatch):
    monkeypatch.setattr("logmind.store.CHROMA_DIR", str(tmp_path / "chroma"))
    (tmp_path / "incident-one.md").write_text("# Incident\n\n" + ("details " * 300))

    from logmind.ingest_postmortems import ingest_postmortems
    from logmind.store import get_vectorstore

    count = ingest_postmortems(str(tmp_path))
    assert count > 1

    store = get_vectorstore()
    results = store.similarity_search("incident details", k=1)
    assert results[0].metadata["source"] == "incident-one.md"
